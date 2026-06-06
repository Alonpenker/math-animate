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

Generate a fresh plan, code implementation plan, code, verify/fix, and render:

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
but still runs real static verification, Docker dry-run, and Docker render.

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
  attempts/1/code.py
  attempts/N/code.py
  final/code.py
  logs/
  media/
  summary.json
```

`plan.txt` is the exact plan text passed into code generation. Each attempt and
final `code.py` is standalone: the application prepends the authoritative
`llm_knowledge/manim_skill/visual_kit.py` source to the model-produced lesson
body when saving it.

Attempt numbering is one-based: `attempts/1` is the initial generated code, and
fixes continue with `attempts/2` through the configured maximum attempt
number, currently `5`.

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
fix_attempt_N_usage.json
token_usage.jsonl
token_usage_summary.json
```

When the optional `code_qa` node is wired into an experiment graph, it also
writes `prompts/code_qa_*`, `logs/code_qa_attempt_N.json`, and
`code_qa_attempt_N_usage.json`.

## Workflow Nodes

The normal graph order is:

```text
generate_plan -> load_static_knowledge -> generate_code_plan -> generate_code -> verify -> render
```

`generate_code_plan` turns the educational scene plan into a short ordered list
of snapshot subscenes. Each subscene names one no-argument builder, describes
its complete arranged snapshot, selects `center` or `split`, and chooses `show`
or `transform` as its entry transition. It also records exact selected reference
titles for complex visuals that should use validated template construction.

The model produces only lesson-body code. It defines no-argument snapshot builders that
return fully arranged `VGroup`s and `SafeScene` classes with orchestration-only
`construct()` methods. A show subscene clears and introduces its snapshot; a
transform subscene smoothly replaces the current main snapshot. Generated
lesson bodies must not import `visual_kit`. The application prepends the
authoritative helper source before verification and rendering.

Verification owns syntax, static safety checks, Manim API/runtime errors, and
Docker dry-run behavior. If verification blocks the code, the workflow routes
through `fix_code` and then returns to verification:

```text
fix_code -> verify
```

The `code_qa` node still exists, but the current experiment graph bypasses it so
verified code renders immediately. This keeps the node available for later
workflow comparisons without adding the QA call to this run path.

## What To Edit

- Prompts: `llm_knowledge/prompts/`
- Workflow configuration: `settings.py`
- Workflow order: `workflow.py`
- Node behavior: `nodes/`
- LLM and rendering helpers: `services/`
- Model names, token limits, Docker settings, and attempt limits: `settings.py`
- Knowledge files: `llm_knowledge/manim_skill/`

Runtime shell/layout helpers live in
`llm_knowledge/manim_skill/visual_kit.py`. Topic-specific visuals can be added
as reference templates or examples and registered for static selection. Code
planning and codegen receive the same core documents and statically selected
recommended references. Video planning receives only their plain-language
capability summaries. Fix attempts receive the selected knowledge, compact
visual-kit API contract, and current lesson body, not the full helper source.

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
