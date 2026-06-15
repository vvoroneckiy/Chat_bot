import asyncio
import logging
import time

import aio_pika
import redis.asyncio as redis

from config import (
    RABBITMQ_URL, RABBITMQ_EXCHANGE, RABBITMQ_QUEUE,
    REDIS_URL, REDIS_STREAM,
)
from protocol import create_message
from metrics import TestResults

logger = logging.getLogger(__name__)


async def _pace(start: float, sent_count: int, target_rate: int):
    if target_rate <= 0:
        return
    expected_time = start + sent_count / target_rate
    now = time.time()
    sleep = expected_time - now
    if sleep > 0.001:
        await asyncio.sleep(sleep)


async def run_rabbitmq_producer(
    cfg,
    results: TestResults,
    stop_event: asyncio.Event,
    start_event: asyncio.Event,
):
    connection = await aio_pika.connect(RABBITMQ_URL)
    channel = await connection.channel()

    exchange = await channel.declare_exchange(
        RABBITMQ_EXCHANGE, aio_pika.ExchangeType.DIRECT, durable=False,
    )
    queue = await channel.declare_queue(RABBITMQ_QUEUE, durable=False)
    await queue.bind(exchange, RABBITMQ_QUEUE)

    await start_event.wait()

    seq = 0
    start = time.time()
    try:
        while not stop_event.is_set():
            if time.time() - start > cfg.duration * 2:
                break
            try:
                body = create_message(seq, cfg.message_size)
                msg = aio_pika.Message(
                    body=body,
                    delivery_mode=aio_pika.DeliveryMode.NOT_PERSISTENT,
                )
                await exchange.publish(
                    msg, routing_key=RABBITMQ_QUEUE,
                )
                results.sent += 1
                await _pace(start, results.sent, cfg.target_rate)
                seq += 1
            except asyncio.CancelledError:
                break
            except Exception as e:
                results.errors += 1
                logger.error("RabbitMQ producer error: %s", e)
    finally:
        await channel.close()
        await connection.close()


async def run_redis_producer(
    cfg,
    results: TestResults,
    stop_event: asyncio.Event,
    start_event: asyncio.Event,
):
    client = redis.from_url(REDIS_URL)
    try:
        await start_event.wait()

        seq = 0
        start = time.time()
        while not stop_event.is_set():
            if time.time() - start > cfg.duration * 2:
                break
            try:
                body = create_message(seq, cfg.message_size)
                await client.xadd(REDIS_STREAM, {b"d": body}, maxlen=2000000)
                results.sent += 1
                await _pace(start, results.sent, cfg.target_rate)
                seq += 1
            except asyncio.CancelledError:
                break
            except Exception as e:
                results.errors += 1
                logger.error("Redis producer error: %s", e)
    finally:
        await client.aclose()
