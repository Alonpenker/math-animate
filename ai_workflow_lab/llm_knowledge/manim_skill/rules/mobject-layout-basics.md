---
name: mobject-layout-basics
description: Core mobject grouping, arrangement, positioning, and bounding-box helpers
metadata:
  tags: mobject, vgroup, group, arrange, positioning, layout
---

# Mobject Layout Basics

Build related objects into groups, arrange them, then position the group.

## Groups

Use `VGroup` for vectorized mobjects and most text/shape/math groupings. Use
`Group` when mixing mobject types that are not all vectorized.

```python
formula = VGroup(eq1, eq2, eq3).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
formula.to_edge(RIGHT, buff=0.6)
```

Move, scale, fade, and transform semantic groups when possible.

## Arrange

Use `arrange` for rows or columns:

```python
steps = VGroup(step1, step2, step3).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
```

Use `arrange_in_grid` for tables, arrays, or repeated diagrams:

```python
tiles = VGroup(*cells).arrange_in_grid(rows=2, cols=3, buff=0.25)
```

## Positioning

Use these methods for layout:

- `next_to(other, direction, buff=...)` for local relationships.
- `move_to(point_or_mobject)` for exact placement.
- `shift(vector)` for intentional offsets.
- `align_to(other, direction)` for columns or baselines.
- `to_edge(direction, buff=...)` and `to_corner(corner, buff=...)` for frame anchoring.

Prefer group placement over moving many children one by one.

## Bounding Boxes

Use bounding-box getters for connections and fit checks:

- `get_width()` and `get_height()`
- `get_center()`
- `get_left()`, `get_right()`, `get_top()`, `get_bottom()`
- `get_corner(UL)`, `get_corner(DR)`, and related corners

```python
arrow = Arrow(source.get_right(), target.get_left(), buff=0.15)
```

Create connectors after final placement, or update/recreate them when targets
move.

## Copies

Use `.copy()` when the same visual source needs to appear in another location.
Do not reuse the same mobject instance in two groups at once.
