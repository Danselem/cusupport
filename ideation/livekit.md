# LiveKit Architecture Guide (2026)

> **Role**: Real-time media transport and infrastructure layer  
> **Best Practice**: LiveKit Cloud (managed) for rapid deployment, Kubernetes self-hosting for compliance  
> **Last Updated**: February 2026

---

## Executive Summary

LiveKit is the gold-standard open-source WebRTC platform that powers real-time audio, video, and data streaming. Notably, **OpenAI chose LiveKit for ChatGPT's Advanced Voice Mode**—validating its production readiness at massive scale.

For BPO customer service agents in 2026, LiveKit serves as the **infrastructure layer** handling:
- WebRTC media transport (lowest latency protocol)
- Room and participant management
- Media routing via SFU (Selective Forwarding Unit)
- SIP/Telephony integration for phone calls
- Signaling and TURN servers for NAT traversal

**Key Decision**: Use **LiveKit Cloud** for rapid market entry ($0.01/minute, auto-scaling, global edge network). Choose **self-hosted Kubernetes** only for strict data sovereignty or compliance requirements.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              LIVEKIT CLOUD                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         SFU CLUSTER                                  │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │    │
│  │  │   Server 1   │  │   Server 2   │  │   Server N   │               │    │
│  │  │  (Region US) │  │  (Region EU) │  │  (Region AP) │               │    │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘               │    │
│  └─────────┼─────────────────┼─────────────────┼───────────────────────┘    │
│            │                 │                 │                            │
│  ┌─────────▼─────────────────▼─────────────────▼───────────────────────┐    │
│  │                     SIGNALING & TURN                                │    │
│  │           WebSocket signaling + TURN relay servers                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ WebRTC
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AGENT WORKERS                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Worker Pool (Kubernetes / LiveKit Cloud)                          │    │
│  │                                                                      │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │    │
│  │  │   Worker 1  │  │   Worker 2  │  │   Worker N  │                  │    │
│  │  │  ┌───────┐  │  │  ┌───────┐  │  │  ┌───────┐  │                  │    │
│  │  │  │ Agent │  │  │  │ Agent │  │  │  │ Agent │  │                  │    │
│  │  │  │Session│  │  │  │Session│  │  │  │Session│  │                  │    │
│  │  │  └───┬───┘  │  │  └───┬───┘  │  │  └───┬───┘  │                  │    │
│  │  └──────┼──────┘  └──────┼──────┘  └──────┼──────┘                  │    │
│  └─────────┼────────────────┼────────────────┼──────────────────────────┘    │
└────────────┼────────────────┼────────────────┼───────────────────────────────┘
             │                │                │
             └────────────────┴────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CLIENTS (BPO USERS)                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Web App    │  │  Mobile App  │  │  SIP Phone   │  │   PSTN       │     │
│  │  (Browser)   │  │  (iOS/Andr)  │  │   (VoIP)     │  │  (Landline)  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Components (2026 Best Practices)

### 1. Workers: Process-Level Orchestration

Workers are processes that connect to LiveKit and wait for job assignments. Each worker can handle multiple concurrent sessions.

**Key Features**:
- **Load Reporting**: Workers report load (0.0 to 1.0) for intelligent job distribution
- **Horizontal Scaling**: Add more worker pods as call volume increases
- **Fault Tolerance**: If a worker fails, jobs automatically restart on healthy workers

```python
from livekit.agents import cli, WorkerOptions

async def entrypoint(ctx: JobContext):
    # Agent logic here
    pass

def calculate_load() -> float:
    """Return 0.0 (idle) to 1.0 (at capacity)"""
    active_sessions = get_active_sessions()
    max_sessions = 10  # Adjust based on your hardware
    return active_sessions / max_sessions

if __name__ == "__main__":
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        load_fnc=calculate_load,  # Enable load-aware routing
    ))
```

### 2. Jobs: Isolated Task Execution

Each voice session is a discrete job dispatched to a worker. Jobs are:
- **Long-lived**: Sessions last minutes to hours
- **Stateful**: Conversation context persists throughout
- **Isolated**: One job failure doesn't affect others

### 3. Agent Sessions: Stateful Conversation Management

The `AgentSession` (or `VoiceAgent`) encapsulates:
- **STT→LLM→TTS Pipeline**: Real-time AI orchestration
- **Turn Detection**: ML-powered phrase endpointing
- **Interruption Handling**: Graceful mid-sentence stops
- **Context Management**: Conversation memory

