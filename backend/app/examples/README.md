# Examples

This directory contains pre-prepared examples and system prompts used by the LLM pipeline.

## Structure

```
examples/
├── plans/                    # Scene plan JSON examples (.txt)
├── code/                     # Corresponding Manim Python examples (.py)
├── index.json                # Document index for the RAG pipeline
├── PLAN_SYSTEM_PROMPT.md     # Planning LLM system prompt (loaded by llm_settings.py)
├── CODEGEN_SYSTEM_PROMPT.md  # Codegen LLM system prompt (loaded by llm_settings.py)
└── README.md                 # This file
```

## How examples are used

The planning LLM call retrieves the top-K most relevant plan examples via vector similarity search (pgvector + `nomic-embed-text`) and injects them into the user query alongside the teacher's request. The codegen call does the same with code examples. System prompts are loaded directly from the `.md` files — no placeholders.

All documents are indexed in `index.json` with a deterministic UUID, a human-readable title, a `doc_type` (`"plan"` or `"code"`), and a relative `file` path.

## How to create a plan example

1. Open `PLAN_SYSTEM_PROMPT.md` and copy its full contents.
2. Paste it into a new ChatGPT conversation as the system prompt (or paste it first in the chat).
3. Send a message describing a math topic, e.g. *"Solving two-step equations with negative coefficients, 1 scene."*
4. Copy the JSON output into a new `.txt` file under `plans/` named after the topic (e.g. `negative_coefficients.txt`).
5. Add an entry to `index.json` with a new UUID, a `"Plan: ..."` title, `"doc_type": "plan"`, and the relative file path.

## How to create a code example

1. Add the plan `.txt` file and `CODEGEN_SYSTEM_PROMPT.md` to your agent context.
2. Prompt: *"Given the instructions and the plan, generate main.py"*
3. Run the render command, review the video, collect issues.
4. Prompt: *"Modify main.py according to these issues: ..."*
5. Repeat until the animation is correct and educational.
6. Final check — prompt: *"Inspect the code and tell me if anything contradicts an instruction in CODEGEN_SYSTEM_PROMPT.md. If so, tell me what to change and why."* Apply any reasonable suggestions to `CODEGEN_SYSTEM_PROMPT.md` before adding the example.
7. Save the final file under `code/` as `<NNN>_<topic>.py` (next sequential index) and add an entry to `index.json`.

## Manim local environment

To set up a local Manim environment matching the version used by the application (v0.19.2):

```bash
winget install Gyan.FFmpeg    # FFmpeg — encode video output
winget install MiKTeX.MiKTeX  # MiKTeX — render math

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
