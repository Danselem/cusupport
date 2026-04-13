# Pipecat Architecture Guide (2026)

> **Role**: AI orchestration and conversation pipeline framework  
> **Best Practice**: Pipecat Cloud (managed GA Jan 2026) for production, Docker/K8s for custom requirements  
> **Last Updated**: February 2026

---

## Executive Summary

Pipecat is the **world's most widely used open-source framework** for building voice and multimodal conversational AI agents. Created by Daily (pioneers in real-time video since 2016), Pipecat provides a **frame-based architecture** that treats everything—audio, text, control signals—as frames flowing through composable pipelines.

**Key Milestone**: Pipecat Cloud became **Generally Available in January 2026**, offering a managed platform purpose-built for deploying voice AI at scale.

For BPO customer service agents, Pipecat serves as the **AI orchestration layer**:
- Manages STT → LLM → TTS pipelines with ultra-low latency
- Handles turn detection, interruptions, and context management
- Integrates 40+ AI service providers (vendor-neutral)
- Supports speech-to-speech models (OpenAI Realtime, Gemini Live)

**Key Decision**: Use **Pipecat Cloud** for rapid deployment (multi-region, auto-scaling, includes Daily WebRTC). Choose **self-hosted Docker/Kubernetes** only for maximum customization or specific compliance needs.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PIPECAT PIPELINE ARCHITECTURE                        │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                        FRAME FLOW                                   │   │
│   │                                                                      │   │
│   │   AudioRawFrame → VAD → STT → TextFrame → LLM → TextFrame → TTS   │   │
│   │                        ↓                                            │   │
│   │                 ControlFrames (interruptions, end-turn)             │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      PROCESSOR CHAIN                                │   │
│   │                                                                      │   │
│   │   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐        │   │
│   │   │Transport │ → │   VAD    │ → │   STT    │ → │Context   │        │   │
│   │   │  Input   │   │ (Silero) │   │ (RIVA)   │   │Aggregator│        │   │
│   │   └──────────┘   └──────────┘   └──────────┘   └─────┬────┘        │   │
│   │                                                      │              │   │
│   │   ┌──────────┐   ┌──────────┐   ┌──────────┐        │              │   │
│   │   │Transport │ ← │   TTS    │ ← │   LLM    │ ←──────┘              │   │
│   │   │  Output  │   │ (RIVA)   │   │(GPT-4o)  │                       │   │
│   │   └──────────┘   └──────────┘   └──────────┘                       │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ API Calls / gRPC
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AI SERVICE PROVIDERS                                 │
│                                                                              │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│   │     STT      │  │     LLM      │  │     TTS      │  │   Extras     │    │
│   ├──────────────┤  ├──────────────┤  ├──────────────┤  ├──────────────┤    │
│   │ • NVIDIA RIVA│  │ • OpenAI     │  │ • NVIDIA RIVA│  │ • Google     │    │
│   │ • Deepgram   │  │ • Anthropic  │  │ • Cartesia   │  │ • Azure      │    │
│   │ • AssemblyAI │  │ • Google     │  │ • ElevenLabs │  │ • AWS        │    │
│   │ • Whisper    │  │ • Meta       │  │ • Deepgram   │  │ • Custom     │    │
│   │ • Azure      │  │ • Cerebras   │  │ • OpenAI     │  │   Models     │    │
│   └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Concepts (Frame-Based Architecture)

Pipecat's power comes from a simple, elegant abstraction: **everything is a frame**.

### Frame Types

```python
from pipecat.frames.frames import (
    AudioRawFrame,      # Raw PCM audio data
    TextFrame,          # Transcriptions and LLM responses
    ControlFrame,       # Interruptions, end-of-turn signals
    EndFrame,           # Pipeline termination
    UserStartedSpeakingFrame,
    UserStoppedSpeakingFrame,
    BotStartedSpeakingFrame,
    BotStoppedSpeakingFrame,
)
```

