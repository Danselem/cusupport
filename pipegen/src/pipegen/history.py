"""Conversation history management."""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger


class ConversationHistory:
    """Manages conversation history with file-based persistence."""

    def __init__(self, storage_dir: str = ".conversations"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self._conversations: dict[str, list[dict[str, Any]]] = {}
        self._lock = asyncio.Lock()

    def _get_file_path(self, conversation_id: str) -> Path:
        """Get the file path for a conversation."""
        return self.storage_dir / f"{conversation_id}.json"

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add a message to the conversation history."""
        async with self._lock:
            if conversation_id not in self._conversations:
                self._conversations[conversation_id] = []
                await self._load_conversation(conversation_id)

            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {},
            }

            self._conversations[conversation_id].append(message)
            await self._save_conversation(conversation_id)

    async def get_history(
        self,
        conversation_id: str,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Get conversation history, optionally limited to recent messages."""
        async with self._lock:
            await self._load_conversation(conversation_id)

            history = self._conversations.get(conversation_id, [])

            if limit:
                return history[-limit:]
            return history

    async def clear_history(self, conversation_id: str) -> None:
        """Clear conversation history."""
        async with self._lock:
            self._conversations.pop(conversation_id, None)
            file_path = self._get_file_path(conversation_id)
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Cleared conversation history: {conversation_id}")

    async def get_conversation_count(self) -> int:
        """Get the number of stored conversations."""
        return len(list(self.storage_dir.glob("*.json")))

    async def _load_conversation(self, conversation_id: str) -> None:
        """Load conversation from file if not already loaded."""
        if conversation_id in self._conversations:
            return

        file_path = self._get_file_path(conversation_id)
        if file_path.exists():
            try:
                with open(file_path) as f:  # noqa: ASYNC230
                    self._conversations[conversation_id] = json.load(f)
                logger.debug(f"Loaded conversation: {conversation_id}")
            except Exception as e:
                logger.error(f"Failed to load conversation {conversation_id}: {e}")
                self._conversations[conversation_id] = []
        else:
            self._conversations[conversation_id] = []

    async def _save_conversation(self, conversation_id: str) -> None:
        """Save conversation to file."""
        file_path = self._get_file_path(conversation_id)
        try:
            with open(file_path, "w") as f:  # noqa: ASYNC230
                json.dump(self._conversations[conversation_id], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save conversation {conversation_id}: {e}")

    def to_langchain_format(self, conversation_id: str) -> list[dict[str, str]]:
        """Convert history to LangChain message format."""
        history = self._conversations.get(conversation_id, [])
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in history
            if msg["role"] in ("user", "assistant", "system")
        ]


# Global instance
_history: ConversationHistory | None = None


def get_conversation_history() -> ConversationHistory:
    """Get or create the global conversation history instance."""
    global _history
    if _history is None:
        storage_dir = os.getenv("CONVERSATION_STORAGE_DIR", ".conversations")
        _history = ConversationHistory(storage_dir=storage_dir)
    return _history
