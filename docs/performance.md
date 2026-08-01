# Performance & Sizing Guide

## Collection Speed

The application collects inventory from all servers concurrently using configurable
SSH sessions. Collection time depends on the concurrency setting.

### 400 Servers — Expected Collection Times

| Concurrency Setting | Total Time | Batches |
|---------------------|-----------|---------|
| **20 concurrent** (default) | **15-20 minutes** | 20 batches x 45-60s |
| 30 concurrent | 10-13 minutes | 14 batches |
| 40 concurrent | 8-10 minutes | 10 batches |
| 50 concurrent | 6-8 minutes | 8 batches |

### Per-Server Timing Breakdown

| Phase | Time | Description |
|-------|------|-------------|
| SSH Connect | 2-5 sec | Key exchange, authentication |
| Distribution Detection | 1 sec | `cat /etc/os-release` |
| 12 Collectors | 30-45 sec | ~38 SSH commands total |
| Snapshot Save (gzip) | 1-2 sec | Compress JSON, write to disk |
| Change Detection | <1 sec | Compare with previous snapshot |
| **Total per server** | **35-55 sec** | Varies by server response time |

---

## CPU & Memory Requirements

### During Data Collection (Peak Load)

| Concurrency | CPU Usage | RAM Usage | Notes |
|-------------|-----------|-----------|-------|
| 20 concurrent | 1.5-2.0 vCPU | 1.5-2.0 GB | Default setting |
| 30 concurrent | 2.0-2.5 vCPU | 2.0-2.5 GB | Recommended for 400 servers |
| 40 concurrent | 2.5-3.0 vCPU | 2.5-3.0 GB | Approaching t3.medium limits |
| 50 concurrent | 3.0-3.5 vCPU | 3.0-3.5 GB | Requires t3.large or higher |

### At Rest (No Collection Running)

| Component | CPU | RAM |
|-----------|-----|-----|
| FastAPI (Uvicorn, 4 workers) | 0.1-0.3 vCPU | 400-600 MB |
| APScheduler | negligible | 20 MB |
| SQLite | negligible | 50-100 MB |
| **Total idle** | **~0.2 vCPU** | **~600 MB** |

### Peak Resource Breakdown (20 Concurrent)

```
CPU:
  Paramiko SSH threads:     ~0.8 vCPU  (20 threads doing I/O)
  JSON parsing:             ~0.3 vCPU  (parsing command output)
  Gzip compression:         ~0.2 vCPU  (snapshot compression)
  Change detection:         ~0.1 vCPU  (dict comparison)
  FastAPI + SQLAlchemy:     ~0.1 vCPU  (DB writes)
  Total:                    ~1.5 vCPU

Memory:
  Paramiko connections:     ~400 MB  (20 x ~20 MB each)
  Collector data in memory: ~200 MB  (parsed JSON per server)
  FastAPI workers:          ~400 MB  (4 Uvicorn workers)
  SQLite cache:             ~100 MB
  Python interpreter:       ~150 MB
  Total:                    ~1.3 GB
```

---

## Recommended EC2 Instances

| Instance | vCPU | RAM | Best For | Monthly Cost |
|----------|------|-----|----------|-------------|
| t3.medium | 2 | 4 GB | 400 servers at 20 concurrent | ~$30 |
| **t3.large** | **2** | **8 GB** | **400 servers at 30 concurrent (recommended)** | **~$60** |
| t3.xlarge | 4 | 16 GB | 1000+ servers at 50 concurrent | ~$120 |

### Recommendation for 400 Servers

**t3.large (2 vCPU / 8 GB RAM)** with 30 concurrent SSH sessions:

- Collection completes in ~12 minutes daily
- Plenty of headroom during collection peak
- Room to grow to 600-700 servers without upgrading
- API stays responsive during collection
- Cost: ~$60/month

If budget is tight, t3.medium ($30/mo) works fine at 20 concurrent — collection takes ~18 minutes instead of 12.

---

## Disk I/O & Storage

| Metric | Value |
|--------|-------|
| Snapshot size per server | 50-150 KB (compressed) |
| 400 servers x 365 days | 20-55 GB/year |
| Daily write burst | ~60 MB (400 x 150 KB) |
| SQLite database size | 50-200 MB |
| **Recommended disk** | **100 GB gp3** |

### Storage Growth Estimate

| Timeframe | Snapshots | SQLite | Logs | Total |
|-----------|-----------|--------|------|-------|
| 1 month | 1.8 GB | 50 MB | 200 MB | ~2 GB |
| 6 months | 10 GB | 100 MB | 1 GB | ~11 GB |
| 1 year | 20 GB | 150 MB | 2 GB | ~22 GB |
| 2 years | 40 GB | 200 MB | 4 GB | ~44 GB |

Retention policy (default 365 days) automatically cleans old snapshots.

---

## Network Bandwidth

| Direction | Peak Usage | Duration |
|-----------|-----------|----------|
| Outbound SSH (to servers) | 2-5 Mbps | During collection |
| Inbound SSH responses | 5-10 Mbps | During collection |
| Web UI traffic | <1 Mbps | Always |
| Secrets Manager API | Negligible | 1 call per profile per cycle |

Standard EC2 networking is more than sufficient. No enhanced networking required.

---

## Scaling Guide

| Servers | Concurrency | Instance | Collection Time | Monthly Cost |
|---------|-------------|----------|-----------------|-------------|
| 100 | 20 | t3.medium | ~5 min | ~$30 |
| 300 | 20 | t3.medium | ~15 min | ~$30 |
| **400** | **30** | **t3.large** | **~12 min** | **~$60** |
| 700 | 40 | t3.large | ~18 min | ~$60 |
| 1000 | 50 | t3.xlarge | ~20 min | ~$120 |
| 2000 | 50 | t3.xlarge | ~40 min | ~$120 |

### How to Adjust Concurrency

Edit `.env` or environment variable:

```
SCHEDULER_MAX_CONCURRENT_COLLECTIONS=30
```

Restart the service:

```bash
sudo systemctl restart linux-inventory-backend
```

---

## Performance Characteristics

The application is **network I/O bound**, not CPU bound:

- Most time is spent waiting for SSH responses from remote servers
- CPU stays moderate even with many concurrent sessions
- One slow server never blocks others (independent async tasks)
- Failed servers are retried independently every hour
- Servers intentionally offline are tolerated gracefully

### What Affects Collection Speed

| Factor | Impact | Mitigation |
|--------|--------|-----------|
| Server response latency | High | Increase concurrency |
| SSH key exchange | Medium | Connection pooling and reuse |
| Package list size (1000+ pkgs) | Medium | Streaming output parsing |
| Network hops between EC2 and servers | Medium | Deploy in same VPC/region |
| Disk I/O for snapshot writes | Low | gp3 is more than sufficient |
| SQLite writes | Low | Batched, async |

### Bottleneck Indicators

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Collection > 30 min | Concurrency too low | Increase to 30-40 |
| High CPU (>90%) sustained | Too many concurrent SSH | Reduce concurrency or upgrade instance |
| High memory (>85%) | Too many connections | Reduce concurrency or upgrade instance |
| Individual servers timeout | Server unreachable | Check network, SSH config |
| Slow API during collection | Workers starving API | Upgrade to t3.large |