**Frame Flow Example**:
```
User speaks → AudioRawFrame → VAD detects speech start
                                    ↓
                          UserStartedSpeakingFrame
                                    ↓
                     STT transcribes → TextFrame("Hello")
                                    ↓
                     LLM generates → TextFrame("Hi! How can I help?")
                                    ↓
                     TTS synthesizes → AudioRawFrame (response)
                                    ↓
                          Transport outputs audio
```

### Processors

Processors are the building blocks that transform frames. Each processor:
- Receives frames from upstream
- Transforms or processes them
- Emits new frames downstream

```python
from pipecat.processors.frame_processor import FrameProcessor

class CustomProcessor(FrameProcessor):
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        # Process incoming frame
        if isinstance(frame, TextFrame):
            # Modify text
            modified_text = frame.text.upper()
            new_frame = TextFrame(text=modified_text)
            await self.push_frame(new_frame, direction)
        else:
            # Pass through non-text frames (CRITICAL!)
            await self.push_frame(frame, direction)
```

**Common Pitfall**: Always pass through control frames and EndFrame, or your pipeline will hang!

### Pipelines

Pipelines chain processors together. Frames flow sequentially through the chain.

```python
from pipecat.pipeline.pipeline import Pipeline

pipeline = Pipeline([
    transport.input(),           # Audio in
    silero_vad,                  # Voice activity detection
    riva_stt,                    # Speech-to-text
    context_aggregator.user(),   # Aggregate user context
    openai_llm,                  # Language model
    context_aggregator.assistant(), # Aggregate assistant context
    riva_tts,                    # Text-to-speech
    transport.output(),          # Audio out
])
```

### Tasks

A Task executes a pipeline with a specific configuration:

```python
from pipecat.pipeline.task import PipelineTask

task = PipelineTask(
    pipeline,
    params=PipelineParams(
        allow_interruptions=True,      # Enable barge-in
        enable_metrics=True,            # Latency tracking
        enable_usage_metrics=True,      # Token tracking
        report_only_initial_ttfb=True,  # Time-to-first-byte
    ),
)
```

---

## Transport Abstraction

Pipecat is **transport-agnostic**. Choose based on your deployment:

| Transport | Latency | Best For | 2026 Recommendation |
|-----------|---------|----------|-------------------|
| **Daily WebRTC** | ~100ms | Production browser/mobile apps | **PRIMARY** |
| **LiveKit WebRTC** | ~100ms | LiveKit ecosystem integration | **ALTERNATIVE** |
| **WebSocket** | ~300ms | Server-to-server, prototyping | Development only |
| **Local Audio** | N/A | Local testing | Development only |

### Daily WebRTC Transport (Recommended)

```python
from pipecat.transports.services.daily import DailyParams, DailyTransport

transport = DailyTransport(
    room_url="https://your-domain.daily.co/room-name",
    token="your-token",
    bot_name="Customer Service Agent",
    params=DailyParams(
        audio_out_enabled=True,
        audio_out_sample_rate=24000,
        vad_enabled=True,
        vad_analyzer=SileroVADAnalyzer(),
        vad_audio_passthrough=True,
    ),
)
```

### LiveKit WebRTC Transport

```python
from pipecat.transports.services.livekit import LiveKitTransport

transport = LiveKitTransport(
    room_url="wss://your-project.livekit.cloud",
    token="your-token",
    params=LiveKitParams(
        audio_out_sample_rate=24000,
        vad_enabled=True,
    ),
)
```

### WebSocket Transport (Development)

```python
from pipecat.transports.network.websocket_server import WebsocketServerParams

transport = WebsocketServerTransport(
    params=WebsocketServerParams(
        audio_out_sample_rate=24000,
        host="0.0.0.0",
        port=8765,
    ),
)
```

---

## Local Development Workflow (2026 Best Practices)

### Prerequisites

```bash
# 2026 Recommended: Use UV package manager (faster than pip)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create project
mkdir bpo-agent && cd bpo-agent
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install Pipecat with dependencies
uv pip install "pipecat-ai[daily,openai,riva,silero]"
```

