# 🤖 Multi-Agent Router System
### Intelligent Enterprise Query Routing via Vector Embeddings + LLM Orchestration

---

## 📌 What Is This Project?

The **Multi-Agent Router System** is a production-grade AI pipeline that automatically classifies any incoming text query and routes it to the correct department agent — **Sales**, **HR**, or **Operations** — with full reasoning transparency.

Every query passes through a **two-layer decision engine**:
1. **VectorAgent** — semantic nearest-neighbour matching using FAISS + sentence-transformers (no LLM, no API cost)
2. **RouterAgent** — LLM-powered classification using the vector hint + its own reasoning via GPT-4o-mini

The correct **Department Agent** then answers the query using a domain-specific system prompt and maintains conversation history for follow-up questions. Irrelevant or spam queries are rejected gracefully before ever reaching a department agent.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           INCOMING USER QUERY                               │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          VECTOR AGENT                                       │
│                                                                             │
│   Query Text ──► sentence-transformer embed ──► FAISS cosine search        │
│                                                                             │
│   Returns: { department: "SALES", similarity: 0.891, matched_doc: "..." }  │
│                                                                             │
│   📦 Local model (all-MiniLM-L6-v2) | No API cost | Persisted to disk      │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │  vector hint
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ROUTER AGENT (Orchestrator)                        │
│                                                                             │
│   Prompt = vector hint + original query                                     │
│   LLM (GPT-4o-mini) → JSON: { department, confidence, reason }             │
│                                                                             │
│   Decision logic:                                                           │
│     Vector + LLM agree  → HIGH confidence route                            │
│     Vector overridden   → LLM reasoning wins, logged                       │
│     Neither matches     → IRRELEVANT → reject gracefully                   │
└──────┬──────────────────────────────────────────────────────────────────────┘
       │
       ├──────────────────┬───────────────────┬─────────────────────────────►
       ▼                  ▼                   ▼                   ▼
┌────────────┐    ┌────────────┐    ┌────────────────┐   ┌──────────────────┐
│   SALES    │    │    HR      │    │  OPERATIONS    │   │   IRRELEVANT     │
│   AGENT    │    │   AGENT    │    │    AGENT       │   │   HANDLER        │
│            │    │            │    │                │   │                  │
│ Pricing    │    │ Recruitment│    │ Inventory      │   │ Polite rejection │
│ Quotes     │    │ Payroll    │    │ Supply Chain   │   │ No dept routed   │
│ Contracts  │    │ Benefits   │    │ Logistics      │   │                  │
│ CRM        │    │ Compliance │    │ Delivery       │   │                  │
└────────────┘    └────────────┘    └────────────────┘   └──────────────────┘
       │                  │                   │
       └──────────────────┴───────────────────┘
                          │
                          ▼
                   FINAL RESPONSE
            (department answer + routing metadata)
```

---

## 📁 File Structure & Descriptions

```
Project1_MultiAgent_Router/
│
├── P1_main.py                  ← Entry point. Interactive CLI + demo batch mode.
├── P1_settings.py              ← All config: API keys, prompts, dept knowledge docs.
├── P1_vector_agent.py          ← FAISS-based semantic department suggestion.
├── P1_router_agent.py          ← Master orchestrator: routes query to right agent.
├── P1_department_agents.py     ← Sales, HR, Operations agents with memory.
├── P1_logger.py                ← Rich-based pretty console output.
├── P1_requirements.txt         ← All Python dependencies.
└── P1_README.md                ← This file.
```

### Detailed File Explanations

#### `P1_main.py` — Entry Point
The application entry point. Supports two modes:
- **Interactive mode** (`python P1_main.py`): Prompts you to type queries one at a time in a loop. Type `exit` to quit.
- **Demo batch mode** (`python P1_main.py --demo`): Runs 8 pre-written sample queries covering all departments and irrelevant cases. Good for first run testing.

Initialises `RouterAgent` once and reuses it for all queries in the session.

#### `P1_settings.py` — Configuration Hub
Central configuration file. Everything configurable lives here:
- OpenAI API key and model name (loaded from `.env`)
- Vector store path and embedding model name
- `DEPARTMENT_DOCS` — the seed knowledge base (7 documents covering Sales, HR, Operations, and Irrelevant patterns) used to build the FAISS index
- All 5 system prompts: `ROUTER_SYSTEM_PROMPT`, `SALES_SYSTEM_PROMPT`, `HR_SYSTEM_PROMPT`, `OPERATIONS_SYSTEM_PROMPT`

To add a new department, add docs here and a new system prompt — no other file changes needed except `P1_router_agent.py` registration.

#### `P1_vector_agent.py` — Semantic Memory Layer
The fastest and cheapest layer of routing. Uses:
- `sentence-transformers` (`all-MiniLM-L6-v2`) to embed text locally — no API calls
- `faiss-cpu` (`IndexFlatIP`) for cosine similarity search on L2-normalised vectors
- First run: builds the FAISS index from `DEPARTMENT_DOCS`, persists to `vector_store/dept_index.faiss` + `dept_meta.json`
- Subsequent runs: loads the persisted index instantly
- `add_documents()` method allows hot-adding new department knowledge without rebuilding

Returns: `{department, similarity (0-1), matched_doc_snippet}`

#### `P1_router_agent.py` — Master Orchestrator
The traffic controller. Every query passes through this agent. Steps:
1. Calls `VectorAgent.suggest_department(query)` for the fast semantic hint
2. Builds a prompt combining the vector hint + original query
3. Calls GPT-4o-mini with `response_format: json_object` → guaranteed structured output
4. Parses `{department, confidence, reason}` from LLM response
5. If department is valid: dispatches to the correct `DepartmentAgent`
6. If `IRRELEVANT`: calls `_handle_irrelevant()` — polite rejection, no dept agent called

#### `P1_department_agents.py` — Domain Specialist Agents
Three agents, one shared base class `_BaseDeptAgent`:
- Each has its own `SYSTEM_PROMPT` constant (loaded from `P1_settings.py`)
- Maintains `self.history` — a rolling list of `{role, content}` dicts (last 10 turns)
- History is included in every LLM call → follow-up questions within a session are coherent
- `clear_history()` resets between unrelated sessions
- All three share the same `OpenAI` client instance (passed from RouterAgent) — no duplicate connections

#### `P1_logger.py` — Rich Console Output
Pretty-prints routing decisions and department responses using the `rich` library:
- Colour-coded by department: Sales=green, HR=blue, Operations=yellow, Irrelevant=red
- Routing metadata table (query, vector hint, routed dept, confidence, reason)
- Department response in a bordered panel

---

## 🔄 Data Flow — Step by Step

```
1. User types: "I need a discount for 500 units"

