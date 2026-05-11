# LLM Knowledge

This directory contains the codebase-owned knowledge used by the LLM pipeline. The markdown and template files here are the source of truth for document content; the database stores only document metadata and embeddings for retrieval.

## Structure

```
llm_knowledge/
├── prompts/
│   ├── PLAN_SYSTEM_PROMPT.md
│   ├── CODEGEN_SYSTEM_PROMPT.md
│   └── CODEGEN_FIX_SYSTEM_PROMPT.md
├── manim_skill/
│   ├── SKILL.md              # Core guidance always injected into codegen
│   ├── rules/                # Optional rule documents retrieved by similarity
│   └── templates/            # Optional code templates retrieved by similarity
├── skill_documents.py        # Registry of every knowledge document
└── README.md
```

## How knowledge is used

Planning uses `prompts/PLAN_SYSTEM_PROMPT.md` directly and sends the teacher request as the user message. It does not retrieve knowledge documents.

Codegen uses `prompts/CODEGEN_SYSTEM_PROMPT.md` with two injected sections:

* Core skill guidance: all registry entries with `priority="core"` are read directly from this folder and inserted into the system prompt.
* Optional candidate documents: the scene plan is embedded, matching `rule`, `template`, and `example` documents are retrieved from the database by vector similarity, and their metadata is listed in the system prompt.

The LLM can then call `load_skill_document(title)` to load the full content of a retrieved candidate by exact title. The tool reads from this folder, not from the database.

Code fixing uses `prompts/CODEGEN_FIX_SYSTEM_PROMPT.md` directly and sends the broken code plus verification error as the user message.

## Registry and seeding

`skill_documents.py` defines the registry with a deterministic UUID, document type, title, category, priority, tags, and relative path for each document.

During worker startup, `seed_knowledge()` reads every registry file, embeds its content, and inserts only metadata plus the embedding into `knowledge_documents`. Existing rows are skipped. If the knowledge table is dropped, the worker can seed it again from this folder.

The database is therefore a retrieval index, not the content store. Updating knowledge content means editing the files in this directory and reseeding the database so embeddings match the new content.

## Manim local environment

To set up a local Manim environment matching the version used by the application (v0.19.2):

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