### Project Structure

```
bpo-agent/
├── bot.py                 # Main bot implementation
├── bot_runner.py          # HTTP server for spawning bots
├── prompts/
│   └── system_prompt.txt  # LLM system prompt
├── requirements.txt       # Dependencies
├── .env                   # Environment variables (gitignored)
└── Dockerfile             # Container definition
```

### Basic Bot Implementation

```python
# bot.py
import os
import asyncio
from dotenv import load_dotenv
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineTask, PipelineParams
from pipecat.transports.services.daily import DailyParams, DailyTransport
from pipecat.services.openai import OpenAILLMService
from pipecat.services.riva import RivaSTTService, RivaTTSService
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext

load_dotenv()

async def main():
    # 1. Configure transport (Daily WebRTC)
    transport = DailyTransport(
        room_url=os.getenv("DAILY_ROOM_URL"),
        token=os.getenv("DAILY_TOKEN"),
        bot_name="BPO Agent",
        params=DailyParams(
            audio_out_enabled=True,
            audio_out_sample_rate=24000,
            vad_enabled=True,
            vad_analyzer=SileroVADAnalyzer(),
            vad_audio_passthrough=True,
        ),
    )
    
    # 2. Configure AI services
    stt = RivaSTTService(
        url=os.getenv("RIVA_URL", "grpc.nvcf.nvidia.com:443"),
        model="parakeet-ctc-1.1b-asr",
    )
    
    llm = OpenAILLMService(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o-mini",
    )
    
    tts = RivaTTSService(
        url=os.getenv("RIVA_URL", "grpc.nvcf.nvidia.com:443"),
        model="fastpitch-hifigan",
        voice_id="English-US.Female-1",
    )
    
    # 3. Configure conversation context
    messages = [
        {
            "role": "system",
            "content": """You are a professional customer service representative.
            Be helpful, empathetic, and concise.
            Always ask clarifying questions if the customer's issue is unclear.""",
        }
    ]
    context = OpenAILLMContext(messages)
    context_aggregator = llm.create_context_aggregator(context)
    
    # 4. Build pipeline
    pipeline = Pipeline([
        transport.input(),
        stt,
        context_aggregator.user(),
        llm,
        tts,
        transport.output(),
        context_aggregator.assistant(),
    ])
    
    # 5. Create task
    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            allow_interruptions=True,
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
    )
    
    # 6. Event handlers
    @transport.event_handler("on_first_participant_joined")
    async def on_first_participant_joined(transport, participant):
        await transport.capture_participant_transcription(participant["id"])
        # Initial greeting
        await task.queue_frames([TextFrame("Hello! How can I assist you today?")])
    
    @transport.event_handler("on_participant_left")
    async def on_participant_left(transport, participant, reason):
        await task.cancel()
    
    # 7. Run pipeline
    runner = PipelineRunner()
    await runner.run(task)

if __name__ == "__main__":
    asyncio.run(main())
```

### Bot Runner (HTTP Server)

```python
# bot_runner.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import subprocess
import os

app = FastAPI()

@app.post("/start_bot")
async def start_bot(request: Request):
    """Spawn a new bot instance"""
    data = await request.json()
    room_url = data.get("room_url")
    token = data.get("token")
    
    # Spawn bot as subprocess
    subprocess.Popen([
        "python", "bot.py",
        "--room_url", room_url,
        "--token", token,
    ], env=os.environ.copy())
    
    return JSONResponse({"status": "bot_started"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Environment Configuration

```bash
# .env - NEVER commit to git!
DAILY_API_KEY=your_daily_api_key
DAILY_ROOM_URL=https://your-domain.daily.co/room-name
OPENAI_API_KEY=sk-...
RIVA_URL=grpc.nvcf.nvidia.com:443
NVIDIA_API_KEY=nvapi-...
```

### Running Locally

```bash
# 1. Create Daily room
curl -X POST https://api.daily.co/v1/rooms \
  -H "Authorization: Bearer $DAILY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":"test-room"}'