```python
from livekit.agents import VoiceAgent, AgentSession
from livekit.plugins import deepgram, openai, cartesia

agent = VoiceAgent(
    stt=deepgram.STT(model="nova-3"),      # Speech-to-Text
    llm=openai.LLM(model="gpt-4o-mini"),   # Language Model
    tts=cartesia.TTS(voice="sonic-3"),     # Text-to-Speech
    # 2026 Best Practice: Use native turn detection
    turn_detection=Multilingual(),          # Custom ML model
)

session = AgentSession(agent=agent)
```

### 4. Rooms: Virtual Meeting Spaces

- **Participants**: Users and agents join as participants
- **Tracks**: Audio/video/data streams published and subscribed
- **Permissions**: Granular access control per participant

### 5. WebRTC Transport

**Why WebRTC for 2026 Production**:
- **Low Latency**: <100ms end-to-end (vs 300ms+ for WebSocket)
- **Adaptive Bitrate**: Adjusts to network conditions
- **Packet Loss Recovery**: Forward Error Correction (FEC)
- **Firewall Traversal**: TURN servers for restrictive networks

---

## Local Development Workflow

### Prerequisites

```bash
# Python 3.10+
pip install livekit-agents

# LiveKit CLI for local server and deployment
npm install -g @livekit/livekit-cli
# OR
brew install livekit-cli
```

### Option A: LiveKit Cloud (Recommended)

**Fastest path to local development**:

1. **Sign up**: https://cloud.livekit.io
2. **Create project**: Get API credentials
3. **Set environment variables**:

```bash
export LIVEKIT_URL=wss://your-project.livekit.cloud
export LIVEKIT_API_KEY=your_api_key
export LIVEKIT_API_SECRET=your_api_secret
```

4. **Run agent**:

```python
# agent.py
import asyncio
from livekit.agents import cli, JobContext, WorkerOptions
from livekit.plugins import deepgram, openai, cartesia

async def entrypoint(ctx: JobContext):
    await ctx.connect()
    
    agent = VoiceAgent(
        stt=deepgram.STT(model="nova-3"),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=cartesia.TTS(),
    )
    
    await agent.start(room=ctx.room)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
```

```bash
python agent.py start
```

### Option B: Local LiveKit Server (Docker)

For offline development or CI/CD testing:

```bash
# Run local LiveKit server
docker run -p 7880:7880 \
  -e LIVEKIT_KEYS="devkey: secret" \
  livekit/livekit-server \
  --dev --bind 0.0.0.0

# Server available at: ws://localhost:7880
# API Key: devkey
# API Secret: secret
```

### Testing Your Agent

```bash
# Create a test room and join with browser
lk room join --url ws://localhost:7880 \
  --api-key devkey --api-secret secret \
  --room test-room --identity agent-test
```

---

## Production Deployment (2026 Best Practices)

### Option A: LiveKit Cloud (RECOMMENDED)

**Why Choose LiveKit Cloud**:
- ✅ **10 Years Experience**: Daily.co's global real-time infrastructure
- ✅ **Auto-scaling**: Elastic capacity for traffic spikes
- ✅ **Stateful Load Balancing**: Sessions stay on same server
- ✅ **Edge Network**: Global presence for low latency
- ✅ **Built-in Observability**: Logs, metrics, traces
- ✅ **Simple Pricing**: $0.01/minute per active session
- ✅ **Zero Infrastructure**: No servers to manage

**Deployment Steps**:

1. **Configure deployment**:

```bash
# Initialize agent project
lk agent create my-bpo-agent

# This creates:
# - agent.py (your bot code)
# - Dockerfile (container definition)
# - lk-deploy.yaml (deployment config)
```

2. **Set secrets** (never commit to git):

```bash
lk agent secrets set my-bpo-agent \
  OPENAI_API_KEY=sk-... \
  DEEPGRAM_API_KEY=... \
  CARTESIA_API_KEY=...
```

3. **Deploy**:

```bash
lk agent deploy

# Output:
# ✓ Building container...
# ✓ Pushing to registry...
# ✓ Deploying to LiveKit Cloud...
# ✓ Agent available at: https://agents.livekit.io/my-bpo-agent
```

4. **Scale configuration**:

```yaml
# lk-deploy.yaml
agent_name: my-bpo-agent
replicas: 3  # Minimum instances (warm pool)
max_replicas: 50  # Auto-scale up to this
resources:
  cpu: 2
  memory: 4Gi
```

