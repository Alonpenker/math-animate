# LLM Knowledge

This directory contains the codebase-owned knowledge used by the LLM pipeline.
The markdown and template files here are the source of truth for document
content. In this standalone lab, document selection is deterministic and static;
the production application can use the same registry with real retrieval.

## Structure

```
llm_knowledge/
├── prompts/
│   ├── PLAN_SYSTEM_PROMPT.md
│   ├── CODEGEN_SYSTEM_PROMPT.md
│   └── CODEGEN_FIX_SYSTEM_PROMPT.md
├── manim_skill/
│   ├── SKILL.md              # Core guidance always injected into codegen
│   ├── visual_kit.py         # Shell/layout runtime copied beside code.py
│   ├── rules/                # Optional rule documents selected per request
│   └── templates/            # Optional code templates selected per request
├── skill_documents.py        # Registry of every knowledge document
└── README.md
```

## How knowledge is used

Planning uses `prompts/PLAN_SYSTEM_PROMPT.md` directly and sends the teacher request as the user message. It does not retrieve knowledge documents.

Codegen uses `prompts/CODEGEN_SYSTEM_PROMPT.md` with knowledge passed as separate context:

* Core skill guidance: all registry entries with `priority="core"` are read directly from this folder and sent with every codegen request.
* Optional selected documents: the lab uses static keyword profiles to choose
  matching `rule`, `template`, and `example` documents. Selected document
  contents are sent with the codegen request.

The document selection step chooses exact titles from the registry. Document
contents are read from this folder.

Code fixing uses `prompts/CODEGEN_FIX_SYSTEM_PROMPT.md` directly and sends the broken code plus verification error as the user message.

`manim_skill/visual_kit.py` is runtime code, not just prompt context. The
workflow copies it beside every generated attempt and final `code.py`, and
generated code imports it with `from visual_kit import *`. It is intentionally
limited to scene shell, fixed regions, cleanup, and layout methods. Topic
content belongs in generated `code.py`, guided by reference templates from
`manim_skill/templates/`. The matching LLM API documentation lives in
`manim_skill/rules/visual-kit-api.md`. Reference templates are not copied beside
generated code; codegen should copy the useful construction helpers inline when
the code plan names them.

## Registry and seeding

`skill_documents.py` defines the registry with a deterministic UUID, document type, title, category, priority, tags, and relative path for each document.

The standalone lab does not seed a database or embeddings. When this knowledge is
used by the production application, the database should be treated as a
retrieval index, not the content store. Updating knowledge content means editing
the files in this directory and reseeding embeddings in the production
environment so retrieval matches the new content.

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