# 2. Generate token
curl -X POST https://api.daily.co/v1/meeting-tokens \
  -H "Authorization: Bearer $DAILY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "properties": {
      "room_name": "test-room",
      "is_owner": true
    }
  }'

# 3. Set env vars and run
export DAILY_ROOM_URL=https://your-domain.daily.co/test-room
export DAILY_TOKEN=your-token
uv run bot.py

# 4. Open browser and join room
# https://your-domain.daily.co/test-room
```

---

## Production Deployment (2026 Best Practices)

### Option A: Pipecat Cloud (RECOMMENDED - GA Jan 2026)

**Why Choose Pipecat Cloud**:
- ✅ **Generally Available**: Production-ready since January 2026
- ✅ **Purpose-Built**: Designed specifically for voice AI deployments
- ✅ **Multi-Region**: Deploy globally for low latency
- ✅ **Auto-Scaling**: Elastic capacity with reserved instances
- ✅ **Ultra-Low Latency**: Optimized for <800ms voice-to-voice
- ✅ **Daily WebRTC Included**: At no additional cost
- ✅ **Vendor-Neutral**: Same code runs anywhere
- ✅ **HIPAA Roadmap**: Compliance enablement planned

**Deployment Steps**:

1. **Install Pipecat Cloud CLI**:

```bash
uv tool install pipecatcloud

# Authenticate
pcc auth login
```

2. **Initialize Project**:

```bash
pcc init

# Creates:
# - bot.py (your bot)
# - Dockerfile
# - pcc-deploy.toml
```

3. **Configure Deployment** (`pcc-deploy.toml`):

```toml
agent_name = "bpo-customer-service"
image = "your-dockerhub/bpo-agent:latest"

# Scaling
min_replicas = 5       # Always warm
max_replicas = 100     # Auto-scale limit

# Resources per agent
cpu = 2
memory = "4Gi"

# Regions for global presence
regions = ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]

# Environment (secrets set separately)
[env]
  OPENAI_MODEL = "gpt-4o-mini"
  RIVA_MODEL = "parakeet-ctc-1.1b-asr"
```

4. **Set Secrets** (encrypted, never in code):

```bash
pcc secrets set bpo-customer-service \
  --file .env

# Or individually:
pcc secrets set bpo-customer-service \
  OPENAI_API_KEY=sk-... \
  NVIDIA_API_KEY=nvapi-... \
  DAILY_API_KEY=...
```

5. **Build and Deploy**:

```bash
# Build Docker image
docker build -t your-dockerhub/bpo-agent:latest .
docker push your-dockerhub/bpo-agent:latest

# Deploy
pcc deploy

# Output:
# ✓ Building container...
# ✓ Running security scan...
# ✓ Deploying to us-east-1, us-west-2, eu-west-1, ap-southeast-1
# ✓ Agent available at: https://agents.pipecat.ai/bpo-customer-service
```

6. **Connect Client**:

```javascript
// Client JavaScript
import { Daily } from '@daily-co/daily-js';

const call = Daily.createCallObject();
await call.join({
  url: 'https://your-domain.daily.co/room-name',
  // Pipecat agent auto-joins via dispatch rule
});
```

**Scaling Behavior**:

```
Traffic Pattern          Pipecat Cloud Response
─────────────────────────────────────────────────
Normal (50 concurrent)   5 reserved instances
                         10% average load

Spike (+200 concurrent)  Auto-scale to 25 instances
                         <30 seconds to full capacity

Burst (+500 concurrent)  Scale to max 100 instances
                         Queue excess with retry logic

Business Hours          Pre-warmed capacity at 8 AM
                         Scale down at 6 PM (save 60%)