2. VectorAgent embeds query → FAISS search → returns:
   { department: "SALES", similarity: 0.891 }

3. RouterAgent builds prompt:
   "Vector hint: SALES (0.891). Query: I need a discount..."
   → GPT-4o-mini → { department: "SALES", confidence: 0.95, reason: "Discount query" }

4. RouterAgent dispatches to SalesAgent

5. SalesAgent builds messages:
   [system: SALES_SYSTEM_PROMPT] + [user history] + [current query]
   → GPT-4o-mini → "Our standard bulk discount for 500+ units is 12%..."

6. History saved. Response returned to logger.

7. Rich console prints routing table + response panel.
```

---

## ⚙️ Setup & Execution

### Prerequisites
- Python 3.10+
- OpenAI API key

### Step 1 — Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### Step 2 — Install Dependencies
```bash
pip install -r P1_requirements.txt
```

### Step 3 — Configure Environment
```bash
# Create .env file
echo "OPENAI_API_KEY=your_key_here" > .env
echo "OPENAI_MODEL=gpt-4o-mini" >> .env
echo "VECTOR_DB_PATH=./vector_store" >> .env
```

### Step 4 — Fix Imports (flat file structure)
Since files are prefixed and flat (no subfolders), update imports in each file:

In `P1_router_agent.py`, change:
```python
from config.settings import ...      →  from P1_settings import ...
from agents.vector_agent import ...  →  from P1_vector_agent import ...
from agents.department_agents import → from P1_department_agents import ...
```

In `P1_vector_agent.py`, change:
```python
from config.settings import ...      →  from P1_settings import ...
```

In `P1_department_agents.py`, change:
```python
from config.settings import ...      →  from P1_settings import ...
```

In `P1_main.py`, change:
```python
from agents.router_agent import ...  →  from P1_router_agent import ...
from utils.logger import ...         →  from P1_logger import ...
```

### Step 5 — Run Interactive Mode
```bash
python P1_main.py
```

### Step 6 — Run Demo Batch
```bash
python P1_main.py --demo
```

---

## 💬 Sample Queries

| Department | Example Query |
|---|---|
| SALES | `"What is the bulk discount for orders over 500 units?"` |
| SALES | `"I want a quote for Model X5 with 3-year warranty"` |
| HR | `"How many sick days do I get annually?"` |
| HR | `"I want to apply for the senior developer opening"` |
| OPERATIONS | `"What is the current stock level for SKU-48291?"` |
| OPERATIONS | `"When will the delayed shipment from Vendor A arrive?"` |
| IRRELEVANT | `"Tell me a joke about penguins"` |
| IRRELEVANT | `"What is the capital of France?"` |

---

## 🧠 Key Design Decisions

| Decision | Why |
|---|---|
| Two-layer routing (Vector + LLM) | Vector = fast/cheap first pass. LLM = nuanced reasoning. Together = high accuracy. |
| FAISS IndexFlatIP | Lightweight, no server, persists to disk. Perfect for moderate-scale routing. |
| Local embedding model | Zero embedding API cost. Runs fully offline. Adequate accuracy for routing. |
| JSON-mode LLM response | Structured output = no parsing failures. Deterministic department extraction. |
| Rolling conversation history | Enables multi-turn coherent sessions per department without re-sending full context. |
| Shared OpenAI client | One connection pool across all dept agents. Memory-efficient. |

---

## 📦 Dependencies

| Package | Version | Purpose |
|---|---|---|
| `openai` | ≥1.30 | LLM API — Router + Department agents |
| `sentence-transformers` | ≥3.0 | Local embedding model for VectorAgent |
| `faiss-cpu` | ≥1.7.4 | Vector similarity index |
| `langchain` | ≥0.2 | Utility wrappers (available for extensions) |
| `python-dotenv` | ≥1.0 | `.env` file loading |
| `rich` | ≥13.7 | Coloured console output |
| `pydantic` | ≥2.7 | Data validation |
| `numpy` | ≥1.26 | Array ops for embeddings |
| `tiktoken` | ≥0.7 | Token counting |

---

## 🔧 Extending the System

**Add a new department (e.g. Finance):**
1. Add 2 knowledge docs to `DEPARTMENT_DOCS` in `P1_settings.py`
2. Add `FINANCE_SYSTEM_PROMPT` constant in `P1_settings.py`
3. Add `FinanceAgent` class in `P1_department_agents.py`
4. Register in `P1_router_agent.py`: `self.agents["FINANCE"] = FinanceAgent(self.client)`
5. Delete `vector_store/` folder → FAISS index auto-rebuilds on next run

**Add persistent cross-session memory:**
Replace the in-memory `self.history` list in `_BaseDeptAgent` with a Redis or SQLite-backed store keyed by `session_id`.
