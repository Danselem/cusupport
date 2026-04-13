# PipeGen - Customer Service Conversational AI

A real-time conversational AI agent built with [Pipecat](https://pipecat.ai/) for customer service applications.

## Features

- Real-time voice conversation
- Google Gemini Live (unified LLM + STT + TTS)
- Silero VAD for voice activity detection
- Daily.co for real-time transport

## Prerequisites

- Python 3.12+
- Google AI account (for Gemini Live API)
- Daily.co account (for video/audio transport)

## Installation

```bash
# Clone the repository
cd pipegen

# Install dependencies
pip install -e ".[dev]"

# Copy environment file
cp .env.example .env

# Edit .env with your API keys and credentials
```

## Configuration

Edit `.env` with your API keys:

| Variable | Description |
|----------|-------------|
| `DAILY_API_KEY` | Your Daily.co API key |
| `DAILY_ROOM_URL` | Your Daily.co room URL |
| `GOOGLE_API_KEY` | Your Google Gemini API key |

## Usage

```bash
# Run the agent
make run

# Or directly
python -m pipegen.agent
```

## Development

```bash
# Install dev dependencies
make install

# Run linters
make lint

# Run type checking
make typecheck

# Run tests
make test

# Format code
make format
```

## Project Structure

```
pipegen/
├── src/pipegen/
│   ├── __init__.py
│   ├── agent.py              # Main agent implementation
│   ├── prompts.py            # System prompts
│   └── services.py           # Service factory
├── pyproject.toml            # Project configuration
├── .env.example              # Environment variables template
├── Makefile                  # Common commands
└── README.md                 # This file
```

## License

MIT