```

### Option B: Self-Hosted Docker/Kubernetes

**When to Choose Self-Hosting**:
- Maximum customization requirements
- Specific compliance not yet in Pipecat Cloud
- Existing Kubernetes infrastructure
- Cost optimization at massive scale

**Architecture**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    KUBERNETES CLUSTER (Self-Hosted)                          │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                     Bot Runner Service                               │  │
│  │  (HTTP API for spawning bot instances)                               │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                         │
│                                    │ Spawns                                   │
│                                    ▼                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                     Bot Worker Pool (HPA)                            │  │
│  │                                                                       │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                   │  │
│  │  │  Bot Pod 1  │  │  Bot Pod 2  │  │  Bot Pod N  │                   │  │
│  │  │ (Pipecat)   │  │ (Pipecat)   │  │ (Pipecat)   │                   │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                   │  │
│  │                                                                       │  │
│  │  Resources per pod: 2 CPU, 4GB RAM                                    │  │
│  │  Capacity: ~10 concurrent calls per pod                               │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Dockerfile** (2026 Best Practice):

```dockerfile
# Use UV for faster builds
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

# Install dependencies first (cache layer)
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

# Download models during build (not at runtime)
RUN python -c "from silero import VAD; VAD.load()"

# Copy application code
COPY bot.py bot_runner.py ./
COPY prompts/ ./prompts/

# Non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Pre-warm and run
CMD ["python", "bot_runner.py"]
```

**Kubernetes Deployment**:

```yaml
# bot-runner-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bot-runner
spec:
  replicas: 2
  selector:
    matchLabels:
      app: bot-runner
  template:
    metadata:
      labels:
        app: bot-runner
    spec:
      containers:
      - name: bot-runner
        image: your-registry/bpo-agent:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: openai-key
```

```yaml
# bot-worker-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bot-workers
spec:
  replicas: 5
  selector:
    matchLabels:
      app: bot-worker
  template:
    metadata:
      labels:
        app: bot-worker
    spec:
      containers:
      - name: bot
        image: your-registry/bpo-agent:latest
        command: ["python", "bot.py"]
        resources:
          requests:
            cpu: 2
            memory: 4Gi
          limits:
            cpu: 4
            memory: 8Gi
```

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: bot-workers-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: bot-workers
  minReplicas: 5
  maxReplicas: 100
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## AI Service Integration (2026 Best Practices)

### Speech-to-Text (STT)

**2026 Recommendation**: NVIDIA Riva Parakeet for lowest latency

```python
from pipecat.services.riva import RivaSTTService

# Cloud endpoint (fastest to start)
stt = RivaSTTService(
    url="grpc.nvcf.nvidia.com:443",
    model="parakeet-ctc-1.1b-asr",
    language="en-US",
)

# Alternative: Deepgram (excellent accuracy)
from pipecat.services.deepgram import DeepgramSTTService

stt = DeepgramSTTService(
    api_key=os.getenv("DEEPGRAM_API_KEY"),
    model="nova-3",  # Latest 2026 model
    language="en-US",
)
```

### Large Language Model (LLM)

**2026 Recommendations by Use Case**:
- **Cost-Optimized**: GPT-4o-mini (fast, cheap, good quality)
- **High Quality**: Claude 3.5 Sonnet (best reasoning)
- **Self-Hosted**: Llama 3.3 70B (data sovereignty)

```python
from pipecat.services.openai import OpenAILLMService
from pipecat.services.anthropic import AnthropicLLMService

# Option 1: OpenAI (recommended for most BPO)
llm = OpenAILLMService(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o-mini",
    temperature=0.7,
    max_tokens=150,  # Keep responses concise for voice
)

# Option 2: Anthropic (complex reasoning)
llm = AnthropicLLMService(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    model="claude-3-5-sonnet-20241022",
)
```

### Text-to-Speech (TTS)

**2026 Recommendation**: NVIDIA Riva FastPitch-HiFiGAN for natural voices

```python
from pipecat.services.riva import RivaTTSService
from pipecat.services.cartesia import CartesiaTTSService

# Option 1: NVIDIA Riva (included with Pipecat Cloud)
tts = RivaTTSService(
    url="grpc.nvcf.nvidia.com:443",
    model="fastpitch-hifigan",
    voice_id="English-US.Female-1",
)

