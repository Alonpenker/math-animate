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
│   ├── SKILL.md              # Core guidance shared by code planning and codegen
│   ├── visual_kit.py         # Authoritative helper prepended to code.py
│   ├── rules/                # Optional rule documents selected per request
│   └── templates/            # Optional code templates selected per request
├── skill_documents.py        # Registry of every knowledge document
└── README.md
```

## How knowledge is used

Planning uses `prompts/PLAN_SYSTEM_PROMPT.md` directly and sends the teacher
request as the user message. It does not receive knowledge-document contents.
For matching templates, it receives only their plain-language
`planning_capability` summaries, never template titles or source.

After planning, the lab loads one shared Manim knowledge bundle:

* Compact core documents for scene structure and the visual-kit API.
* General recommended documents configured for every request.
* The full ordered document set from the first matching static topic profile.

Code planning receives its prompt, the teacher request, the video plan, and this
knowledge bundle. Codegen receives its prompt, both plans, and the same bundle.
This lets the implementation plan use available Manim patterns and references
before code is written.

Each code-plan subscene records matching exact titles in
`templates[].reference`. Codegen and fixing construct those templates locally
and preserve their build/action contracts instead of copying or recreating
complex geometry.

The document selection step chooses exact titles from the registry. Document
contents are read from this folder.

Code fixing uses `prompts/CODEGEN_FIX_SYSTEM_PROMPT.md` directly and sends the
broken code plus verification error as the user message. It also receives the
same core and selected knowledge messages used by code planning and codegen.

`manim_skill/visual_kit.py` is the authoritative helper source. Models produce
only lesson-body code and never import or reproduce the helper. The application
prepends the exact source plus every template referenced by the code plan to
every attempt and final `code.py`, producing one standalone renderable script.
Templates are `VisualTemplate` groups with maintained `build(...)` contracts
and optional safe actions. Subscenes own center/split composition. The matching
compact API contract lives in `manim_skill/rules/visual-kit-api.md`.

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
