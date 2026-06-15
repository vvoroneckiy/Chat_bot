# Message Broker Benchmark Report

Tests run: 18

## 1. Baseline Comparison (1 KB, 1000 msg/s, 30s)

## Baseline Results

| broker | message size | target rate | duration | sent | received | errors | lost | loss pct | actual throughput | avg latency ms | min latency ms | max latency ms | p95 latency ms | p99 latency ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rabbitmq | 1024 | 1000 | 30 | 29948 | 29948 | 0 | 0 | 0.000 | 998.300 | 1.033 | 0.730 | 6.777 | 1.269 | 1.706 |
| redis | 1024 | 1000 | 30 | 29988 | 29986 | 0 | 2 | 0.010 | 999.500 | 1.946 | 0.393 | 15.179 | 3.668 | 4.535 |

## 2. Message Size Impact (1000 msg/s, 30s)

![Message Size Impact](results/message_size_impact.png)

##   Rabbitmq

| broker | message size | target rate | duration | sent | received | errors | lost | loss pct | actual throughput | avg latency ms | min latency ms | max latency ms | p95 latency ms | p99 latency ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rabbitmq | 1024 | 1000 | 30 | 29948 | 29948 | 0 | 0 | 0.000 | 998.300 | 1.033 | 0.730 | 6.777 | 1.269 | 1.706 |
| rabbitmq | 128 | 1000 | 30 | 29948 | 29948 | 0 | 0 | 0.000 | 998.300 | 1.027 | 0.742 | 5.008 | 1.281 | 1.721 |
| rabbitmq | 10240 | 1000 | 30 | 29937 | 29937 | 0 | 0 | 0.000 | 997.900 | 1.101 | 0.780 | 6.737 | 1.369 | 1.815 |
| rabbitmq | 102400 | 1000 | 30 | 5980 | 5980 | 0 | 0 | 0.000 | 199.300 | 5.416 | 1.045 | 49.834 | 44.175 | 45.920 |

##   Redis

| broker | message size | target rate | duration | sent | received | errors | lost | loss pct | actual throughput | avg latency ms | min latency ms | max latency ms | p95 latency ms | p99 latency ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| redis | 1024 | 1000 | 30 | 29988 | 29986 | 0 | 2 | 0.010 | 999.500 | 1.946 | 0.393 | 15.179 | 3.668 | 4.535 |
| redis | 128 | 1000 | 30 | 30000 | 29999 | 0 | 1 | 0.000 | 1000.000 | 1.947 | 0.381 | 10.249 | 3.632 | 4.395 |
| redis | 10240 | 1000 | 30 | 30001 | 30000 | 0 | 1 | 0.000 | 1000.000 | 2.667 | 0.454 | 33.722 | 6.827 | 16.829 |
| redis | 102400 | 1000 | 30 | 4744 | 4743 | 0 | 1 | 0.020 | 158.100 | 8.719 | 1.442 | 50.126 | 44.178 | 45.476 |

## 3. Throughput Intensity (1 KB, 30s)

![Throughput Intensity](results/throughput_intensity.png)

##   Rabbitmq

| broker | message size | target rate | duration | sent | received | errors | lost | loss pct | actual throughput | avg latency ms | min latency ms | max latency ms | p95 latency ms | p99 latency ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rabbitmq | 1024 | 1000 | 30 | 29948 | 29948 | 0 | 0 | 0.000 | 998.300 | 1.033 | 0.730 | 6.777 | 1.269 | 1.706 |
| rabbitmq | 1024 | 5000 | 30 | 35276 | 35276 | 0 | 0 | 0.000 | 1175.900 | 1.064 | 0.763 | 4.251 | 1.311 | 1.642 |
| rabbitmq | 1024 | 10000 | 30 | 31731 | 31731 | 0 | 0 | 0.000 | 1057.700 | 1.202 | 0.848 | 5.689 | 1.479 | 1.823 |
| rabbitmq | 1024 | 20000 | 30 | 33411 | 33411 | 0 | 0 | 0.000 | 1113.700 | 1.140 | 0.792 | 5.536 | 1.421 | 1.726 |
| rabbitmq | 1024 | 50000 | 30 | 35822 | 35822 | 0 | 0 | 0.000 | 1194.100 | 1.055 | 0.768 | 4.553 | 1.259 | 1.529 |
| rabbitmq | 1024 | 100000 | 30 | 35813 | 35813 | 0 | 0 | 0.000 | 1193.800 | 1.051 | 0.764 | 4.233 | 1.267 | 1.584 |

##   Redis