**Cost Calculation** (BPO Example):
- 100 concurrent agents × 8 hours/day × 22 business days
- = 100 × 8 × 60 × 22 = 1,056,000 minutes/month
- **Cost**: 1,056,000 × $0.01 = **$10,560/month** (LiveKit Cloud)
- **Plus**: STT/LLM/TTS provider costs (varies by usage)

### Option B: Self-Hosted Kubernetes

**When to Choose Self-Hosting**:
- Strict data residency requirements (GDPR, HIPAA)
- Existing Kubernetes expertise
- Cost optimization at massive scale (>10,000 concurrent)
- Custom network policies

**Architecture**:

```
┌─────────────────────────────────────────────────────────────┐
│                    KUBERNETES CLUSTER                        │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              LiveKit Server (SFU)                      │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │  │
│  │  │  Server 1   │  │  Server 2   │  │  Server N   │    │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘    │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Agent Workers (HPA)                       │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │  │
│  │  │  Worker 1   │  │  Worker 2   │  │  Worker N   │    │  │
│  │  │  (Agent)    │  │  (Agent)    │  │  (Agent)    │    │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘    │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Supporting Services                       │  │
│  │  - Redis (session state)                               │  │
│  │  - Prometheus (metrics)                                │  │
│  │  - Grafana (dashboards)                                │  │
│  │  - TURN servers (coturn)                               │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Deployment**:

```yaml
# livekit-server-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: livekit-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: livekit-server
  template:
    metadata:
      labels:
        app: livekit-server
    spec:
      containers:
      - name: livekit-server
        image: livekit/livekit-server:latest
        ports:
        - containerPort: 7880
        - containerPort: 7881
        env:
        - name: LIVEKIT_KEYS
          valueFrom:
            secretKeyRef:
              name: livekit-secrets
              key: keys
        - name: LIVEKIT_REDIS_ADDRESS
          value: "redis:6379"
```

```yaml
# agent-worker-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-workers
spec:
  replicas: 5
  selector:
    matchLabels:
      app: agent-worker
  template:
    metadata:
      labels:
        app: agent-worker
    spec:
      containers:
      - name: agent
        image: your-registry/bpo-agent:latest
        env:
        - name: LIVEKIT_URL
          value: "wss://your-livekit-server"
        - name: LIVEKIT_API_KEY
          valueFrom:
            secretKeyRef:
              name: livekit-secrets
              key: api-key
```

```yaml
# hpa.yaml - Horizontal Pod Autoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: agent-workers-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: agent-workers
  minReplicas: 5
  maxReplicas: 100
  metrics:
  - type: Pods
    pods:
      metric:
        name: agent_load
      target:
        type: AverageValue
        averageValue: "0.7"
```

---

## Integration with Pipecat and RIVA

### LiveKit + Pipecat Architecture

LiveKit provides the **transport layer**, Pipecat provides the **AI orchestration**:

```
Client (Browser/Phone)
         │
         │ WebRTC
         ▼
┌─────────────────────┐
│   LiveKit Cloud     │  ← Rooms, Participants, Media Routing
│   (Transport)       │
└──────────┬──────────┘
           │ Audio Frames
           ▼
┌─────────────────────┐
│     Pipecat         │  ← VAD → STT → LLM → TTS Pipeline
│   (Orchestration)   │
└──────────┬──────────┘
           │ API Calls
           ▼
┌─────────────────────┐
│    NVIDIA RIVA      │  ← ASR (Parakeet), TTS (FastPitch)
│    (Speech AI)      │
└─────────────────────┘
```

**Code Example**:

```python
# Pipecat agent connecting to LiveKit
from pipecat.pipeline.pipeline import Pipeline
from pipecat.transports.services.livekit import LiveKitTransport
from pipecat.services.riva import RivaSTTService, RivaTTSService
from pipecat.services.openai import OpenAILLMService

async def main():
    # LiveKit transport handles WebRTC
    transport = LiveKitTransport(
        room_url="wss://...",
        token="...",
    )
    
    # Pipecat pipeline with RIVA services
    stt = RivaSTTService(url="grpc.nvcf.nvidia.com:443")
    llm = OpenAILLMService(api_key="...")
    tts = RivaTTSService(url="grpc.nvcf.nvidia.com:443")
    
    pipeline = Pipeline([
        transport.input(),    # LiveKit audio in
        stt,                  # RIVA ASR
        llm,                  # OpenAI
        tts,                  # RIVA TTS
        transport.output(),   # LiveKit audio out
    ])