# Option 2: Cartesia (highly natural)
tts = CartesiaTTSService(
    api_key=os.getenv("CARTESIA_API_KEY"),
    voice_id="71a7ad14-091c-4e8e-a314-022ece01c121",
    model="sonic-3",
)
```

### Voice Activity Detection (VAD)

**2026 Best Practice**: Always use Silero VAD

```python
from pipecat.audio.vad.silero import SileroVADAnalyzer

vad = SileroVADAnalyzer(
    start_duration_secs=0.3,  # Speech start sensitivity
    stop_duration_secs=0.8,   # Speech end sensitivity
)
```

---

## Advanced Features for BPO

### Turn Detection

Enable natural conversation pauses:

```python
from pipecat.processors.turn_detection import TurnDetection

turn_detection = TurnDetection(
    model="multilingual",  # Custom ML model
    min_silence_ms=500,    # Wait 500ms before responding
)

pipeline = Pipeline([
    transport.input(),
    vad,
    turn_detection,  # Add to pipeline
    stt,
    # ... rest
])
```

### Interruption Handling

Allow users to barge in:

```python
task = PipelineTask(
    pipeline,
    params=PipelineParams(
        allow_interruptions=True,  # Enable barge-in
        interruption_duration_secs=0.5,  # Min interruption length
    ),
)
```

### Tool Calling (Function Execution)

Integrate with CRM, booking systems:

```python
from pipecat.services.openai import OpenAILLMService
from pipecat.frames.frames import FunctionCallInProgressFrame, FunctionCallResultFrame

# Define tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "lookup_customer",
            "description": "Look up customer by phone number",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone": {"type": "string"},
                },
                "required": ["phone"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_appointment",
            "description": "Book an appointment",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string"},
                    "time": {"type": "string"},
                    "service": {"type": "string"},
                },
                "required": ["date", "time", "service"],
            },
        },
    },
]

llm = OpenAILLMService(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o-mini",
    tools=tools,
)

# Handle function calls
@llm.on("function_call")
async def on_function_call(function_name, arguments):
    if function_name == "lookup_customer":
        phone = arguments["phone"]
        customer = await crm.lookup(phone)
        return FunctionCallResultFrame(
            function_name=function_name,
            result=customer,
        )
    elif function_name == "book_appointment":
        # ... handle booking
        pass
```

### Pipecat Flows (State Machines)

For complex multi-step conversations:

```python
from pipecat_flows import FlowManager, FlowConfig

# Define conversation flow
flow_config = FlowConfig(
    initial_node="greeting",
    nodes={
        "greeting": {
            "messages": [{"role": "system", "content": "Greet the customer"}],
            "transitions": {
                "issue_identified": "troubleshoot",
                "booking_requested": "booking",
            },
        },
        "troubleshoot": {
            "messages": [{"role": "system", "content": "Help troubleshoot"}],
            "transitions": {
                "resolved": "closing",
                "escalate": "human_handoff",
            },
        },
        "booking": {
            "messages": [{"role": "system", "content": "Book appointment"}],
            "functions": ["check_availability", "book_appointment"],
            "transitions": {
                "booked": "closing",
            },
        },
    },
)

flow_manager = FlowManager(llm=llm, config=flow_config)
```

---

## NVIDIA Integration (nvidia-pipecat)

For optimized NVIDIA RIVA performance:

```bash
pip install nvidia-pipecat
```

### Speculative Speech Processing (2026 Optimization)

Reduces latency by 200ms by processing ASR interim transcripts:

```python
from nvidia_pipecat.processors import SpeculativeSpeechProcessor

# Add to pipeline after STT
speculative = SpeculativeSpeechProcessor()

pipeline = Pipeline([
    transport.input(),
    stt,
    speculative,  # Process interim transcripts early
    llm,
    tts,
    transport.output(),
])
```

### Audio2Face (Avatar Agents)

For video avatars with lip sync:

```python
from nvidia_pipecat.services import Audio2FaceService

