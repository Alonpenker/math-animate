---
name: geometry-shapes-and-labels
description: Geometry primitives, side labels, vertex labels, angle marks, and figure groups
metadata:
  tags: geometry, shapes, polygon, circle, angle, rightangle, labels
---

# Geometry Shapes And Labels

Geometry scenes need stable figures, readable labels, and marks that do not
cover the shape.

## Core Shapes

Use standard primitives first:

```python
circle = Circle(radius=1.2)
square = Square(side_length=2)
rect = Rectangle(width=3, height=1.5)
triangle = Polygon(A, B, C)
pentagon = RegularPolygon(n=5)
point = Dot(A)
```

Special shapes such as stars, annuli, sectors, and polygrams are available, but
use them only when the topic needs them.

## Angles

Use `Angle` and `RightAngle` for angle marks:

```python
angle = Angle(Line(B, A), Line(B, C), radius=0.35)
right = RightAngle(Line(A, B), Line(C, B), length=0.25)
```

Place angle labels outside the mark when possible and keep them compact.

## Side Labels

Side and vertex labels should usually use `font_size=28` to `32`. Place side
labels outside the polygon, offset perpendicular to the side. For vector math
snippets like this, include `import numpy as np` in the scene file:

```python
mid = (A + B) / 2
side_vec = B - A
normal = np.array([-side_vec[1], side_vec[0], 0])
normal = normal / np.linalg.norm(normal)
label = MathTex("a", font_size=30).move_to(mid + 0.28 * normal)
```

If the normal points inward, multiply it by `-1` or choose `next_to(side, ...)`
with a direction that keeps the label outside the figure.

## Vertex Labels

Place vertex labels just outside the polygon:

```python
center = polygon.get_center()
for vertex, name in zip(polygon.get_vertices(), ["A", "B", "C"]):
    direction = vertex - center
    direction = direction / np.linalg.norm(direction)
    label = MathTex(name, font_size=30).move_to(vertex + 0.25 * direction)
```

Do not put vertex labels directly on vertices; use a small outward offset.

## Group Figures

Group the figure with its labels and marks:

```python
figure = VGroup(triangle, side_labels, vertex_labels, angle_marks)
figure.move_to(ORIGIN)
```

Move or scale the group as a unit. Fade temporary construction marks once they
are no longer needed.
