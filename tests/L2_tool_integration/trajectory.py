"""
Trajectory recording and analysis utilities for Level-2 tests.

The core idea: every ADK ``Runner.run_async`` call yields ``Event`` objects
that carry ``function_call`` and ``function_response`` parts.  We collect
them into a structured ``Trajectory`` that test-code can query with simple,
readable helpers.
"""

from __future__ import annotations

import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part


# Data classes

@dataclass
class ToolInvocation:
    """One recorded tool call inside a trajectory."""

    agent_name: str
    tool_name: str
    arguments: dict[str, Any]
    response: Any = None
    timestamp: float = field(default_factory=time.time)

    @property
    def signature(self) -> tuple[str, str]:
        canonical = str(sorted(self.arguments.items()))
        return (self.tool_name, canonical)


@dataclass
class Trajectory:
    """
    Immutable-ish record of everything that happened during one agent run.
    """

    raw_events: list = field(default_factory=list)
    tool_calls: list[ToolInvocation] = field(default_factory=list)
    final_text: str = ""
    agent_texts: dict[str, str] = field(default_factory=dict)

    #  Query helpers

    def tools_called(self) -> list[str]:
        return [tc.tool_name for tc in self.tool_calls]

    def unique_tools_called(self) -> set[str]:
        return set(self.tools_called())

    def tool_was_called(self, name: str) -> bool:
        return name in self.unique_tools_called()

    def tool_was_not_called(self, name: str) -> bool:
        return name not in self.unique_tools_called()

    def tool_call_count(self, name: str) -> int:
        return sum(1 for tc in self.tool_calls if tc.tool_name == name)

    def get_tool_calls(self, name: str) -> list[ToolInvocation]:
        return [tc for tc in self.tool_calls if tc.tool_name == name]

    def get_tool_arguments(self, name: str, occurrence: int = 0) -> dict:
        calls = self.get_tool_calls(name)
        if occurrence < len(calls):
            return calls[occurrence].arguments
        raise IndexError(
            f"Tool '{name}' was called {len(calls)} time(s); "
            f"requested occurrence #{occurrence}"
        )

    def get_tool_response(self, name: str, occurrence: int = 0) -> Any:
        calls = self.get_tool_calls(name)
        if occurrence < len(calls):
            return calls[occurrence].response
        raise IndexError(
            f"Tool '{name}' was called {len(calls)} time(s); "
            f"requested occurrence #{occurrence}"
        )

    #  Safety helpers

    def has_repeated_identical_calls(self, max_allowed: int = 3) -> bool:
        counts = Counter(tc.signature for tc in self.tool_calls)
        return any(n > max_allowed for n in counts.values())

    def max_identical_call_count(self) -> int:
        if not self.tool_calls:
            return 0
        counts = Counter(tc.signature for tc in self.tool_calls)
        return max(counts.values())

    def total_tool_calls(self) -> int:
        return len(self.tool_calls)

    #  Error-recovery helpers

    _ERROR_KEYWORDS: tuple[str, ...] = (
        "sorry", "couldn't", "could not", "unable", "unavailable",
        "not available", "error", "failed", "try again", "apologize",
    )

    def output_contains_graceful_error(
        self, extra_keywords: list[str] | None = None,
    ) -> bool:
        keywords = self._ERROR_KEYWORDS + tuple(extra_keywords or [])
        lower = self.final_text.lower()
        return any(kw in lower for kw in keywords)

    #  Pretty printing
    def summary(self) -> str:
        lines = ["═══ Trajectory Summary ═══"]
        for i, tc in enumerate(self.tool_calls, 1):
            lines.append(
                f"  {i}. [{tc.agent_name}] → {tc.tool_name}({tc.arguments})"
            )
        lines.append(f"  Final text (first 300 chars): {self.final_text[:300]}")
        return "\n".join(lines)


#  Collector

def _safe_dict(mapping: Any) -> dict:
    try:
        return dict(mapping)
    except (TypeError, ValueError):
        return {}


async def collect_trajectory(
    runner: Runner,
    user_id: str,
    session_id: str,
    message: str,
) -> Trajectory:
    trajectory = Trajectory()
    user_content = Content(role="user", parts=[Part(text=message)])

    unmatched: list[ToolInvocation] = []

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=user_content,
    ):
        trajectory.raw_events.append(event)

        if not event.content or not event.content.parts:
            continue

        author = getattr(event, "author", "unknown")

        for part in event.content.parts:
            fc = getattr(part, "function_call", None)
            if fc is not None:
                invocation = ToolInvocation(
                    agent_name=author,
                    tool_name=fc.name,
                    arguments=_safe_dict(fc.args),
                )
                trajectory.tool_calls.append(invocation)
                unmatched.append(invocation)

            fr = getattr(part, "function_response", None)
            if fr is not None:
                for i, inv in enumerate(unmatched):
                    if inv.tool_name == fr.name:
                        inv.response = fr.response
                        unmatched.pop(i)
                        break

            text = getattr(part, "text", None)
            if text:
                trajectory.final_text = text
                trajectory.agent_texts[author] = text

    return trajectory


# Factory

async def make_runner_and_session(
    agent,
    *,
    app_name: str = "test",
    user_id: str = "test_user",
    initial_state: dict[str, Any] | None = None,
) -> tuple[Runner, str, str, InMemorySessionService]:
    """
    Build a Runner + Session for one agent.
    Optionally pre-populate state to simulate prior agents in the pipeline.
    """
    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent,
        app_name=app_name,
        session_service=session_service,
    )
    session = await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        state=initial_state or {},
    )

    return runner, user_id, session.id, session_service