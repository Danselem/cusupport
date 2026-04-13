# Metrics Monitoring System - Usage Guide

## Overview

The LiveKit Customer Support Agent includes a comprehensive metrics monitoring system that tracks all calls and provides multiple interfaces to view and query the data.

## Where Are Metrics Stored?

After each call ends, metrics are automatically saved to:

### File-Based Storage (Default)
```
livegen/metrics_data/2025-02-14/
├── room-abc123.json
├── room-def456.json  
└── room-ghi789.json
```

Each JSON file contains:
```json
{
  "room_id": "room-abc123",
  "duration": 125.5,
  "consent_given": true,
  "phone_collected": true,
  "phone_number": "+1234567890",
  "error_count": 0,
  "retries": 0,
  "created_at": "2025-02-14T10:30:00Z"
}
```

### SQLite Database Alternative
```
livegen/metrics.db
├── calls table
└── Indexed for fast queries
```

## 5 Ways to View Metrics

### 1. Web Dashboard 📊

**Best for:** Visual overview with charts

```
http://localhost:8081/metrics/dashboard
```

Shows:
- Live statistics cards
- Call distribution charts  
- Recent calls table
- Auto-refreshing data

### 2. HTTP API 🔌

**Best for:** Programmatic access

```bash
# Get stats
curl http://localhost:8081/metrics/stats
# Response:
# {
#   "total_calls": 42,
#   "consent_rate": 95.2,
#   "avg_duration": 125.3,
#   ...
# }

# List calls
curl http://localhost:8081/metrics/all?limit=10
# Response: [{"room_id": "...", "duration": 125.5, ...}, ...]

# Get specific call
curl http://localhost:8081/metrics/call/room-abc123

# Date range query
curl "http://localhost:8081/metrics/by-date?start_date=2025-01-01&end_date=2025-01-31"
```

### 3. Command-Line Interface 💻

**Best for:** Terminal-based queries

```bash
# Show stats
python -m src.metrics_cli stats
# Output:
# 📊 Agent Metrics Summary
# 
# Total Calls:           42
# Average Duration:      125.3 seconds
# Consent Rate:          95.2%
# Phone Collection Rate: 88.1%
# Error Rate:            2.4%
# ...

# List calls
python -m src.metrics_cli list --limit 50
# Output: Formatted table with recent calls

# Show specific call
python -m src.metrics_cli show room-abc123
# Output: Detailed metrics for that call

# Date range
python -m src.metrics_cli range 2025-01-01 2025-01-31

# Export to JSON
python -m src.metrics_cli export report.json
```

### 4. Python API 🐍

**Best for:** Custom analysis scripts

```python
from src.monitoring import metrics

# Get all calls
all_calls = metrics.get_all_calls(limit=100)
for call in all_calls:
    print(f"Call {call['room_id']}: {call['duration']}s")

# Get specific call
call = metrics.get_call_metrics("room-abc123")
if call:
    print(f"Consent: {call['consent_given']}")
    print(f"Phone: {call['phone_collected']}")
    print(f"Errors: {call['error_count']}")

# Get statistics
stats = metrics.get_stats()
print(f"Total calls: {stats['total_calls']}")
print(f"Consent rate: {stats['consent_rate']}%")
print(f"Error rate: {stats['error_rate']}%")

# Date range queries
from datetime import datetime, timedelta
start = datetime(2025, 1, 1)
end = datetime(2025, 1, 31)
calls = metrics.get_calls_by_date(start.isoformat(), end.isoformat())
print(f"Found {len(calls)} calls in range")
```

### 5. Raw JSON Files 📄

**Best for:** Direct file inspection

```bash
# View today's calls (file-based storage)
cat livegen/metrics_data/2025-02-14/room-abc123.json | jq .

# Find all calls from a date
find livegen/metrics_data/2025-02-14 -name "*.json" | wc -l
```

## Common Queries

### Find high-error calls
```bash
python -c "
from src.monitoring import metrics
calls = metrics.get_all_calls(limit=1000)
errors = [c for c in calls if c['error_count'] > 0]
print(f'Found {len(errors)} calls with errors')
for call in errors:
    print(f\"  {call['room_id']}: {call['error_count']} errors\")
"
```