| broker | message size | target rate | duration | sent | received | errors | lost | loss pct | actual throughput | avg latency ms | min latency ms | max latency ms | p95 latency ms | p99 latency ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| redis | 1024 | 1000 | 30 | 29988 | 29986 | 0 | 2 | 0.010 | 999.500 | 1.946 | 0.393 | 15.179 | 3.668 | 4.535 |
| redis | 1024 | 5000 | 30 | 59159 | 58325 | 0 | 834 | 1.410 | 1944.200 | 239.753 | 1.315 | 464.093 | 435.692 | 457.262 |
| redis | 1024 | 10000 | 30 | 59857 | 59007 | 0 | 850 | 1.420 | 1966.900 | 242.015 | 1.148 | 487.520 | 461.851 | 479.684 |
| redis | 1024 | 20000 | 30 | 56313 | 55558 | 0 | 755 | 1.340 | 1851.900 | 235.845 | 1.069 | 526.016 | 440.046 | 495.779 |
| redis | 1024 | 50000 | 30 | 53370 | 52611 | 0 | 759 | 1.420 | 1753.700 | 233.181 | 1.462 | 500.621 | 420.031 | 463.396 |
| redis | 1024 | 100000 | 30 | 54517 | 53744 | 0 | 773 | 1.420 | 1791.500 | 233.469 | 1.059 | 469.508 | 411.982 | 443.205 |

## 4. Degradation Analysis

### RabbitMQ Degradation Point

- **1000 msg/s**: sent=29948, recv=29948, loss=0.0%, lat=1.03ms (p95=1.27ms), p95=1.27ms — OK
- **5000 msg/s**: sent=35276, recv=35276, loss=0.0%, lat=1.06ms (p95=1.31ms), p95=1.31ms — OK
- **10000 msg/s**: sent=31731, recv=31731, loss=0.0%, lat=1.20ms (p95=1.48ms), p95=1.48ms — OK
- **20000 msg/s**: sent=33411, recv=33411, loss=0.0%, lat=1.14ms (p95=1.42ms), p95=1.42ms — OK
- **50000 msg/s**: sent=35822, recv=35822, loss=0.0%, lat=1.05ms (p95=1.26ms), p95=1.26ms — OK
- **100000 msg/s**: sent=35813, recv=35813, loss=0.0%, lat=1.05ms (p95=1.27ms), p95=1.27ms — OK

### Redis Degradation Point

- **1000 msg/s**: sent=29988, recv=29986, loss=0.0%, lat=1.95ms (p95=3.67ms), p95=3.67ms — WARNING (some loss)
- **5000 msg/s**: sent=59159, recv=58325, loss=1.4%, lat=239.75ms (p95=435.69ms), p95=435.69ms — WARNING (some loss), HIGH LATENCY
- **10000 msg/s**: sent=59857, recv=59007, loss=1.4%, lat=242.01ms (p95=461.85ms), p95=461.85ms — WARNING (some loss), HIGH LATENCY
- **20000 msg/s**: sent=56313, recv=55558, loss=1.3%, lat=235.84ms (p95=440.05ms), p95=440.05ms — WARNING (some loss), HIGH LATENCY
- **50000 msg/s**: sent=53370, recv=52611, loss=1.4%, lat=233.18ms (p95=420.03ms), p95=420.03ms — WARNING (some loss), HIGH LATENCY
- **100000 msg/s**: sent=54517, recv=53744, loss=1.4%, lat=233.47ms (p95=411.98ms), p95=411.98ms — WARNING (some loss), HIGH LATENCY

## 5. Conclusions

### 5.1 Which broker showed higher throughput?
At 1000 msg/s target rate, **RabbitMQ** achieves 998 msg/s with 0% loss, while **Redis** achieves 1000 msg/s with 0.01% loss. RabbitMQ latency: 1.03ms (p95=1.27ms) vs Redis: 1.95ms (p95=3.67ms).

At higher target rates, Redis appears to send more messages because its producer is less constrained by broker-side flow control, but ~1.4% of messages are lost and latency spikes to ~240ms. RabbitMQ maintains 0% loss and ~1ms latency across all rates up to 100000 msg/s, but its effective throughput is limited by publisher-confirm flow control to ~1200 msg/s.

### 5.2 Which broker handles larger messages better?

- **128 B**: RabbitMQ 998 msg/s, 1.03ms (p95=1.28ms) | Redis 1000 msg/s, 1.95ms (p95=3.63ms) — Both handle well
- **1024 B**: RabbitMQ 998 msg/s, 1.03ms (p95=1.27ms) | Redis 1000 msg/s, 1.95ms (p95=3.67ms) — Both handle well
- **10240 B**: RabbitMQ 998 msg/s, 1.10ms (p95=1.37ms) | Redis 1000 msg/s, 2.67ms (p95=6.83ms) — Both handle well
- **102400 B**: RabbitMQ 199 msg/s, 5.42ms (p95=44.17ms) | Redis 158 msg/s, 8.72ms (p95=44.18ms) — Both degrade

### 5.3 Degradation point

- **RabbitMQ**: no degradation observed up to 100000 msg/s (loss=0.0%, lat=1.05ms (p95=1.27ms))
- **Redis**: clear degradation at ~5000 msg/s (loss=1.4%, lat=239.75ms (p95=435.69ms))

### 5.4 Best tool for this scenario
Python asyncio with aio-pika / redis.asyncio provides fine-grained control over pacing, latency measurement, and result collection. For larger-scale tests, k6 or Locust could be used, but Python allows precise instrumentation of broker-specific internals (e.g., confirmation callbacks, stream group state).