```

---

## Telephony Integration (BPO Critical)

For phone-based customer service:

### SIP Trunk Integration

```python
from livekit.plugins import sip

# Create SIP participant
sip_trunk = sip.SIPTrunk(
    outbound_address="sip.provider.com",
    outbound_username="user",
    outbound_password="pass",
)

# Dial phone number
await ctx.room.sip.dial(
    sip_trunk=sip_trunk,
    to_uri="sip:+1234567890@sip.provider.com",
)
```

### PSTN via Twilio

```python
# LiveKit Cloud provides built-in PSTN
# Or integrate with Twilio for BYOC (Bring Your Own Carrier)

from livekit.plugins import twilio

twilio_client = twilio.TwilioClient(
    account_sid="...",
    auth_token="...",
)

# Incoming calls routed to LiveKit rooms
@app.post("/twilio/webhook")
async def handle_call(request: Request):
    room_name = generate_room_name()
    token = create_agent_token(room_name)
    
    return twilio_client.create_twiml(
        connect_url=f"wss://your-project.livekit.cloud?token={token}"
    )
```

---

## Security Best Practices (2026)

### 1. Secrets Management

**NEVER** commit API keys to git. Use LiveKit Cloud secrets:

```bash
# Set secrets via CLI
lk agent secrets set my-bpo-agent \
  OPENAI_API_KEY=sk-... \
  DEEPGRAM_API_KEY=... \
  DB_PASSWORD=...

# Access in code via environment variables
import os
api_key = os.getenv("OPENAI_API_KEY")
```

### 2. End-to-End Encryption

```python
# Enable E2EE for sensitive conversations
from livekit import e2ee

key_provider = e2ee.KeyProvider(
    shared_key=b"your-32-byte-key-here..."
)

room = rtc.Room(e2ee_options=e2ee.E2EEOptions(key_provider))
```

### 3. PII Redaction

```python
from livekit.plugins import redaction

# Automatically redact PII from logs and transcripts
redaction.enable(
    patterns=[
        redaction.PIIType.SSN,
        redaction.PIIType.CREDIT_CARD,
        redaction.PIIType.PHONE_NUMBER,
    ]
)
```

### 4. Access Control

```python
# Granular room permissions
from livekit import AccessToken, VideoGrant

token = AccessToken(api_key, api_secret) \
    .with_identity("agent-1") \
    .with_name("Customer Service Agent") \
    .with_grants(VideoGrant(
        room_join=True,
        room="support-room-123",
        can_publish=True,
        can_subscribe=True,
        can_publish_data=True,
        # BPO-specific: Record for quality assurance
        can_record=True,
    ))
```

---

## Observability and Monitoring

### LiveKit Cloud Dashboard

Built-in observability includes:
- **Session Analytics**: Active calls, duration, drop rates
- **Error Tracking**: Exception rates and stack traces
- **Quality Metrics**: Latency, packet loss, jitter
- **Build Logs**: Container build status
- **Realtime Metrics**: Live session monitoring

### OpenTelemetry Integration

```python
from livekit.agents import otel

# Configure tracing
otel.init_tracing(
    service_name="bpo-agent",
    exporter=otel.OTLPExporter(
        endpoint="https://your-otel-collector",
    ),
)

# Custom spans
with otel.start_span("process_customer_intent") as span:
    span.set_attribute("customer.id", customer_id)
    span.set_attribute("intent", detected_intent)
    result = await process_intent(customer_input)
    span.set_attribute("result", result)
```

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram

# Define metrics
session_duration = Histogram(
    'agent_session_duration_seconds',
    'Duration of agent sessions'
)

transcription_latency = Histogram(
    'stt_latency_seconds',
    'Speech-to-text latency'
)

# Record metrics
with session_duration.time():
    await run_session()

transcription_latency.observe(stt_latency)
```

---

## Performance Optimization

### Latency Budget (2026 Target: <800ms)

| Component | Target Latency | Optimization |
|-----------|---------------|--------------|
| Network (WebRTC) | <100ms | Edge deployment, TURN optimization |
| VAD | <50ms | Silero VAD (on-device) |
| STT (RIVA) | <200ms | Parakeet CTC, GPU acceleration |
| LLM | <300ms | GPT-4o-mini, streaming responses |
| TTS (RIVA) | <150ms | FastPitch-HiFiGAN, caching |
| **Total** | **<800ms** | **Natural conversation feel** |

