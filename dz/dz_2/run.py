#!/usr/bin/env python3
"""
Message Broker Benchmark Runner

Usage:
    python run.py [--broker rabbitmq|redis|all] [--mode baseline|size|intensity|all]
                  [--quick]  # shorter duration for smoke-testing
"""

import argparse
import asyncio
import logging
import sys

import os
from config import BASE_TESTS, SIZE_TESTS, INTENSITY_TESTS
from benchmark import run_all_tests
from metrics import MetricsCollector
from report import generate_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def _filter_tests(tests, broker, mode):
    filtered = []
    for t in tests:
        if broker != "all" and t.broker != broker:
            continue
        filtered.append(t)
    return filtered


async def main():
    parser = argparse.ArgumentParser(description="Message Broker Benchmark")
    parser.add_argument(
        "--broker", choices=["rabbitmq", "redis", "all"], default="all",
    )
    parser.add_argument(
        "--mode", choices=["baseline", "size", "intensity", "all"], default="all",
    )
    parser.add_argument("--quick", action="store_true", help="Run short tests (5s)")
    args = parser.parse_args()

    if args.mode == "baseline":
        tests = _filter_tests(BASE_TESTS, args.broker, args.mode)
    elif args.mode == "size":
        tests = _filter_tests(SIZE_TESTS, args.broker, args.mode)
    elif args.mode == "intensity":
        tests = _filter_tests(INTENSITY_TESTS, args.broker, args.mode)
    elif args.mode == "all":
        tests = (
            _filter_tests(BASE_TESTS, args.broker, args.mode)
            + _filter_tests(SIZE_TESTS, args.broker, args.mode)
            + _filter_tests(INTENSITY_TESTS, args.broker, args.mode)
        )
    else:
        tests = _filter_tests(BASE_TESTS, args.broker, args.mode)

    if args.quick:
        for t in tests:
            t.duration = 5
            t.tag = ""  # regenerate tag
            t.__post_init__()

    if not tests:
        logger.warning("No tests matched the filters. Exiting.")
        return

    logger.info("=== Starting %d tests ===", len(tests))
    for t in tests:
        logger.info("  %s", t.tag)

    collector = MetricsCollector()

    try:
        await run_all_tests(tests, collector)
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")

    os.makedirs("results", exist_ok=True)
    collector.save("results/metrics.json")

    report_path = generate_report(collector)
    logger.info("=== All done ===")
    logger.info("Report: %s", report_path)


if __name__ == "__main__":
    asyncio.run(main())
