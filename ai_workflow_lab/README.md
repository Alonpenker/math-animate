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

Generate a fresh plan, code, verify/fix, and render:

```bash
uv run python run_experiment.py --request inputs/pythagoras_request.txt --name baseline
```

Reuse a saved plan for faster codegen experiments:

```bash
uv run python run_experiment.py --request inputs/pythagoras_request.txt --plan runs/baseline/plan.txt --name codegen-v2
```

Each run writes:

```text
runs/<name>/
  request.txt
  plan.txt
  selected_documents.json
  prompts/
  attempts/0/code.py
  attempts/N/code.py
  final/code.py
  logs/
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
generate_code_usage.json
fix_attempt_N_usage.json
token_usage.jsonl
token_usage_summary.json
```

## What To Edit

- Prompts: `llm_knowledge/prompts/`
- Workflow configuration: `settings.py`
- Workflow order: `workflow.py`
- Node behavior: `nodes/`
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
