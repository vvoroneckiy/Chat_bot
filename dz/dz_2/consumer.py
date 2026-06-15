import asyncio
import logging
import time

import aio_pika
import redis.asyncio as redis

from config import (
    RABBITMQ_URL, RABBITMQ_QUEUE,
    REDIS_URL, REDIS_STREAM, REDIS_GROUP,
)
from protocol import parse_message
from metrics import TestResults

logger = logging.getLogger(__name__)


async def run_rabbitmq_consumer(
    cfg,
    results: TestResults,
    stop_event: asyncio.Event,
    ready_event: asyncio.Event,
):
    connection = await aio_pika.connect(RABBITMQ_URL)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=100)
    queue = await channel.declare_queue(RABBITMQ_QUEUE, durable=False)

    async def on_message(msg: aio_pika.IncomingMessage):
        async with msg.process():
            try:
                seq, ts, ps, actual = parse_message(msg.body)
                latency = time.time() - ts
                results.latencies.append(latency)
                results.received += 1
            except Exception as e:
                results.errors += 1
                logger.error("RabbitMQ consumer parse error: %s", e)

    consumer_tag = await queue.consume(on_message)
    ready_event.set()

    try:
        await stop_event.wait()
    except asyncio.CancelledError:
        pass
    finally:
        try:
            await queue.cancel(consumer_tag)
        except Exception:
            pass
        try:
            await channel.close()
        except Exception:
            pass
        try:
            await connection.close()
        except Exception:
            pass


async def run_redis_consumer(
    cfg,
    results: TestResults,
    stop_event: asyncio.Event,
    ready_event: asyncio.Event,
    consumer_idx: int = 0,
):
    client = redis.from_url(REDIS_URL)
    try:
        try:
            await client.xgroup_create(REDIS_STREAM, REDIS_GROUP, id="0", mkstream=True)
        except redis.ResponseError:
            pass

        consumer_name = f"c{consumer_idx}"
        ready_event.set()

        while not stop_event.is_set():
            try:
                raw = await client.xreadgroup(
                    REDIS_GROUP, consumer_name,
                    {REDIS_STREAM: ">"},
                    count=100,
                    block=1000,
                )
                if raw:
                    for stream_name, messages in raw:
                        if not messages:
                            continue
                        for msg_id, msg_data in messages:
                            try:
                                data = msg_data[b"d"]
                                seq, ts, ps, actual = parse_message(data)
                                latency = time.time() - ts
                                results.latencies.append(latency)
                                results.received += 1
                                await client.xack(REDIS_STREAM, REDIS_GROUP, msg_id)
                            except Exception as e:
                                results.errors += 1
                                logger.error("Redis consumer parse error: %s", e)
            except asyncio.CancelledError:
                break
            except Exception as e:
                results.errors += 1
                logger.error("Redis consumer error: %s", e)
    finally:
        await client.aclose()
