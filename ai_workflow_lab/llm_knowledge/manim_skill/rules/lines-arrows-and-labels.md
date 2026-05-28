---
name: lines-arrows-and-labels
description: Lines, arrows, braces, connectors, dynamic connections, and label placement
metadata:
  tags: line, arrow, dashedline, brace, curvedarrow, label, connector
---

# Lines, Arrows, And Labels

Connectors should clarify relationships without covering the objects they
connect.

## Basic Connectors

Use the connector that matches the meaning:

- `Line`: neutral segment or construction line.
- `Arrow`: one-way direction or implication.
- `DoubleArrow`: bidirectional relationship or distance between two sides.
- `DashedLine`: temporary guide, projection, or construction helper.
- `Brace`: span, dimension, or grouped quantity label.
- `CurvedArrow`: crowded diagrams or relationships that should arc around content.

```python
connector = Arrow(left.get_right(), right.get_left(), buff=0.15)
guide = DashedLine(point, axes.c2p(point_x, 0), color=GREY_B)
```

## Edge-To-Edge Connections

Connect object edges, not guessed coordinates:

```python
arrow = Arrow(source.get_right(), target.get_left(), buff=0.18)
label = MathTex(r"\times 2", font_size=28).next_to(arrow, UP, buff=0.12)
```

Create arrows after source and target objects are in final position.

## Dynamic Connections

For moving targets, rebuild the connector with `always_redraw`:

```python
arrow = always_redraw(
    lambda: Arrow(source.get_right(), target.get_left(), buff=0.15)
)
```

If the movement is brief and simple, animate the connector with the target group
or recreate it after the movement.

## Label Placement

Labels must not sit on arrow shafts or tips. Offset labels from the connector,
usually perpendicular to its direction:

```python
label.next_to(arrow, UP, buff=0.12)
```

Keep labels short. If an arrow points to a small object, put the label beside
the target or beside the arrow midpoint, not on the tip.

Use curved arrows in crowded diagrams to avoid crossing shafts. Use braces for
side lengths, spans, dimensions, and grouped terms; a brace says "this whole
segment" more clearly than an arrow.

## Cleanup

Temporary arrows, dashed lines, braces, and labels should fade after their
relationship is understood.