### Optimization Techniques

1. **Edge Deployment**: Deploy agents close to users (regional LiveKit Cloud)
2. **Model Pre-warming**: Load models before first request
3. **Connection Reuse**: Persistent connections to AI providers
4. **Audio Codec**: Opus for best quality/bandwidth ratio
5. **Adaptive Bitrate**: Let WebRTC handle network fluctuations

---

## Scaling Strategies

### BPO Contact Center Scaling Example

**Scenario**: Handle 1,000 concurrent customer calls

```yaml
# lk-deploy.yaml for LiveKit Cloud
agent_name: bpo-customer-service

# Base capacity (always warm)
replicas: 20  # 20 agents ready instantly

# Auto-scaling
max_replicas: 200
metrics:
  - type: load
    target_average_value: 0.7  # Scale when 70% loaded

# Resources per agent
resources:
  cpu: 2
  memory: 4Gi

# Regional deployment
regions:
  - us-east-1
  - us-west-2
  - eu-west-1
  - ap-southeast-1
```

**Scaling Behavior**:
1. **Normal Load** (500 calls): 50 agents running, 50% capacity
2. **Traffic Spike** (1,000 calls): Auto-scale to 100 agents in <30 seconds
3. **Burst** (2,000 calls): Scale to max 200 agents, queue excess

### Cost Optimization

- **Reserved Instances**: Pre-warm agents during business hours
- **Scheduled Scaling**: Scale up at 8 AM, down at 6 PM
- **Spot Instances**: Use for non-critical workloads (save 70%)

---

## Deployment Checklist

### Pre-Production

- [ ] Load testing with 2x expected traffic
- [ ] Latency profiling (<800ms target)
- [ ] Security audit (secrets, encryption)
- [ ] PII redaction rules configured
- [ ] Monitoring dashboards created
- [ ] Alerting rules set up (PagerDuty/Slack)
- [ ] Disaster recovery plan tested
- [ ] Rollback procedure documented

### Go-Live

- [ ] Start with 10% traffic (canary deployment)
- [ ] Monitor error rates and latency
- [ ] Gradual ramp to 100% over 1 week
- [ ] On-call engineer assigned
- [ ] Customer communication ready

---

## Common Pitfalls and Solutions

### 1. Cold Start Latency

**Problem**: First request takes 5-10 seconds

**Solution**:
```python
# Pre-warm models on worker startup
async def prewarm():
    # Load VAD model
    await silero.VAD.load()
    # Warm up STT connection
    await stt.warmup()
    # Warm up LLM
    await llm.generate("Hello", max_tokens=1)

cli.run_app(WorkerOptions(
    entrypoint_fnc=entrypoint,
    prewarm_fnc=prewarm,  # Called before accepting jobs
))
```

### 2. Memory Leaks in Long Sessions

**Problem**: Agent memory grows over hours-long calls

**Solution**:
```python
# Limit conversation context
from livekit.agents import llm

chat_context = llm.ChatContext()
chat_context.max_messages = 20  # Keep last 20 messages

# Periodic cleanup
async def cleanup_task():
    while True:
        await asyncio.sleep(300)  # Every 5 minutes
        gc.collect()  # Force garbage collection
```

### 3. Network Partitions

**Problem**: Agent loses connection to LiveKit

**Solution**:
```python
# Automatic reconnection is built-in
# Configure retry policy
cli.run_app(WorkerOptions(
    entrypoint_fnc=entrypoint,
    max_retry=5,
    retry_delay=5.0,  # Seconds between retries
))
```

---

## Conclusion

LiveKit provides the **rock-solid infrastructure foundation** for BPO voice agents. For 2026 deployments:

1. **Start with LiveKit Cloud** for fastest time-to-market
2. **Use WebRTC** for production (not WebSocket)
3. **Implement proper observability** from day one
4. **Plan for horizontal scaling** with stateless workers
5. **Prioritize security** with secrets management and encryption

**Next Steps**:
- Review `pipecat.md` for AI orchestration layer
- Review `nvidia-riva.md` for speech AI services
- See integration examples in architecture overview

---

## References

- LiveKit Documentation: https://docs.livekit.io
- LiveKit Agents: https://docs.livekit.io/agents
- LiveKit Cloud: https://cloud.livekit.io
- GitHub: https://github.com/livekit
- Community: https://livekit.io/slack
