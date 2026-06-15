from dataclasses import dataclass
from typing import List
import os

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

RABBITMQ_EXCHANGE = "bench_exchange"
RABBITMQ_QUEUE = "bench_queue"
REDIS_STREAM = "bench_stream"
REDIS_GROUP = "bench_group"


@dataclass
class TestConfig:
    broker: str
    message_size: int
    target_rate: int
    duration: int
    num_producers: int = 1
    num_consumers: int = 1
    tag: str = ""

    def __post_init__(self):
        if not self.tag:
            self.tag = (
                f"{self.broker}"
                f"_s{self.message_size}"
                f"_r{self.target_rate}"
                f"_d{self.duration}"
                f"_p{self.num_producers}"
                f"_c{self.num_consumers}"
            )


BASE_TESTS = [
    TestConfig("rabbitmq", 1024, 1000, 30),
    TestConfig("redis", 1024, 1000, 30),
]

SIZE_TESTS = [
    TestConfig(b, s, 1000, 30)
    for b in ("rabbitmq", "redis")
    for s in (128, 10240, 102400)
]

INTENSITY_TESTS = [
    TestConfig(b, 1024, r, 30)
    for b in ("rabbitmq", "redis")
    for r in (5000, 10000, 20000, 50000, 100000)
]
