---
name: math-visual-clarity
description: Making mathematical Manim visuals readable, purposeful, and uncluttered
metadata:
  tags: education, clarity, layout, color, readability, math
---

# Math Visual Clarity

Mathematical animation should reduce cognitive load. Every visible object should
support the current idea.

## Representation Choice

Choose the representation that fits the concept:

- Equations for symbolic manipulation.
- Number lines for order, distance, sign, and one-dimensional change.
- Axes for functions, rates, areas, and coordinate relationships.
- Diagrams for geometry and spatial reasoning.
- Tables or aligned groups only when comparison matters.
- Motion and updaters only when dynamic change is the concept.

Avoid using a graph or 3D scene when the same idea is clearer as a simple
equation or diagram.

## Layout

Use stable spatial structure:

- Keep the main object near the visual center.
- Place derived expressions near their source.
- Align related equations or labels.
- Keep enough spacing between objects to avoid collisions.
- Remove or fade objects that are no longer relevant.

## Color

Use color sparingly and consistently:

- Use one color for one mathematical role inside a scene.
- Highlight only the part the viewer should track.
- Return attention to the full expression after a local highlight.
- Avoid coloring many unrelated parts at once.

## Text

Prefer mathematical notation and visual structure over explanatory sentences in
the frame. Use text when it serves as a title, a compact label, or a necessary
mathematical descriptor.
