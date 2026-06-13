---
name: geometry-shapes-and-labels
description: Derived geometry, labels, angle marks, and compatible figure snapshots
metadata:
  tags: geometry, shapes, polygon, circle, angle, rightangle, labels
---

# Geometry Shapes And Labels

Use standard Manim geometry primitives and derive dependent shapes from their
source geometry. Use `Angle` and `RightAngle` for angle marks.

Place side labels outside segments using a perpendicular outward offset. Place
vertex labels just beyond their vertices. Keep labels compact and avoid covering
the figure.

Return each complete figure as one semantic `VGroup` containing geometry,
labels, markers, and highlights. Across transform snapshots, keep corresponding
parts in stable child order and rebuild labels or markers from the target
geometry.
