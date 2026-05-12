---
name: layout-composition
description: Frame-safe composition patterns for readable Manim scenes
metadata:
  tags: layout, composition, frame, positioning, readability, overlap, offscreen
---

# Layout Composition

Manim scenes must stay readable inside the frame. Layout is part of the
mathematical explanation, not a cleanup step after objects are created.

## Hard Contract

Plan the screen before placing objects.

Every major visible object must belong to a deliberate region before it is
animated onto the screen. Major objects include equations, derivation groups,
axes, graphs, diagrams, tables, large labels, and explanatory blocks.

For each scene:

1. Choose the active regions.
2. Build related objects into semantic groups.
3. Fit each group inside its region.
4. Animate the fitted groups.
5. Remove, replace, or compress stale groups before adding more.

Do not create a long visual transcript. If a scene needs many steps, transform
the current content, replace it with a compact summary, or fade stale content.

## Regions

Use a small number of stable regions:

- Top: title or compact context.
- Center: primary equation, graph, or diagram.
- Left/right split: algebra on one side, visual representation on the other.
- Bottom: short takeaway, final result, or transient annotation.

Use only as many regions as the current idea needs. Empty space is useful when it
keeps the main object readable.

## Group-First Layout

Build related objects into a `VGroup` or `Group` before final positioning.
Use `arrange`, `align_to`, and group placement for related content.

Avoid using repeated `next_to(..., DOWN)` calls as the main layout engine for
major content. That pattern often pushes objects offscreen.

Use `next_to` for local relationships: labels beside shapes, braces beside
segments, arrows between nearby objects, and short temporary callouts.

After a group is arranged and positioned, move the group as a unit. Avoid moving
individual children later unless the animation specifically teaches that local
movement.

## Fit Before Showing

Do not animate a large object or group onto the screen before it fits.

Build the object, arrange it, scale it if needed, place it in its region, then
animate its appearance. Use `get_width`, `get_height`,
`scale_to_fit_width`, and `scale_to_fit_height` to reason about fit.

If fitting would make text or math too small to read, remove content or split the
idea into another scene instead of shrinking everything.

No major object should be created, moved, or animated to a position where part of
it is outside the frame unless that offscreen motion is intentional and brief.

## Visibility Budget

The screen should show only:

- The current main idea.
- A small amount of useful reference context.
- Active labels, arrows, braces, or highlights needed for the current action.

If adding a new major object would crowd the frame, first remove, transform, or
compress older content. Avoid keeping complete derivation history visible unless
the comparison itself is the point.

Temporary labels, arrows, highlights, braces, and notes should usually fade out
after they stop supporting the current step. Group temporary objects so they can
be removed together.

## Overlap Discipline

Objects must not cover unrelated objects. Equations, diagrams, labels, braces,
arrows, and highlights need visible spacing.

When equations and diagrams appear together, reserve separate regions for them.
For symbolic sequences, align equations and keep only useful history. For visual
diagrams, keep the main construction near the center and move explanatory text
to the side or bottom.

## Labels, Arrows, and Callouts

Labels and arrows must be attached to visible targets and should not cover the
main object. Use short labels and enough buffer to avoid overlap.

On-screen text should be concise. Prefer short phrases over full explanatory
sentences; leave longer explanations for narration. Any title, takeaway, or
caption must be fitted to its region before display. For longer text, reduce
font size, split into two short lines, or rewrite it shorter. Never let text
extend beyond the frame edges.

If an arrow points between two objects, use actual object points such as
`get_left`, `get_right`, `get_top`, `get_bottom`, or `get_center`.

Create arrows and markers after the target objects have reached their final
positions. Do not calculate an arrow endpoint, then move the target object and
reuse the old endpoint.

For axes, graphs, and coordinate diagrams, attach markers with `axes.c2p(...)`
or graph helper methods. Do not guess graph positions with manual `shift` values
when coordinate conversion exists.

For moving targets, recreate or update the marker after the movement, or animate
the marker together with the target group.

## Axes, Graphs, and Large Objects

Axes, number planes, graphs, plotted points, shaded areas, tangent lines, graph
labels, and coordinate markers should be treated as one plot group.

Choose the plot region before creating the axes. Set `x_length` and `y_length`
for that region instead of relying on default full-frame axes. Keep tick labels
and axis numbers sparse; too many labels can crowd the plot and collide with
annotations.

Add labels, dots, arrows, and highlighted regions after the axes are placed, so
their positions match the final coordinate system.

Large formulas, diagrams, graphs, and tables must be scaled or simplified before
they are shown. If a single object dominates the frame, reserve the center for it
and keep all labels short and local.

## Movement Discipline

Avoid cumulative layout drift.

Do not build a scene with repeated manual `shift` calls or long chains of
relative placement for major content. Prefer:

- `VGroup(...).arrange(...)` for related items.
- `move_to(...)`, `to_edge(...)`, or `to_corner(...)` for group placement.
- `align_to(...)` for equation columns or label columns.
- Moving semantic groups instead of moving each child separately.

When an object needs to move for the lesson, move it from one clear region to
another. Move or remove supporting labels, arrows, and highlights with it.

## Scene Ending

End each scene with a readable final composition that fits inside the frame.
Hold that composition briefly so the viewer can understand the result.

Then fade out the visible scene content as a group and wait about one second,
unless the next scene intentionally requires hard visual continuity.

## Best Practices

1. Plan regions before positioning individual objects.
2. Use groups and `arrange` for related content.
3. Fit groups before showing them.
4. Avoid long `next_to(..., DOWN)` chains for major scene steps.
5. Remove, transform, or compress stale content before adding more.
6. Keep labels and arrows local, short, attached, and temporary.
7. Keep text concise and fit it to its region before showing it.
8. Treat axes, graphs, and annotations as one plot group.
9. Move semantic groups rather than drifting individual objects.
10. Hold the final composition, then fade out visible content and wait.
