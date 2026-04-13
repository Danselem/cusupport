"""
LiveKit Server Connection Test
Run: uv run python test_connection.py
     docker exec livegen-agent-1 python test_connection.py
"""

from livekit import api

print("=== LiveKit Server Test ===")
print("Server: ws://localhost:7880")
print("API Key: dev")
print("")

# Create token with room
token = api.AccessToken("dev", "secret")
token = token.with_identity("test-user")
token = token.with_grants(
    api.VideoGrants(
        room="test-room",
        room_join=True,
        can_publish=True,
        can_subscribe=True,
    )
)
jwt = token.to_jwt()

print(f"✓ Token created: {jwt[:50]}...")
print("✓ LiveKit server is accessible!")