a2f = Audio2FaceService(
    url="localhost:50051",
    model="mark_us",
)

# Pipeline outputs to Audio2Face for avatar rendering
```

---

## Observability and Monitoring

### Built-in Metrics

```python
task = PipelineTask(
    pipeline,
    params=PipelineParams(
        enable_metrics=True,       # Pipeline latency
        enable_usage_metrics=True,  # Token usage
    ),
)

# Access metrics
@task.on("metrics")
async def on_metrics(metrics):
    print(f"TTFB: {metrics.ttfb}ms")
    print(f"STT Latency: {metrics.stt_latency}ms")
    print(f"LLM Tokens: {metrics.llm_tokens}")
```

### OpenTelemetry Integration

```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Configure tracer
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

exporter = OTLPSpanExporter(endpoint="https://your-collector")
span_processor = BatchSpanProcessor(exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Create spans
with tracer.start_as_current_span("customer_interaction") as span:
    span.set_attribute("customer.id", customer_id)
    span.set_attribute("agent.id", agent_id)
    # ... pipeline execution
```

### Logging Best Practices

```python
import logging
import structlog

# Structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()

# Log with context
logger.info(
    "customer_call_started",
    customer_id=customer_id,
    room_name=room_name,
    agent_version="1.2.3",
)
```

---

## Performance Optimization

### Latency Budget

| Component | Target | Optimization |
|-----------|--------|--------------|
| Transport | <100ms | WebRTC edge deployment |
| VAD | <50ms | Silero on-device |
| STT (RIVA) | <200ms | GPU acceleration |
| LLM | <300ms | Streaming, GPT-4o-mini |
| TTS (RIVA) | <150ms | Caching, FastPitch |
| **Total** | **<800ms** | **Natural conversation** |

### Optimization Techniques

1. **Model Pre-warming**:
```python
async def prewarm():
    # Load before accepting calls
    await stt.warmup()
    await llm.generate("Hello", max_tokens=1)
    await tts.synthesize("Hello")
```

2. **Connection Pooling**:
```python
# Reuse HTTP connections to AI providers
import aiohttp

session = aiohttp.ClientSession(
    connector=aiohttp.TCPConnector(limit=100),
)
```

3. **Audio Caching**:
```python
# Cache common TTS responses
from functools import lru_cache

@lru_cache(maxsize=1000)
async def get_greeting_audio(name):
    return await tts.synthesize(f"Hello {name}, how can I help?")
```

---

## Deployment Checklist

### Pre-Production

- [ ] Load testing: 2x expected traffic
- [ ] Latency profiling: <800ms target
- [ ] Security: Secrets in Pipecat Cloud, not code
- [ ] PII redaction configured
- [ ] Monitoring: OpenTelemetry, Prometheus
- [ ] Alerting: PagerDuty/Slack integration
- [ ] Rollback plan tested
- [ ] Documentation updated

### Go-Live

- [ ] Canary deployment: 10% traffic
- [ ] Monitor error rates (<0.1%)
- [ ] Gradual ramp to 100%
- [ ] On-call engineer assigned
- [ ] Post-launch review scheduled

---

## Conclusion

Pipecat provides the **AI orchestration layer** for BPO voice agents with:

1. **Frame-based architecture**: Elegant, composable, testable
2. **Vendor neutrality**: 40+ providers, no lock-in
3. **Pipecat Cloud GA**: Production-ready managed platform
4. **Ultra-low latency**: <800ms voice-to-voice
5. **BPO-ready features**: Tool calling, flows, interruptions

**Next Steps**:
- Review `livekit.md` for transport layer
- Review `nvidia-riva.md` for speech AI
- Start with Pipecat Cloud quickstart

---

## References

- Pipecat Documentation: https://docs.pipecat.ai
- Pipecat Cloud: https://pipecat.cloud
- GitHub: https://github.com/pipecat-ai/pipecat
- NVIDIA Pipecat: https://github.com/nvidia/voice-agent-examples
- Community: https://discord.gg/pipecat
