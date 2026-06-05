# Visual Kit API

Generated Manim code must import Manim and the copied runtime:

```python
from manim import *
from visual_kit import *
```

Every renderable scene class must inherit `SafeScene`:

```python
class Scene1(SafeScene):
    def construct(self):
        self.show_title("Lesson title")
```

`visual_kit.py` is a small scene shell and layout runtime. It is not a topic
library. Lesson-specific diagrams, graphs, proofs, tables, simulations, and
formula systems belong inline in generated `code.py`, guided by selected
template context when useful.

## Public API

Use only these runtime helpers:

- `fit_to_region(mobject, region, buff=0.0)`
- `self.show_title(text)`
- `self.set_bottom_text(text)`
- `self.clear_subscene()`
- `self.fade_out_all()`
- `self.show_center(content)`
- `self.show_center_with_caption(content, caption)`
- `self.show_left_right(left, right)`
- `self.show_stack(items)`
- `self.transform_center(content)`
- `self.transform_center_with_caption(content, caption)`
- `self.transform_left_right(left, right)`
- `self.transform_stack(items)`

`SafeScene` owns the title, main, left-main, right-main, and bottom regions.
Layout methods fit content into those regions, animate it in, and register the
main visual for later cleanup or transform.

## Usage Pattern

Start each scene with `show_title`. For each subscene, build one clear Manim
object or group for the current idea, then show it with one visual-kit layout
method.

Use `clear_subscene()` when moving to a new idea that should remove both the
current main visual and its bottom text. Use `set_bottom_text()` only for short
one-line comments or conclusions.

For continuity, first display the source content with a `show_*` method. Then
build the target content and use the matching `transform_*` method.

Do not animate the same main object immediately after a `show_*` call; the
layout method already animates it.
Do not use `self.add(...)` to keep unmanaged background copies; include visible
continuity content in the single group passed to a visual-kit method.

## Reference Templates

Selected templates are prompt context. Generated code cannot import template
modules or assume template files exist beside `code.py`.

When a selected template is relevant, copy the useful construction pattern
inline into generated `code.py`. If a template exposes a public builder, follow
that builder's structure and preserve the mathematical relationships it encodes.
Treat complex template builder outputs as one validated main visual; do not
split, rebuild, restyle, mark, or move their children unless the template
documents that as a public option.
