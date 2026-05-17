"""
config/settings.py
------------------
Central configuration for the Multi-Agent Router System.
Loads environment variables and defines department routing knowledge base.
"""

import os
from dotenv import load_dotenv

load_dotenv(override=True)

# ── LLM Settings ────────────────────────────────────────────────────────────
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str   = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# ── Vector Store ─────────────────────────────────────────────────────────────
VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", "./vector_store")
EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"   # local sentence-transformer

# ── Department Routing Knowledge ─────────────────────────────────────────────
# These sample documents seed the vector store so the VectorAgent can
# recommend which department best matches an incoming query.
DEPARTMENT_DOCS: list[dict] = [
    # SALES
    {
        "content": "Sales team handles product pricing, discounts, purchase orders, "
                   "quotations, upselling, cross-selling, contract negotiations, "
                   "revenue targets, customer acquisition, and deal closures.",
        "department": "SALES",
    },
    {
        "content": "Sales department manages CRM data, lead pipelines, demos, "
                   "proposals, customer onboarding after purchase, and sales forecasts.",
        "department": "SALES",
    },
    # HR
    {
        "content": "HR department manages employee recruitment, onboarding, "
                   "payroll queries, benefits, leave policies, performance reviews, "
                   "training programs, and workplace grievances.",
        "department": "HR",
    },
    {
        "content": "Human Resources handles job applications, interview scheduling, "
                   "offer letters, termination procedures, employee relations, "
                   "compliance with labor laws, and diversity initiatives.",
        "department": "HR",
    },
    # OPERATIONS
    {
        "content": "Operations team provides information on inventory levels, "
                   "supply chain status, warehouse management, logistics, "
                   "order fulfillment, SLA adherence, and process documentation.",
        "department": "OPERATIONS",
    },
    {
        "content": "Operations handles production schedules, vendor management, "
                   "quality control, delivery timelines, operational KPIs, "
                   "and cross-department process coordination.",
        "department": "OPERATIONS",
    },
    # IRRELEVANT / SPAM
    {
        "content": "Casual chit-chat, jokes, personal questions, random trivia, "
                   "spam messages, hate speech, and completely off-topic queries "
                   "should be flagged and not routed to any department.",
        "department": "IRRELEVANT",
    },
]

# ── Agent Prompts ─────────────────────────────────────────────────────────────
ROUTER_SYSTEM_PROMPT = """
You are the Master Router Agent for a multi-department enterprise system.
Your ONLY job is to classify the incoming query into exactly one of:
  - SALES
  - HR
  - OPERATIONS
  - IRRELEVANT

Rules:
1. Use the Vector Agent's department suggestion as a strong hint.
2. Apply your own reasoning to confirm or override the hint.
3. If the message is spam, abusive, or completely unrelated, classify as IRRELEVANT.
4. Respond with a JSON object ONLY: {"department": "<DEPARTMENT>", "confidence": <0-1>, "reason": "<one sentence>"}
"""

SALES_SYSTEM_PROMPT = """
You are the Sales Department AI Assistant.
Answer queries related to: pricing, quotes, product info, purchase orders,
discounts, contracts, lead follow-ups, and revenue questions.
Be professional, persuasive, and customer-focused.
If a query is outside your scope, say so politely.
"""

HR_SYSTEM_PROMPT = """
You are the HR Department AI Assistant.
Answer queries related to: recruitment, payroll, leave policies, benefits,
performance reviews, onboarding, training, compliance, and employee relations.
Be empathetic, policy-compliant, and clear in your responses.
If a query is outside HR scope, say so politely.
"""

OPERATIONS_SYSTEM_PROMPT = """
You are the Operations Department AI Assistant.
Answer queries related to: inventory, supply chain, logistics, order status,
production schedules, vendor management, delivery, and operational KPIs.
Be precise, data-driven, and process-oriented.
If a query is outside Operations scope, say so politely.
"""
