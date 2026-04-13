# Conversation Logging - Enhanced Metrics

Your metrics now include **full conversation transcripts** with timestamps and speaker information!

## What's Now Tracked

### Before (Basic Metrics Only)
```json
{
  "room_id": "console",
  "duration_seconds": 0.07,
  "consent_obtained": false,
  "phone_collected": false,
  "error_count": 0
}
```

### After (With Conversation Logging)
```json
{
  "room_id": "console",
  "duration_seconds": 125.5,
  "consent_obtained": true,
  "phone_collected": true,
  "error_count": 0,
  "conversation": [
    {
      "timestamp": "2026-02-28T12:22:53.123456",
      "role": "system",
      "message": "Call initiated"
    },
    {
      "timestamp": "2026-02-28T12:22:54.234567",
      "role": "agent",
      "message": "[instruction] Briefly introduce yourself..."
    },
    {
      "timestamp": "2026-02-28T12:22:58.345678",
      "role": "user",
      "message": "Consent: APPROVED"
    },
    {
      "timestamp": "2026-02-28T12:23:01.456789",
      "role": "user",
      "message": "Phone Number: 5551234567"
    },
    {
      "timestamp": "2026-02-28T12:24:58.567890",
      "role": "system",
      "message": "Call ended"
    }
  ]
}
```

## 3 Ways to View Your Conversation Data

### 1. 🎯 Quick View Script (Recommended)

```bash
# List all calls with conversation status
python view_metrics.py

# View a specific call with full transcript
python view_metrics.py metrics_data/2026-02-28/room-abc123.json
```

Output shows:
- ✅ Call metadata (duration, consent, phone)
- ✅ Timestamped conversation turns
- ✅ Speaker identification (AGENT, USER, SYSTEM)
- ✅ Full message text

### 2. 💻 CLI Command

```bash
python -m src.metrics_cli show room-abc123

# This now includes conversation in the output
```

### 3. 📁 Direct File Access

```bash
# List today's metrics
ls -la metrics_data/2026-02-28/

# View raw JSON
cat metrics_data/2026-02-28/room-abc123.json | python -m json.tool

# Pretty print
cat metrics_data/2026-02-28/room-abc123.json | jq '.conversation'
```

## What Messages Get Logged

### System Messages
- **Call initiated** - When session starts
- **Call ended** - When session ends

### Agent Messages  
- **Instructions** - What the agent is instructed to say
  - Consent requests
  - Greetings/welcome
  - Help offerings
  - Error responses

### User Messages
- **User Input Events**
  - `Consent: APPROVED` - When user gives consent
  - `Consent: DENIED` - When user denies consent  
  - `Phone Number: XXX` - When phone is collected
  - Custom user responses (when integrated with ASR)

## Recent Changes Made

### 1. Enhanced `monitoring.py`
- Added `ConversationTurn` dataclass
- Added `add_message()` method to `CallMetrics`
- New `add_conversation_message()` method in `MetricsCollector`
- New `get_conversation()` query method
- Conversation included in `to_dict()` output

### 2. Enhanced `agent.py`
- Calls `metrics.create_call()` at session start
- Logs "Call initiated" and "Call ended" messages
- Calls `metrics.end_call()` in finally block to save metrics

### 3. Enhanced `tools.py`
- Consent tool logs "Consent: APPROVED/DENIED"
- Phone tool logs "Phone Number: XXX"

## Usage Examples

### Example 1: Review a Recent Call

