"""Turn-level tracing for debugging and auditability."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class TraceEvent:
    """Single event in a turn trace."""
    timestamp: str
    event_type: str  # e.g., "intent_classified", "ambiguity_detected", "tool_called"
    data: dict[str, Any]
    
    @classmethod
    def now(cls, event_type: str, **data) -> TraceEvent:
        """Create event with current timestamp."""
        return cls(
            timestamp=datetime.utcnow().isoformat(),
            event_type=event_type,
            data=data
        )


@dataclass
class TurnTrace:
    """Complete trace for one conversation turn."""
    turn_id: str
    user_input: str
    events: list[TraceEvent] = field(default_factory=list)
    
    def add_event(self, event_type: str, **data) -> None:
        """Add event to trace."""
        self.events.append(TraceEvent.now(event_type, **data))
    
    def to_dict(self) -> dict:
        """Convert to dictionary for logging."""
        return {
            "turn_id": self.turn_id,
            "user_input": self.user_input,
            "events": [
                {
                    "timestamp": e.timestamp,
                    "type": e.event_type,
                    "data": e.data
                }
                for e in self.events
            ]
        }
    
    def print_summary(self) -> None:
        """Print human-readable trace summary."""
        print(f"\n{'='*80}")
        print(f"TRACE: {self.turn_id}")
        print(f"Input: {self.user_input}")
        print(f"{'-'*80}")
        for event in self.events:
            print(f"[{event.timestamp}] {event.event_type}")
            for key, value in event.data.items():
                print(f"  {key}: {value}")
        print(f"{'='*80}\n")