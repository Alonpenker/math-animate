# AI Workflow Lab

This document describes the current AI-facing workflow that turns a teacher
request into standalone Manim scene files. It focuses on what each model sees,
what each step must produce, and how the final code is structured.

## Workflow

```text
teacher request
    |
    v
generate_plan
    |
    v
load_static_knowledge
    |
    v
generate_code_plan
    |
    v
generate_code
    |
    v
verify ---- failure ----> fix_code ----> verify
    |
    v
render
```

`code_qa` exists but is not connected to the current graph.

## AI Context

| Step | System prompt | Request | Video plan | Code plan | Fixed knowledge | Topic reference | Current lesson body | Failure |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `generate_plan` | Plan prompt | Yes | No | No | Human-facing capabilities | No implementation references | No | No |
| `generate_code_plan` | Code-plan prompt | Yes | Yes | No | Core documents | Selected relevant set | No | No |
| `generate_code` | Codegen prompt | No | Yes | Yes | Core documents | Selected relevant set | No | No |
| `fix_code` | Fix prompt | Yes | Yes | Yes | Core documents and visual-kit API | Selected relevant set | Yes | Yes |

The two core documents shared by code planning and codegen are:

- `manim_skill/SKILL.md`: concise scene and builder structure.
- `manim_skill/rules/visual-kit-api.md`: concise safe-scene API contract.

Static selection uses the request and video plan. General recommended documents
are always included, then the first matching topic profile contributes its full
ordered set of specialized rules, templates, or examples.

Before video planning, the same request-based selection exposes only plain
language capability summaries. The video planner never sees reference titles,
template source, function names, or APIs.

## Step Contracts

### Generate Plan

**Goal:** produce a grounded, human-readable educational video plan.

**Input:** plan system prompt, raw teacher request, and relevant human-facing
validated visual capabilities.

**Output:** structured `VideoPlan`.

```json
{
  "scenes": [
    {
      "scene_number": 1,
      "learning_objective": "What this scene teaches",
      "visual_storyboard": "A short numbered sequence of readable visual phases",
      "voice_notes": "Natural narration in the same order"
    }
  ]
}
```

The storyboard describes what the viewer sees. Each scene establishes its idea,
develops it through meaningful visible changes, and visually earns its
conclusion without discussing code or Manim APIs.

### Load Static Knowledge

**Goal:** prepare the shared Manim knowledge bundle used by code planning and
code generation.

**Input:** teacher request, serialized video plan, and the static document
registry.

**Output:** compact core knowledge plus the statically selected relevant
document set. Selected document metadata is saved to `selected_documents.json`.

### Generate Code Plan

**Goal:** map the video-plan phases to a short implementation contract.

**Input:** code-plan system prompt, teacher request, video plan, and the same
Manim knowledge bundle later used by code generation.

**Output:** structured `CodePlan`.

```json
{
  "scenes": [
    {
      "scene_number": 1,
      "scene_title": "Scene title",
      "subscenes": [
        {
          "id": "main_diagram",
          "purpose": "What this snapshot teaches",
          "builder_name": "build_main_diagram",
          "builder_shape": "Describe the visible objects, semantic groups, and internal arrangement",
          "layout": "center",
          "transition": "show",
          "references": ["Exact Selected Template Title"],
          "caption": null,
          "bottom_text": "Optional short takeaway"
        }
      ]
    }
  ]
}
```

Each no-argument builder returns one complete, internally arranged snapshot
`VGroup`. Each subscene chooses `show` to clear and introduce its snapshot or
`transform` to smoothly replace the current main snapshot. Layouts are only
`center` and `split`; every split builder returns
`VGroup(left_panel, right_panel)`. Validation only warns about missing,
duplicate, or extra scene numbers and a scene whose first subscene transforms.

`references` contains exact loaded template or example titles. When a reference
provides a required complex visual, codegen copies and uses its validated
construction and state pattern instead of recreating the geometry.

### Generate Code

**Goal:** produce the lesson-specific body of the Manim script.

**Input:** codegen system prompt, video plan, code plan, and the shared Manim
knowledge bundle.

**Output:** Python lesson body only. It starts with `from manim import *`, does
not import `visual_kit`, and does not define `Layout` or `SafeScene`.

Required structure:

```python
from manim import *


def build_initial_diagram() -> VGroup:
    return arranged_initial_group


def build_developed_diagram() -> VGroup:
    return arranged_developed_group


class Scene1(SafeScene):
    def construct(self):
        self.show_title("Scene title")
        self._subscene_initial_diagram()
        self._subscene_developed_diagram()
        self.fade_out_all()

    def _subscene_initial_diagram(self):
        self.clear_content()
        self.show_main(build_initial_diagram(), layout=Layout.CENTER)
        self.set_bottom_text(None)
        self.wait(1)

    def _subscene_developed_diagram(self):
        self.transform_main(build_developed_diagram(), layout=Layout.CENTER)
        self.set_bottom_text("Optional short takeaway")
        self.wait(2)
```

Every builder returns one fully internally arranged snapshot `VGroup`.
`construct()` only orchestrates ordered subscene methods. Subscenes use safe
whole-group show or transform transitions and do not call lesson-specific
`self.play(...)`. Every subscene applies its planned bottom text, including
`None` to clear previous text.

### Assemble Standalone Code

`llm_knowledge/manim_skill/visual_kit.py` is the authoritative maintained helper
source. Models never reproduce or import it.

When an attempt or final artifact is saved, the application prepends the exact
helper source to the lesson body. The result is one standalone `code.py` that
can be rendered without a neighboring helper module.

### Verify

**Goal:** reject unsafe or non-renderable lesson bodies.

**Checks:**

1. Parse the lesson body with Python AST.
2. Reject forbidden imports, including `visual_kit`.
3. Reject dangerous builtin calls.
4. Require renderable `Scene<number>` classes to inherit `SafeScene`.
5. Save the assembled standalone file and run Docker Manim dry-run.

Verification checks execution safety and runtime behavior, not rendered-frame
composition.

### Fix Code

**Goal:** repair a failed lesson body while preserving the plans and structure.

**Input:** fix prompt, failure, request, video plan, code plan, compact
visual-kit API, shared core and selected knowledge, and current lesson body.

**Output:** complete corrected lesson body only. The fixer repairs every
occurrence of the reported root-cause pattern while preserving mathematical
invariants and referenced template constructions. The application assembles it
with the authoritative helper before the next verification attempt.

### Render

**Goal:** render every planned scene from the verified standalone script.

**Output:** final standalone `code.py`, MP4 files, logs, and run summary.

## Run Artifacts

```text
runs/<name>/
  request.txt
  plan.txt
  code_plan.json
  selected_documents.json
  prompts/
  attempts/<attempt>/code.py
  final/code.py
  logs/
  media/
  summary.json
```

Archived prompts record the exact AI context used in each run. Every saved
attempt and final `code.py` is already assembled as a standalone file.
