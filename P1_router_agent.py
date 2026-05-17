"""
agents/router_agent.py
----------------------
RouterAgent — the orchestrator and traffic controller of the system.

Responsibility:
  1. Receives every incoming user query.
  2. Calls VectorAgent to get a semantic department suggestion.
  3. Sends the query + vector hint to the LLM for final classification.
  4. Dispatches the query to the correct department agent (Sales / HR / Operations).
  5. Handles IRRELEVANT messages gracefully without forwarding them.
  6. Returns the final response to the caller.

Design pattern:  Chain-of-thought routing → department dispatch → response assembly.
"""

from __future__ import annotations

import json
from openai import OpenAI

from config.settings import (
    OPENAI_API_KEY,
    OPENAI_MODEL,
    ROUTER_SYSTEM_PROMPT,
)
from agents.vector_agent import VectorAgent
from agents.department_agents import SalesAgent, HRAgent, OperationsAgent


class RouterAgent:
    """Master orchestrator that routes queries to the right department agent."""

    def __init__(self):
        self.client       = OpenAI(api_key=OPENAI_API_KEY)
        self.vector_agent = VectorAgent()
        self.agents       = {
            "SALES":      SalesAgent(self.client),
            "HR":         HRAgent(self.client),
            "OPERATIONS": OperationsAgent(self.client),
        }
        print("[RouterAgent] Initialised. All department agents ready.")

    # ── Public API ─────────────────────────────────────────────────────────────

    def process(self, query: str) -> dict:
        """
        Full pipeline: vector suggestion → LLM classification → department response.

        Returns
        -------
        dict with keys:
            query        : original user query
            department   : where it was routed
            confidence   : router confidence score (0-1)
            reason       : router classification reason
            vector_hint  : semantic department from VectorAgent
            response     : final answer from department agent (or rejection msg)
        """
        print(f"\n[RouterAgent] Processing: '{query[:80]}…'")

        # ── Step 1: Vector Agent semantic suggestion ──────────────────────────
        vector_result = self.vector_agent.suggest_department(query)
        print(f"[VectorAgent] → {vector_result['department']} "
              f"(similarity={vector_result['similarity']:.3f})")

        # ── Step 2: LLM-based routing decision ───────────────────────────────
        routing = self._classify(query, vector_result)
        department = routing.get("department", "IRRELEVANT")
        print(f"[RouterAgent] → Classified as: {department} "
              f"(confidence={routing.get('confidence', 0):.2f})")

        # ── Step 3: Dispatch to department agent or reject ────────────────────
        if department == "IRRELEVANT":
            response_text = self._handle_irrelevant(query)
        else:
            agent         = self.agents[department]
            response_text = agent.respond(query)

        return {
            "query":       query,
            "department":  department,
            "confidence":  routing.get("confidence", 0),
            "reason":      routing.get("reason", ""),
            "vector_hint": vector_result["department"],
            "response":    response_text,
        }

    # ── Private helpers ───────────────────────────────────────────────────────

    def _classify(self, query: str, vector_result: dict) -> dict:
        """Ask LLM to classify the query; include vector hint as context."""
        hint_block = (
            f"Vector Agent Suggestion: {vector_result['department']} "
            f"(similarity {vector_result['similarity']:.3f})\n"
            f"Matched Doc Snippet: {vector_result['matched_doc']}\n\n"
        )
        user_msg = hint_block + f"User Query: {query}"

        resp = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"department": "IRRELEVANT", "confidence": 0.0,
                    "reason": "Router failed to parse LLM response."}

    def _handle_irrelevant(self, query: str) -> str:
        return (
            "⚠️  Your message does not appear to be related to Sales, HR, or Operations. "
            "Please rephrase your query or contact the relevant department directly. "
            f"(Received: '{query[:60]}…')"
        )
