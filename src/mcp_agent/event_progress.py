"""Module for converting log events to progress events."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from mcp_agent.logging.events import Event


class ProgressAction(str, Enum):
    """Progress actions available in the system."""

    STARTING = "Starting"
    LOADED = "Loaded"
    INITIALIZED = "Initialized"
    CHATTING = "Chatting"
    READY = "Ready"
    CALLING_TOOL = "Calling Tool"
    FINISHED = "Finished"
    SHUTDOWN = "Shutdown"
    AGGREGATOR_INITIALIZED = "Running"
    ROUTING = "Routing"
    FATAL_ERROR = "Error"


@dataclass
class ProgressEvent:
    """Represents a progress event converted from a log event."""

    action: ProgressAction
    target: str
    details: Optional[str] = None
    agent_name: Optional[str] = None

    def __str__(self) -> str:
        """Format the progress event for display."""
        base = f"{self.action.ljust(11)}. {self.target}"
        if self.details:
            base += f" - {self.details}"
        if self.agent_name:
            base = f"[{self.agent_name}] {base}"
        return base


def convert_log_event(event: Event) -> Optional[ProgressEvent]:
    """Convert a log event to a progress event if applicable."""

    # Check to see if there is any additional data
    if not event.data:
        return None

    event_data = event.data.get("data")
    if not isinstance(event_data, dict):
        return None

    progress_action = event_data.get("progress_action")
    if not progress_action:
        return None

    # Build target string based on the event type.
    # Progress display is currently [time] [event] --- [target] [details]
    namespace = event.namespace
    agent_name = event_data.get("agent_name")
    target = agent_name
    details = ""
    if progress_action == ProgressAction.FATAL_ERROR:
        details = event_data.get("error_message", "An error occurred")
    elif "mcp_aggregator" in namespace:
        server_name = event_data.get("server_name", "")
        tool_name = event_data.get("tool_name")
        if tool_name:
            # fetch(fetch)
            details = f"{server_name} ({tool_name})"
        else:
            details = f"{server_name}"

    elif "augmented_llm" in namespace:
        model = event_data.get("model", "")

        details = f"{model}"
        chat_turn = event_data.get("chat_turn")
        if chat_turn is not None:
            details = f"{model} turn {chat_turn}"
    else:
        if not target:
            event_data.get("target", "unknown")

    return ProgressEvent(
        ProgressAction(progress_action),
        target,
        details,
        agent_name=event_data.get("agent_name"),
    )
