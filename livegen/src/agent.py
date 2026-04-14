import asyncio
import json
import logging
import os
import time

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from livekit import agents  # noqa: E402
from livekit.agents import AgentServer, AgentSession, Agent  # noqa: E402
from livekit.plugins import google, silero  # noqa: E402

from src.models import CallMetrics, CallEndReason  # noqa: E402
from src.prompts import SYSTEM_PROMPT, GREETING, SalesPrompts, RetentionPrompts  # noqa: E402


async def save_metrics(metrics: CallMetrics):
    try:
        os.makedirs("metrics_data", exist_ok=True)
        filename = f"metrics_data/{metrics.session_id}_{int(metrics.call_start)}.json"

        data = {
            "session_id": str(metrics.session_id),
            "call_start": float(metrics.call_start),
            "call_end": float(metrics.call_end),
            "duration": float(metrics.call_end - metrics.call_start),
            "total_turns": int(metrics.total_turns),
            "interruptions": int(metrics.interruptions),
            "error_count": int(metrics.error_count),
            "collected_info": metrics.collected_info.model_dump(),
            "service_type": metrics.service_type,
            "success": bool(metrics.success),
            "end_reason": str(metrics.end_reason),
        }
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved metrics for session {metrics.session_id}")
    except Exception as e:
        logger.error(f"Failed to save metrics: {e}")


async def handle_error(error: Exception, metrics: CallMetrics) -> CallMetrics:
    error_msg = str(error)
    logger.error(f"Error in session: {error_msg}")
    metrics.error_count += 1

    if metrics.error_count >= 3:
        logger.error("Max errors reached, ending session")
        metrics.end_reason = CallEndReason.ERROR.value
        metrics.success = False
    else:
        logger.warning(f"Error {metrics.error_count}/3, continuing...")

    return metrics


class BPOServiceAgent(Agent):
    """BPO Service Agent - Handles customer support, sales, and retention."""

    def __init__(self, room_sid: str = "console", service_type: str = "support"):
        self._room_sid = room_sid
        self._service_type = service_type

        if service_type == "sales":
            base_instructions = SYSTEM_PROMPT + "\n" + SalesPrompts.INSTRUCTIONS
            greeting = SalesPrompts.GREETING
        elif service_type == "retention":
            base_instructions = SYSTEM_PROMPT + "\n" + RetentionPrompts.INSTRUCTIONS
            greeting = RetentionPrompts.GREETING
        else:
            base_instructions = SYSTEM_PROMPT
            greeting = GREETING

        instructions = f"""## Opening Greeting (Required)
When the call starts, say exactly: "{greeting}"

{base_instructions}"""

        super().__init__(instructions=instructions)
        self._greeting = greeting


server = AgentServer()


@server.rtc_session(agent_name="customer-support")
async def bpo_entrypoint(ctx: agents.JobContext):
    """BPO Service entrypoint - routes to support/sales/retention based on room name."""
    room_name = ctx.room.name if ctx.room else "support"

    if "sales" in room_name.lower():
        service_type = "sales"
    elif "retention" in room_name.lower() or "loyalty" in room_name.lower():
        service_type = "retention"
    else:
        service_type = "support"

    room_sid = str(ctx.room.sid) if ctx.room else f"{service_type}-{int(time.time())}"
    call_start = time.time()

    logger.info(f"Starting {service_type} session: {room_sid}")

    agent = BPOServiceAgent(room_sid=room_sid, service_type=service_type)

    llm = None
    try:
        llm = google.realtime.RealtimeModel(
            model="gemini-2.5-flash-native-audio-preview-12-2025",
            voice="Vindemiatrix",
            instructions=agent.instructions,
            enable_affective_dialog=True,
        )
        logger.info(f"LLM initialized with model: {llm.model}")
    except Exception as e:
        logger.error(f"Failed to initialize LLM: {e}")
        return

    session = None
    try:
        session = AgentSession(llm=llm, vad=silero.VAD.load())
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        return

    metrics = CallMetrics(
        session_id=room_sid,
        call_start=call_start,
        service_type=service_type,
    )

    try:
        await session.start(room=ctx.room, agent=agent)
        logger.info("Session started successfully")

        greeting = agent._greeting
        logger.info(f"Calling generate_reply with greeting: {greeting}")

        await asyncio.sleep(0.5)
        await session.generate_reply(
            instructions=f"Greet the user by saying exactly: {greeting}"
        )
        logger.info("generate_reply completed")

        await asyncio.sleep(5)

        metrics.call_end = time.time()
        metrics.success = True
        metrics.end_reason = CallEndReason.COMPLETED.value
        logger.info(f"Session completed successfully: {room_sid}")

    except asyncio.TimeoutError:
        metrics.call_end = time.time()
        metrics.success = True
        metrics.end_reason = CallEndReason.TIMEOUT.value
        logger.warning(f"Session timed out: {room_sid}")

    except Exception as e:
        metrics = await handle_error(e, metrics)
        metrics.call_end = time.time()

    finally:
        await save_metrics(metrics)
        logger.info(
            f"Session ended. Success: {metrics.success}, Reason: {metrics.end_reason}"
        )


if __name__ == "__main__":
    agents.cli.run_app(server)
