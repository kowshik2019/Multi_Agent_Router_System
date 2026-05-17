# PROJECT 1 — Multi-Agent Router System

## Short Description:
Enterprise-grade multi-agent AI system that intelligently classifies and routes queries to Sales, HR, or Operations using FAISS vector search + LLM orchestration.

---

## Full GitHub Repository Description

### 🤖 Multi-Agent Router System — Intelligent Enterprise Query Routing

An enterprise-grade AI pipeline that automatically routes any incoming query to the correct department agent using a dual-layer decision engine: **FAISS vector embeddings** for fast semantic matching followed by **GPT-4o-mini** for nuanced LLM-based classification.

#### 🔑 What makes this unique:

**Two-Layer Routing Intelligence**
Every query hits two decision systems before reaching a department agent. First, a VectorAgent performs instant cosine similarity search against department knowledge documents using sentence-transformers and FAISS — no LLM call, no API cost, deterministic results. Then the RouterAgent combines this vector "hint" with the original query and sends it to GPT-4o-mini, which confirms or overrides the suggestion with full reasoning. The final classification includes a department label, confidence score (0–1), and one-sentence justification — all as structured JSON.

**Department Specialist Agents with Memory**
Three domain-specific agents (Sales, HR, Operations) each carry their own system prompt and maintain a rolling 10-turn conversation history. This means follow-up questions within a session are answered coherently — the Sales agent remembers that you already asked about bulk pricing when you follow up about warranty terms.

**Graceful Irrelevance Handling**
Spam, off-topic queries, and abuse are identified at the Router layer and rejected cleanly — no department agent is ever invoked, no LLM token is wasted on irrelevant content.

**Zero-Cost Embeddings**
The VectorAgent uses the `all-MiniLM-L6-v2` sentence-transformer model locally. No embedding API calls. The FAISS index is persisted to disk and loads instantly on subsequent runs — the semantic routing layer is effectively free after first setup.

#### 🏗️ Architecture:
```
User Query → VectorAgent (FAISS) → RouterAgent (GPT-4o-mini) → [Sales | HR | Operations | Reject]
```

#### 🛠️ Tech Stack:
Python · OpenAI GPT-4o-mini · FAISS · sentence-transformers · LangChain · Rich

#### 📁 Key Files:
| File | Role |
|------|------|
| `P1_vector_agent.py` | FAISS semantic routing layer |
| `P1_router_agent.py` | Master orchestrator + LLM classifier |
| `P1_department_agents.py` | Sales, HR, Operations domain agents |
| `P1_settings.py` | All prompts, config, knowledge base |
| `P1_main.py` | Interactive CLI + demo batch runner |

#### 🚀 Quick Start:
```bash
pip install -r P1_requirements.txt
echo "OPENAI_API_KEY=your_key" > .env
python P1_main.py           # interactive
python P1_main.py --demo    # batch demo
```

#### 💡 Use Cases:
- Enterprise chatbot routing to correct department
- Customer support triage automation
- Internal helpdesk query classification
- Multi-team knowledge base assistant



#### 🔧 Extend It:
Adding a new department takes 4 steps: add knowledge docs to `P1_settings.py`, add a system prompt, create an agent class, and register it in `P1_router_agent.py`. The FAISS index auto-rebuilds.
