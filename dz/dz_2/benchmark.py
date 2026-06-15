import asyncio
import logging
import time

from config import TestConfig, RABBITMQ_QUEUE, REDIS_STREAM, REDIS_GROUP
from metrics import TestResults, MetricsCollector
from producer import run_rabbitmq_producer, run_redis_producer
from consumer import run_rabbitmq_consumer, run_redis_consumer

logger = logging.getLogger(__name__)


async def cleanup_broker(cfg: TestConfig):
    if cfg.broker == "rabbitmq":
        import aio_pika
        from config import RABBITMQ_URL
        try:
            conn = await aio_pika.connect(RABBITMQ_URL)
            ch = await conn.channel()
            try:
                await ch.queue_delete(RABBITMQ_QUEUE)
            except Exception:
                pass
            try:
                await ch.exchange_delete("bench_exchange")
            except Exception:
                pass
            await ch.close()
            await conn.close()
        except Exception as e:
            logger.warning("RabbitMQ cleanup warning: %s", e)
    else:
        import redis.asyncio as redis
        from config import REDIS_URL
        try:
            cl = redis.from_url(REDIS_URL)
            try:
                await cl.delete(REDIS_STREAM)
            except Exception:
                pass
            try:
                await cl.xgroup_destroy(REDIS_STREAM, REDIS_GROUP)
            except Exception:
                pass
            await cl.aclose()
        except Exception as e:
            logger.warning("Redis cleanup warning: %s", e)


async def run_single_test(cfg: TestConfig) -> TestResults:
    logger.info("=== RUNNING: %s ===", cfg.tag)

    await cleanup_broker(cfg)
    await asyncio.sleep(0.5)

    results = TestResults(
        broker=cfg.broker,
        message_size=cfg.message_size,
        target_rate=cfg.target_rate,
        duration=cfg.duration,
    )

    stop_event = asyncio.Event()
    start_event = asyncio.Event()
    consumer_ready = asyncio.Event()

    if cfg.broker == "rabbitmq":
        producer_fns = [
            run_rabbitmq_producer(cfg, results, stop_event, start_event)
            for _ in range(cfg.num_producers)
        ]
        consumer_fns = [
            run_rabbitmq_consumer(cfg, results, stop_event, consumer_ready)
            for _ in range(cfg.num_consumers)
        ]
    else:
        producer_fns = [
            run_redis_producer(cfg, results, stop_event, start_event)
            for _ in range(cfg.num_producers)
        ]
        consumer_fns = [
            run_redis_consumer(cfg, results, stop_event, consumer_ready, idx)
            for idx in range(cfg.num_consumers)
        ]

    consumer_tasks = [
        asyncio.create_task(fn) for fn in consumer_fns
    ]

    try:
        await asyncio.wait_for(consumer_ready.wait(), timeout=15)
    except asyncio.TimeoutError:
        logger.warning("Consumers not ready within timeout, proceeding anyway")

    await asyncio.sleep(0.5)

    producer_tasks = [
        asyncio.create_task(fn) for fn in producer_fns
    ]

    start_event.set()

    await asyncio.sleep(cfg.duration)

    stop_event.set()

    await asyncio.gather(*producer_tasks, return_exceptions=True)

    await asyncio.sleep(2)

    for t in consumer_tasks:
        t.cancel()

    await asyncio.gather(*consumer_tasks, return_exceptions=True)

    logger.info(
        "  sent=%d  received=%d  errors=%d  lost=%d  avg_lat=%.3fms  p95=%.3fms  p99=%.3fms",
        results.sent, results.received, results.errors,
        results.lost,
        results.avg_latency * 1000,
        results.p95 * 1000,
        results.p99 * 1000,
    )

    return results


async def run_all_tests(tests, collector: MetricsCollector):
    for cfg in tests:
        result = await run_single_test(cfg)
        collector.add(result)
    return collector
