import json
import math
from dataclasses import dataclass, asdict
from typing import List


@dataclass
class TestResults:
    broker: str
    message_size: int
    target_rate: int
    duration: int
    sent: int = 0
    received: int = 0
    errors: int = 0
    latencies: List[float] = None

    def __post_init__(self):
        if self.latencies is None:
            self.latencies = []

    @property
    def lost(self) -> int:
        return max(0, self.sent - self.received - self.errors)

    @property
    def avg_latency(self) -> float:
        if self.latencies:
            return sum(self.latencies) / len(self.latencies)
        ls = getattr(self, "_lat_stats", {})
        return ls.get("avg_latency_ms", 0) / 1000 if ls else 0.0

    @property
    def max_latency(self) -> float:
        if self.latencies:
            return max(self.latencies)
        ls = getattr(self, "_lat_stats", {})
        return ls.get("max_latency_ms", 0) / 1000 if ls else 0.0

    @property
    def min_latency(self) -> float:
        if self.latencies:
            return min(self.latencies)
        ls = getattr(self, "_lat_stats", {})
        return ls.get("min_latency_ms", 0) / 1000 if ls else 0.0

    def percentile(self, p: float) -> float:
        if self.latencies:
            sorted_lats = sorted(self.latencies)
            idx = int(len(sorted_lats) * p / 100)
            return sorted_lats[min(idx, len(sorted_lats) - 1)]
        ls = getattr(self, "_lat_stats", {})
        key = f"p{p}_latency_ms"
        if ls and key in ls:
            return ls[key] / 1000
        return 0.0

    @property
    def p95(self) -> float:
        return self.percentile(95)

    @property
    def p99(self) -> float:
        return self.percentile(99)

    @property
    def actual_throughput(self) -> float:
        return self.received / self.duration if self.duration else 0

    @property
    def loss_pct(self) -> float:
        if self.sent == 0:
            return 0.0
        return 100.0 * self.lost / self.sent

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("latencies", None)
        d["lost"] = self.lost
        d["loss_pct"] = round(self.loss_pct, 2)
        d["actual_throughput"] = round(self.actual_throughput, 1)
        d["avg_latency_ms"] = round(self.avg_latency * 1000, 3)
        d["min_latency_ms"] = round(self.min_latency * 1000, 3)
        d["max_latency_ms"] = round(self.max_latency * 1000, 3)
        d["p95_latency_ms"] = round(self.p95 * 1000, 3)
        d["p99_latency_ms"] = round(self.p99 * 1000, 3)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "TestResults":
        lat_stats = {
            "avg_latency_ms": d.pop("avg_latency_ms", 0),
            "min_latency_ms": d.pop("min_latency_ms", 0),
            "max_latency_ms": d.pop("max_latency_ms", 0),
            "p95_latency_ms": d.pop("p95_latency_ms", 0),
            "p99_latency_ms": d.pop("p99_latency_ms", 0),
            "loss_pct": d.pop("loss_pct", 0),
            "actual_throughput": d.pop("actual_throughput", 0),
            "lost": d.pop("lost", 0),
        }
        valid_keys = {k for k in d if k in TestResults.__dataclass_fields__}
        filtered = {k: d[k] for k in valid_keys}
        obj = cls(**filtered)
        # Store latency stats for report generation
        obj._lat_stats = lat_stats
        return obj

    @property
    def _lat_stats(self) -> dict:
        if not hasattr(self, "_lat_stats_saved"):
            self._lat_stats_saved = {}
        return self._lat_stats_saved

    @_lat_stats.setter
    def _lat_stats(self, val: dict):
        self._lat_stats_saved = val


class MetricsCollector:
    def __init__(self):
        self.results: List[TestResults] = []

    def add(self, result: TestResults):
        self.results.append(result)

    def save(self, path: str):
        data = [r.to_dict() for r in self.results]
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def load(self, path: str):
        with open(path) as f:
            data = json.load(f)
        for d in data:
            self.results.append(TestResults.from_dict(d))