```bash
python view_metrics.py
# Output shows list of metrics files

python view_metrics.py metrics_data/2026-02-28/console_20260228_122253.json
# Output:
# 📊 CALL METRICS - console_20260228_122253.json
# ==========================================
# Room ID:             console
# Duration:            125.5 seconds
# Consent:             ✅ Given
# Phone Collected:     ✅ Yes
# Errors:              0
#
# 📝 CONVERSATION TRANSCRIPT (5 turns)
# ==========================================
#
# 1. [12:22:53] ⚙️ SYSTEM:
#    Call initiated
#
# 2. [12:22:54] 🤖 AGENT:
#    [instruction] Briefly introduce yourself...
#
# 3. [12:22:58] 👤 USER:
#    Consent: APPROVED
#
# 4. [12:23:01] 👤 USER:
#    Phone Number: 5551234567
#
# 5. [12:24:58] ⚙️ SYSTEM:
#    Call ended
```

### Example 2: Export Conversation as Text

```bash
python -c "
import json
from pathlib import Path

# Read metrics file
metrics = json.load(open('metrics_data/2026-02-28/room-id.json'))

# Extract conversation
for turn in metrics['conversation']:
    role = turn['role'].upper()
    msg = turn['message']
    print(f'{role}: {msg}')
"
```

### Example 3: Analyze Consent Success Rate

```bash
python -c "
import json
import glob

# Get all metrics files
files = glob.glob('metrics_data/**/*.json', recursive=True)

approved = 0
denied = 0

for filepath in files:
    data = json.load(open(filepath))
    if data['consent_obtained']:
        approved += 1
    else:
        denied += 1

total = approved + denied
if total > 0:
    rate = (approved / total) * 100
    print(f'Consent Approval Rate: {rate:.1f}% ({approved}/{total})')
"
```

## Integration with Existing Systems

### Python API
```python
from src.monitoring import metrics

# Add a message programmatically
metrics.add_conversation_message(room_id, "user", "Hello!")

# Retrieve conversation
transcript = metrics.get_conversation(room_id)
for turn in transcript:
    print(f"{turn['role']}: {turn['message']}")
```

### Web Dashboard Update

The conversation data is now available through:
- **Metrics API**: `GET /metrics/call/{room_id}` includes conversation
- **Metrics CLI**: `show` command displays conversation
- **Raw JSON**: Direct access via file system

## Limitations & Future Enhancements

### Current Limitations
- Messages are captured at key decision points (consent, phone)
- Full ASR transcripts not yet integrated (requires RTCSession integration)
- No TTS response text captured (would require LLM response interception)

### Future Enhancements
1. **Full STT/TTS Integration** - Capture actual user speech and agent responses
2. **Sentiment Analysis** - Add sentiment/emotion to messages
3. **Conversation Summary** - Auto-generate summaries of calls
4. **Search & Filter** - Find conversations by content
5. **Export Formats** - PDF, CSV, Markdown reports

## Troubleshooting

### No conversation data appearing?

1. ✅ Ensure call completes (not dropped early)
2. ✅ Check that consent/phone tools are being called
3. ✅ Verify `metrics.create_call()` called at session start
4. ✅ Check metrics file location: `./metrics_data/YYYY-MM-DD/`

### Script permissions issue?

```bash
chmod +x view_metrics.py
```

### JSON parsing errors?

```bash
# Validate JSON format
python -m json.tool metrics_data/*/room-*.json
```

## Technical Details

### Timestamp Format
All conversation timestamps use **ISO 8601** format with UTC timezone:
```
2026-02-28T12:22:53.778296
```

### Message Types

| Role | Source | Example |
|------|--------|---------|
| `system` | Agent lifecycle | "Call initiated", "Call ended" |
| `agent` | Agent responses | Consent prompts, greetings |
| `user` | User actions | Consent decisions, phone input |

### Storage Format

Conversations are stored directly in the metrics JSON file under the `"conversation"` key as an array of turn objects.

Each turn has:
- `timestamp`: ISO 8601 format
- `role`: "agent", "user", or "system"
- `message`: Text content
- `duration_ms`: Optional duration for audio (future use)

## Questions?

If metrics still not showing conversation data:
1. Run a fresh test call
2. Check the raw JSON file directly
3. Verify the agent is calling `metrics.create_call()
4. Check logs for any errors during message logging
