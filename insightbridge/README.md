# InsightBridge

InsightBridge is a small natural-language business intelligence prototype. A user asks a plain-English question, a constrained intent parser maps it to a fixed read-only SQL template, Flask queries SQLite, and React presents the answer with its interpretation and SQL.

## Architecture

`React → Flask API → intent parser → semantic mapping → safe SQL template → SQLite → result formatter`

The original generic `table1`–`table12` names and sample rows are retained. `query_engine.py` contains a compact `SEMANTIC_SCHEMA` that gives the important physical fields business names.

## Setup

Requirements: Python 3.10+ and Node.js 20+.

```bash
cd insightbridge/backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python setup_db.py
python app.py
```

In a second terminal:

```bash
cd insightbridge/frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The Vite development server proxies `/api` to Flask on port 5000.

Run backend checks with:

```bash
cd insightbridge/backend
python -m unittest -v
```

## Supported questions

- Customers filtered by plan tier and/or state
- Completed revenue grouped by quarter and optionally year
- Top customers by completed transaction revenue
- Customer health filtered by churn risk
- Sales pipeline filtered by stage or open status
- Subscription counts and MRR by plan
- Marketing campaign performance

Examples include “Premium customers in California”, “Show revenue by quarter in 2023”, “Which customers have high or critical churn risk?”, “Show open sales opportunities”, and “Which plans have the most subscriptions?”. Ambiguous wording such as “Show the best customers” returns a clarification instead of guessing.

## SQLite adaptation and source-data notes

`setup_db.py` reads the supplied SQL, removes MySQL `CREATE DATABASE`/`USE`, maps `ENUM` to SQLite `TEXT`, and removes MySQL's `ON UPDATE CURRENT_TIMESTAMP`. It then enables and validates foreign keys. All supplied rows are preserved.

Known source inconsistencies:

- `table8.field3` contains `organic` and `direct_outreach`, values not declared in its MySQL enum.
- `table6.field1` contains `suspended`, which is not declared in its MySQL enum.
- Usage row `usage-019` links `comp-025` to `user-020`, although that user belongs to `comp-019`.
- Transactions `txn-023` through `txn-025` are dated 2023 but appear below the “2024 Transactions” comment.

Because enforcing the original enums would reject supplied rows, SQLite stores enum-like columns as `TEXT`. The application only emits recognized filter values.

## Optional Ollama/Qwen

The deterministic flow works without an LLM. To let unsupported phrasing fall back to local intent classification, start Ollama with `qwen3:1.7b` installed and set:

```bash
set OLLAMA_ENABLED=true
```

On macOS/Linux use `export OLLAMA_ENABLED=true`. Qwen receives the allowed intents and returns structured JSON only; it never writes or executes SQL. Invalid output, unsupported intents, connection errors, and the two-second timeout all fall back safely to the rules parser.

## SQL safety

- Browser input is never treated as SQL.
- Every query comes from a server-side `SELECT` template.
- User-derived values use `?` parameters.
- The database connection uses SQLite read-only mode.
- Results are limited to 100 rows (top customers to 10).
- The data layer rejects non-`SELECT`, multiple statements, and write/schema keywords.
- API errors are generic; stack traces stay in server logs.

## Limitations and future scope

This prototype supports a small set of single-turn intents and fixed business definitions. It does not infer arbitrary metrics or maintain conversation history. Future work could add automatic schema discovery, larger models, a business glossary, follow-up questions, charts, role-based access, caching, audit logs, and an analytical warehouse/read replica for larger datasets.