### Calculate consent success rate
```bash
python -c "
from src.monitoring import metrics
stats = metrics.get_stats()
print(f\"Consent Rate: {stats['consent_rate']}%\")
print(f\"Phone Collection: {stats['phone_collection_rate']}%\")
"
```

### Export weekly report
```bash
from src.metrics_cli import MetricsCLI
from src.monitoring import metrics
from datetime import datetime, timedelta

cli = MetricsCLI(metrics)

# Get this week's data
start = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
end = datetime.now().strftime('%Y-%m-%d')

# Export
cli.export_json(f'report_{start}_to_{end}.json')
```

## Switching Storage Backends

### Use File Storage (Default)
```bash
# In .env:
METRICS_STORAGE=file
# Creates: ./metrics_data/YYYY-MM-DD/room-id.json
```

### Use SQLite Storage
```bash
# In .env:
METRICS_STORAGE=sqlite
METRICS_DB_PATH=./metrics.db
# Creates: ./metrics.db with indexed calls table
```

**Performance Note:**
- File storage: Good for < 100k calls
- SQLite: Better for production with frequent queries

## Integration Examples

### Send metrics to external dashboard
```python
import requests
from src.monitoring import metrics

# Every few minutes, send stats to external service
stats = metrics.get_stats()
requests.post('https://your-analytics.com/api/metrics', json=stats)
```

### Generate daily report
```python
from src.monitoring import metrics
from datetime import datetime, timedelta
import json

# Get yesterday's data
today = datetime.now().strftime('%Y-%m-%d')
calls = metrics.get_calls_by_date(today, today)

report = {
    'date': today,
    'total_calls': len(calls),
    'consent_rate': sum(1 for c in calls if c['consent_given']) / len(calls) * 100,
    'avg_duration': sum(c['duration'] for c in calls) / len(calls),
}

# Save or email
with open(f'reports/{today}.json', 'w') as f:
    json.dump(report, f)
```

### Alert on high error rate
```python
from src.monitoring import metrics

stats = metrics.get_stats()
if stats['error_rate'] > 10:  # Alert if > 10% errors
    send_alert(f"High error rate: {stats['error_rate']}%")
```

## Retention & Cleanup

### Archive old metrics
```bash
# Move metrics older than 30 days to archive
find livegen/metrics_data -mtime +30 -exec mv {} archive/ \;

# Or delete if using SQLite (database handles cleanup)
```

### Export before cleanup
```bash
# Always export first!
python -m src.metrics_cli export backup_$(date +%Y-%m-%d).json

# Then clean up
rm -rf livegen/metrics_data/2024-*
```

## Troubleshooting

### Metrics not appearing
- ✅ Ensure call completed normally (not dropped)
- ✅ Check storage location: `metrics_data/` or `metrics.db`
- ✅ Verify storage type: `METRICS_STORAGE` env variable
- ✅ Check file permissions on `metrics_data/` directory

### Dashboard shows "No data"
- ✅ Ensure Flask is installed: `pip install flask`
- ✅ Run at least one complete call
- ✅ Wait for call to end (metrics saved on completion)
- ✅ Refresh dashboard page

### Slow queries on large datasets
- ✅ Switch to SQLite storage in `.env`
- ✅ Archive old files: `mv metrics_data/2024-* archive/`
- ✅ Use date range filters instead of `get_all_calls()`

## Architecture

The metrics system consists of 4 layers:

```
┌─────────────────────────────────────┐
│   Query Interfaces                  │
│  (Dashboard, API, CLI, Python)      │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│   MetricsCollector                  │
│   (Record events, query in-memory)  │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│   StorageBackend (Abstract)         │
│   (FileStorageBackend,              │
│    SQLiteStorageBackend)            │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│   Persistent Storage                │
│   (JSON files or SQLite DB)         │
└─────────────────────────────────────┘
```

This design allows:
- Switching storage backends without code changes
- Adding new query interfaces easily
- Efficient in-memory caching with persistence
- Extensibility for custom storage (S3, BigQuery, etc.)
