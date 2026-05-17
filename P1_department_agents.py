"""
agents/department_agents.py
---------------------------
Department Agents — specialised AI workers for Sales, HR, and Operations.

Each agent:
  - Has a domain-specific system prompt (from config/settings.py).
  - Maintains a short conversation history (context window) so follow-up
    questions within a session are coherent.
  - Exposes a single `respond(query)` method called by the RouterAgent.

All three agents share the same OpenAI client instance passed from RouterAgent,
avoiding redundant client creation and respecting connection pooling.
"""

from __future__ import annotations

from openai import OpenAI

from config.settings import (
    OPENAI_MODEL,
    SALES_SYSTEM_PROMPT,
    HR_SYSTEM_PROMPT,
    OPERATIONS_SYSTEM_PROMPT,
)


class _BaseDeptAgent:
    """Shared base for all department agents."""

    SYSTEM_PROMPT: str = ""   # overridden by subclasses
    MAX_HISTORY   : int = 10  # keep last N turns to manage context size

    def __init__(self, client: OpenAI, name: str):
        self.client  = client
        self.name    = name
        self.history : list[dict] = []   # shared memory within a session
        print(f"[{self.name}] Initialised.")

    def respond(self, query: str) -> str:
        """
        Generate a department-specific response for the given query.
        Maintains rolling conversation history for context continuity.
        """
        # Add user turn
        self.history.append({"role": "user", "content": query})

        messages = (
            [{"role": "system", "content": self.SYSTEM_PROMPT}]
            + self.history[-self.MAX_HISTORY:]
        )

        resp = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.3,
        )
        answer = resp.choices[0].message.content

        # Save assistant turn
        self.history.append({"role": "assistant", "content": answer})
        print(f"[{self.name}] Response generated ({len(answer)} chars).")
        return answer

    def clear_history(self) -> None:
        """Reset conversation memory (call between unrelated sessions)."""
        self.history = []
        print(f"[{self.name}] History cleared.")


# ── Concrete Department Agents ────────────────────────────────────────────────

class SalesAgent(_BaseDeptAgent):
    """
    Sales Department Agent.
    Handles: pricing, quotes, product inquiries, purchase orders,
             discounts, contract negotiations, CRM queries, lead follow-ups.
    """
    SYSTEM_PROMPT = SALES_SYSTEM_PROMPT

    def __init__(self, client: OpenAI):
        super().__init__(client, "SalesAgent")


class HRAgent(_BaseDeptAgent):
    """
    HR Department Agent.
    Handles: recruitment, payroll, leave policies, benefits,
             onboarding, performance reviews, compliance, grievances.
    """
    SYSTEM_PROMPT = HR_SYSTEM_PROMPT

    def __init__(self, client: OpenAI):
        super().__init__(client, "HRAgent")


class OperationsAgent(_BaseDeptAgent):
    """
    Operations Department Agent.
    Handles: inventory status, supply chain, logistics, delivery timelines,
             production schedules, vendor queries, operational KPIs.
    """
    SYSTEM_PROMPT = OPERATIONS_SYSTEM_PROMPT

    def __init__(self, client: OpenAI):
        super().__init__(client, "OperationsAgent")
