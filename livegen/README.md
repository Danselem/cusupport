# BPO Service - AI-Powered Business Process Outsourcing

A production-ready omnichannel customer service platform powered by LiveKit and Google's Gemini Realtime LLM. Designed to handle customer inquiries, complaints, sales, telesales, and loyalty programs.

## Overview

BPO Service is an AI-driven contact center solution that provides:

- **Omnichannel Support** - Phone, email, chat, and social media
- **Customer Acquisition** - Sales and telesales capabilities
- **Customer Retention** - Loyalty programs and lifecycle management
- **Emotion-Aware Responses** - Sentiment-based conversation handling
- **Comprehensive Analytics** - Full call metrics and transcripts

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        BPO Service                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    │
│  │   Phone    │    │   Email    │    │   Chat/    │    │
│  │   (SIP)   │    │  (SMTP)    │    │ Social    │    │
│  └─────┬──────┘    └─────┬──────┘    └─────┬──────┘    │
│        │                │                │                │           │
│        └────────────────┼────────────────┘                │
│                       ▼                                  │
│            ┌─────────────────────┐                     │
│            │   LiveKit Agent   │                     │
│            │     Server      │                     │
│            └───────┬─────────┘                     │
│                    │                            │
│        ┌─────────┴─────────┐                 │
│        ▼                 ▼                 │
│  ┌──────────┐    ┌──────────┐          │
│  │ Gemini  │    │  Agent  │          │
│  │ Realtime│    │   AI   │          │
│  │   LLM  │    │ Logic  │          │
│  └────────┘    └────────┘          │
│                                      │
│        ┌─────────┴─────────┐          │
│        ▼               ▼          │
│  ┌──────────┐ ┌─────────┐         │
│  │Metrics │ │Transcript│         │
│  │ Storage│ │ Storage │         │
│  └────────┘ └─────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
bpo-service/
├── src/
│   ├── agent.py          # Main entry point
│   ├── models.py        # Pydantic data models
│   └── prompts.py     # System prompts & instructions
├── webembed/         # Frontend web interface
├── tests/           # Test suite
├── metrics_data/    # Call recordings & metrics
├── .env            # Environment configuration
├── pyproject.toml   # Project dependencies
└── README.md       # This file
```

## Features

### 🎯 Core Capabilities

| Feature | Description |
|---------|------------|
| **Voice Calls** | Real-time phone support via SIP |
| **Emotion Detection** | Sentiment-aware responses |
| **Phone Collection** | DTMF digit capture |
| **Session Management** | Full call lifecycle tracking |
| **Metrics** | Comprehensive analytics |
| **Transcripts** | Full conversation recording |

### 📋 Service Modules

1. **Customer Support**
   - Inquiry handling
   - Complaint resolution
   - Technical support triage
   - FAQ automation

2. **Sales & Telesales**
   - Product information
   - Lead qualification
   - Upselling/cross-selling
   - Appointment scheduling

3. **Customer Retention**
   - Loyalty program support
   - Feedback collection
   - Account management
   - Win-back campaigns

## Quick Start

### Prerequisites

- Python 3.12+
- LiveKit Cloud account (or self-hosted)
- Google AI API key (Gemini Realtime)

### Installation

```bash
# Clone the repository
cd bpo-service

# Install dependencies (uses uv)
make bootstrap

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Running

```bash
# Development mode
make agent

# Console testing
make run-console

# Frontend
make frontend
```

## Configuration

### Environment Variables

```env
# LiveKit
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret

# Google AI
GOOGLE_API_KEY=your_google_api_key
GOOGLE_LLM_MODEL=gemini-2.5-flash-native-audio-preview-12-2025
```

### Agent Settings

Edit `src/agent.py` to customize:

- **Voice**: `voice="Puck"` (or other Gemini voices)
- **Instructions**: `src/prompts.py` for system prompts
- **Session timeout**: Adjust `asyncio.sleep()` duration

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov
```

## Metrics & Analytics

Call metrics are saved to `metrics_data/` after each call:

```json
{
  "session_id": "room_123",
  "call_start": 1775950000.0,
  "call_end": 1775950100.0,
  "duration": 100.0,
  "total_turns": 5,
  "interruptions": 1,
  "collected_info": {"phone": "555-1234"},
  "success": true,
  "end_reason": "completed"
}
```

## Omnichannel Setup

### Phone (SIP)

Configure SIP trunk in LiveKit Cloud:
```bash
lk sip trunk create --name bpo-trunk
lk sip inbound create --trunk bpo-trunk
```

### Email/Chat

Coming soon - use LiveKit's MCP integrations.

## Production Deployment

### Docker

```bash
docker-compose up -d
```

### Kubernetes

```bash
kubectl apply -f k8s/
```

### Environment

- Use LiveKit Cloud for production
- Enable recording for compliance
- Set up SIP trunk for phone

## License

MIT License