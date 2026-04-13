"""Customer Service Conversational AI Agent using Pipecat."""

import json
import os
import uuid
from typing import Any

from dotenv import load_dotenv
from loguru import logger
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import LLMRunFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContext,
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport

from pipegen.history import get_conversation_history
from pipegen.observability import setup_observability
from pipegen.services import create_llm_service
from pipegen.tools import get_tool_registry

load_dotenv()


async def run_agent(transport: SmallWebRTCTransport) -> None:
    """Run the customer service agent with the given transport."""

    logger.info("Setting up customer service agent...")

    history = get_conversation_history()
    tool_registry = get_tool_registry()

    conversation_id = str(uuid.uuid4())
    logger.info(f"Conversation ID: {conversation_id}")

    context = LLMContext()
    llm = create_llm_service()

    tools = tool_registry.get_tools_list()
    if tools:
        context.add_message(
            {
                "role": "system",
                "content": f"You have access to the following tools:\n{json.dumps(tools, indent=2)}\n\nUse these tools when appropriate to help customers.",
            }
        )

    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(
            vad_analyzer=SileroVADAnalyzer(),
        ),
    )

    pipeline = Pipeline(
        [
            transport.input(),
            user_aggregator,
            llm,
            transport.output(),
            assistant_aggregator,
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
    )

    async def add_to_history(role: str, content: str, metadata: dict | None = None):
        """Add message to conversation history."""
        try:
            await history.add_message(conversation_id, role, content, metadata)
        except Exception as e:
            logger.warning(f"Failed to save message to history: {e}")

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport: SmallWebRTCTransport, client: dict[str, Any]) -> None:
        logger.info(f"Client connected: {client}")

        existing_history = await history.get_history(conversation_id)
        if existing_history:
            logger.info(f"Loaded {len(existing_history)} previous messages")

        welcome_message = (
            "Welcome! Thank you for contacting our customer service. How may I assist you today?"
        )
        context.add_message({"role": "system", "content": welcome_message})

        await add_to_history("assistant", welcome_message, {"event": "welcome"})
        await task.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(
        transport: SmallWebRTCTransport, client: dict[str, Any]
    ) -> None:
        logger.info(f"Client disconnected: {client}")
        await task.cancel()

    @transport.event_handler("on_client_error")
    async def on_client_error(
        transport: SmallWebRTCTransport, client: dict[str, Any], error: Exception
    ) -> None:
        logger.error(f"Client error: {error}")
        await task.cancel()

    runner = PipelineRunner(handle_sigint=False)

    logger.info("Starting customer service agent...")
    await runner.run(task)


async def main(runner_args: Any) -> None:
    """Main entry point for the agent."""

    setup_observability(
        service_name="pipegen",
        otlp_endpoint=os.getenv("OTLP_ENDPOINT"),
        langfuse_public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        langfuse_secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        langfuse_host=os.getenv("LANGFUSE_HOST"),
    )

    transport = SmallWebRTCTransport(
        runner_args.webrtc_connection,
        params=None,
    )
    await run_agent(transport)


if __name__ == "__main__":
    from pipecat.runner.run import main as run_main

    run_main()
