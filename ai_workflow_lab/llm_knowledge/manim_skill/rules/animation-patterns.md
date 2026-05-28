---
name: animation-patterns
description: Core Manim animation choices, sequencing, transforms, and timing
metadata:
  tags: animation, animate, create, write, transform, timing, laggedstart
---

# Animation Patterns

Animation should make the mathematical step visible. Choose the simplest motion
that tells the viewer what changed.

## Object Animation

Use `.animate` for direct changes to an existing mobject:

```python
self.play(square.animate.shift(RIGHT).set_color(YELLOW), run_time=0.8)
```

Keep `.animate` calls readable. If a target state is complex, build a target
object and transform to it instead.

## Introduce And Remove

Use the common creation/removal animations deliberately:

- `Create`: draw geometric objects, axes, lines, braces, and outlines.
- `Write`: reveal `Text`, `Tex`, `MathTex`, and compact labels.
- `FadeIn`: introduce existing objects or groups without implying drawing.
- `FadeOut`: remove stale objects and temporary guides.

```python
self.play(Create(axes), Write(label))
self.play(FadeOut(VGroup(label, guide_line)))
```

## Transform Choices

Use `ReplacementTransform(old, new)` when one object replaces another. Use
`TransformFromCopy(source, target)` when the source should remain as evidence.

Use `TransformMatchingTex` for related equations with shared LaTeX terms:

```python
self.play(TransformMatchingTex(eq1, eq2))
```

If terms do not have clear continuity, use `ReplacementTransform`, fade pieces
out/in, or place the new value explicitly.

## Sequencing

Use `LaggedStart` when related animations should cascade, such as revealing a
row of labels or multiple construction marks:

```python
self.play(LaggedStart(*[Write(label) for label in labels], lag_ratio=0.15))
```

Use `Succession` when the order itself matters and each action should finish
before the next begins.

## Timing

Most instructional steps should use `run_time` between `0.5` and `1.5` seconds.
Use longer durations only for transformations the viewer must track.

`rate_func` controls pacing. Keep it simple:

- `smooth`: default readable easing for most animation.
- `linear`: constant-rate motion, useful for trackers or scans.
- `there_and_back`: temporary pulses that return to the original state.

```python
self.play(region.animate(rate_func=there_and_back).set_fill(YELLOW, opacity=0.35))
```

Hold important states with `self.wait(0.3)` to `self.wait(1.0)`. Do not turn
the scene into a transcript of waits; use waits only when comprehension needs a
beat.

## Cleanup

Temporary labels, arrows, highlights, braces, and guide lines should leave once
they stop supporting the current step. Group them so cleanup is one animation:

```python
temporary = VGroup(row_box, col_box, connector)
self.play(FadeOut(temporary))
```
