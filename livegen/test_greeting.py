"""Test script to verify agent greeting.

Note: This is an integration test that requires a running LiveKit server.
Run with: pytest test_greeting.py -v
Or manually: python test_greeting.py
"""

import asyncio
import pytest
from livekit import rtc
from livekit.agents import AgentSession, Agent
from livekit.plugins import google
from livekit.plugins import silero
from livekit import api


@pytest.mark.integration
@pytest.mark.asyncio
async def test_greeting():
    """Test if agent can greet on session start."""
    # Create a token to join room
    grants = api.VideoGrants(
        room="test-greeting-room",
        room_join=True,
        can_publish=True,
        can_subscribe=True,
    )
    token = (
        api.AccessToken(api_key="dev", api_secret="secret")
        .with_identity("test-user")
        .with_grants(grants)
        .to_jwt()
    )

    # Create room
    print("Creating room...")
    room = rtc.Room()

    await room.connect("ws://localhost:7880", token)
    print("Connected to room")

    # Create session
    session = AgentSession(
        llm=google.realtime.RealtimeModel(
            voice="Aoede",
            temperature=0.7,
            proactivity=True,
        ),
        vad=silero.VAD.load(),
        preemptive_generation=True,
    )

    agent = Agent(
        instructions="You are a professional customer service assistant.",
    )

    print("Starting session...")
    await session.start(
        agent=agent,
        room=room,
    )

    print("Generating greeting...")
    try:
        await session.generate_reply(
            instructions="Greet the user with: Hello and welcome. I am your AI customer service assistant. How can I assist you today?"
        )
        print("Greeting generated successfully!")
    except Exception as e:
        print(f"Error generating greeting: {e}")
        import traceback

        traceback.print_exc()

    # Wait a bit to see if audio is played
    await asyncio.sleep(5)

    await room.disconnect()
    print("Test complete")


if __name__ == "__main__":
    asyncio.run(test_greeting())
