# Isolated AI Workflow Lab

Standalone uv project for iterating on the Manim AI workflow without the main
application stack. It keeps a lightweight LangChain + LangGraph workflow, uses
local copied prompts and skill knowledge, writes all artifacts to local run
folders, and renders with the Manim Docker image.

## Setup

```bash
cd ai_workflow_lab
uv sync
cp .env.example .env
```

Set `OPENROUTER_API_KEY` in `.env` or export it in your shell.

## Run

Generate a fresh plan, code implementation plan, code, verify/fix, one visual QA
review, and render:

```bash
uv run python run_experiment.py --request inputs/pythagoras_request.txt --name baseline
```

Reuse a saved plan for faster codegen experiments:

```bash
uv run python run_experiment.py --request inputs/pythagoras_request.txt --plan runs/baseline/plan.txt --name codegen-v2
```

Run the local end-to-end workflow without real API calls:

```bash
uv run python run_experiment.py --e2e
```

E2E mode always overwrites `runs/e2e`. It uses deterministic fake LLM responses,
including a fake code QA pass after verification succeeds, but still runs real
static verification, Docker dry-run, and Docker render.

Each run writes:

```text
runs/<name>/
  request.txt
  plan.txt
  code_plan.json
  selected_documents.json
  prompts/
  prompts/generate_code_plan_system.md
  prompts/generate_code_plan_user.txt
  prompts/code_qa_system.md
  prompts/code_qa_attempt_N_user.txt
  attempts/0/code.py
  attempts/N/code.py
  final/code.py
  logs/
  logs/code_qa_attempt_N.json
  media/
  summary.json
```

`plan.txt` is the exact plan text passed into code generation.

## Logs And Token Usage

The workflow prints progress to stdout while it runs. The same lines are written
to:

```text
runs/<name>/logs/workflow.log
```

Each LLM call logs its model, duration, input tokens, reasoning tokens, output
tokens, total tokens, and cumulative total tokens so far. Token files are saved
under `runs/<name>/logs/`:

```text
generate_plan_usage.json
generate_code_plan_usage.json
generate_code_usage.json
code_qa_attempt_N_usage.json
fix_attempt_N_usage.json
token_usage.jsonl
token_usage_summary.json
```

## Workflow Nodes

The normal graph order is:

```text
generate_plan -> load_static_knowledge -> generate_code_plan -> generate_code -> verify -> code_qa -> render
```

`generate_code_plan` turns the educational scene plan into an implementation
blueprint for codegen: subscene staging, visual blocks, layout regions, text
budgets, animation beats, helper contracts, and cleanup lists. It is upstream
planning, not defect detection.

Verification owns syntax, static safety checks, Manim API/runtime errors, and
Docker dry-run behavior. If verification blocks the code, the workflow routes
through `fix_code` and then returns to verification:

```text
fix_code -> verify
```

After code passes verification, `code_qa` runs at most once. It is downstream
defect detection. It uses
`llm_knowledge/prompts/CODE_QA_SYSTEM_PROMPT.md` to review verified Manim code
for high-confidence code-visible visual defects such as detached semantic
groups, stale labels after movement, fake square-on-side geometry, unreadable
contrast, and missing `VGroup` tracking for major objects. Warning-only reports
continue to render. Blocker reports are written to `logs/code_qa_attempt_N.json`
and sent to `fix_code`; after that QA is skipped and the normal fix/verify loop
continues until render or failure.

## What To Edit

- Prompts: `llm_knowledge/prompts/`
- Workflow configuration: `settings.py`
- Workflow order: `workflow.py`
- Node behavior: `nodes/`
- LLM and rendering helpers: `services/`
- Model names, token limits, Docker settings, and fix attempts: `settings.py`
- Knowledge files: `llm_knowledge/manim_skill/`

There is no DB, Redis, Celery, MinIO, Docker Compose, RAG, or embedding service
in this lab.

## Docker Rendering

The lab uses:

```text
manimcommunity/manim:v0.19.2
```

Docker dry-run happens during verification. Final MP4s are written under the
run folder's `media/` directory.

## Manim Local Environment

To set up a local Manim environment matching the version used by the application
(v0.19.2):

```bash
winget install Gyan.FFmpeg    # FFmpeg - encode video output
winget install MiKTeX.MiKTeX  # MiKTeX - render math

mkdir manim-playground && cd manim-playground
uv init --python 3.11
uv add "manim==0.19.2"
```

Render all scenes in a file:

```bash
uv run manim -ql -a main.py
```

Render a specific scene:

```bash
uv run manim -ql main.py YourScene
```
