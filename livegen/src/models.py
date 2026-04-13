import time
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class CallEndReason(str, Enum):
    COMPLETED = "completed"
    HANGUP = "hangup"
    ERROR = "error"
    TIMEOUT = "timeout"
    ESCALATION = "escalation"


class CollectedInfo(BaseModel):
    phone: Optional[str] = None
    extension: Optional[str] = None
    intent: Optional[str] = None
    email: Optional[str] = None
    account_number: Optional[str] = None


class SessionState(BaseModel):
    session_id: str = ""
    caller_id: Optional[str] = None
    collected_phone: str = ""
    collected_ext: str = ""
    intent: Optional[str] = None
    sentiment_score: float = 0.0
    call_start_time: float = Field(default_factory=time.time)
    turn_count: int = 0
    interrupted: bool = False
    resolution_attempts: int = 0
    error_count: int = 0


class CallMetrics(BaseModel):
    session_id: str
    call_start: float
    call_end: float = 0.0
    total_turns: int = 0
    interruptions: int = 0
    error_count: int = 0
    service_type: str = "support"
    collected_info: CollectedInfo = Field(default_factory=CollectedInfo)
    success: bool = False
    end_reason: str = ""


class TranscriptEntry(BaseModel):
    role: str
    text: str
    timestamp: float


class CallTranscript(BaseModel):
    session_id: str
    call_start: float
    entries: list[TranscriptEntry] = []
