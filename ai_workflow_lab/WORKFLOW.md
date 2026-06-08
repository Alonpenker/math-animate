Doe# AI Workflow Lab

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

- `manim_skill/SKILL.md`: concise scene and template structure.
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
          "purpose": "What this phase teaches",
          "layout": "center",
          "transition": "show",
          "templates": [
            {
              "name": "equation",
              "reference": "Equation Template",
              "parameters": {"state": "display", "expression": "a^2+b^2=c^2"}
            }
          ],
          "actions": [
            {
              "target": "equation",
              "action": "set_expression",
              "parameters": {"expression": "c^2=a^2+b^2"}
            }
          ],
          "caption": null,
          "bottom_text": "Optional short takeaway"
        }
      ]
    }
  ]
}
```

Each subscene constructs its named templates locally, chooses `show` to clear
and introduce them or `transform` to smoothly replace the current main content,
then executes optional actions sequentially. Center uses one template. Split
uses exactly `VGroup(left_template, right_template)` in planned order. Template
names are unique within a subscene and action targets must match them.

`templates[].reference` contains exact loaded template titles. Referenced
templates are prepended authoritatively, and codegen calls their public
`build(...)` and safe action methods instead of copying or recreating geometry.

### Generate Code

**Goal:** produce the lesson-specific body of the Manim script.

**Input:** codegen system prompt, video plan, code plan, and the shared Manim
knowledge bundle.

**Output:** Python lesson body only. It starts with `from manim import *`, does
not import `visual_kit`, and does not define `Layout` or `SafeScene`.

Required structure:

```python
from manim import *


class Scene1(SafeScene):
    def construct(self):
        self.show_title("Scene title")
        self._subscene_initial_diagram()
        self._subscene_developed_diagram()
        self.fade_out_all()

    def _subscene_initial_diagram(self):
        self.clear_content()
        equation = EquationTemplate.build(state="display", expression=r"a^2+b^2=c^2")
        self.show_main(equation, layout=Layout.CENTER)
        self.set_bottom_text(None)
        self.wait(1)

    def _subscene_developed_diagram(self):
        equation = EquationTemplate.build(state="display", expression=r"c^2=a^2+b^2")
        self.transform_main(equation, layout=Layout.CENTER)
        self.play_action(equation.set_expression(expression=r"c=\sqrt{a^2+b^2}"))
        self.set_bottom_text("Optional short takeaway")
        self.wait(2)
```

`construct()` only orchestrates ordered subscene methods. Each subscene builds
its planned templates locally, uses the planned safe whole-group show or
transform transition, then executes actions sequentially through
`play_action(...)`. Every subscene applies its planned bottom text, including
`None` to clear previous text.

### Assemble Standalone Code

`llm_knowledge/manim_skill/visual_kit.py` and code-plan-referenced templates are
authoritative maintained helper sources. Models never reproduce or import them.

When an attempt or final artifact is saved, the application prepends the visual
kit followed by each uniquely referenced template in first-use order. The
result is one standalone `code.py` that can be rendered without neighboring
helper modules.

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
invariants, local template construction, and ordered safe actions. The
application assembles it with the authoritative helpers before the next
verification attempt.

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
