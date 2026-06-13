---
name: axes-and-graphing
description: Fixed-axis graph construction and compatible graph snapshots
metadata:
  tags: axes, numberplane, graphing, plot, coordinates, fixed-axes
---

# Axes And Graphing

Treat axes, axis labels, graphs, graph labels, points, and shaded regions as one
semantic plot system.

## Construction

Choose ranges and physical dimensions for the intended region. Use sparse labels
and ticks. Use `NumberPlane` only when the grid supports the explanation.

Use coordinate helpers instead of guessed shifts:

- `axes.c2p(x, y)` for mathematical coordinates.
- `axes.p2c(point)` for scene points.
- `axes.i2gp(x, graph)` for points on a plotted graph.
- `axes.plot(...)` for functions.

Create labels, anchor markers, and annotations from the same axes used to create
the graph.

## Fixed-Axis Transform Snapshots

When a graph should visibly move while axes remain fixed:

- Rebuild identical axes in every snapshot.
- Keep the axes group in the same semantic child slot.
- Put the source and target graphs in the same graph slot.
- Put graph labels and meaningful anchor markers in corresponding stable slots.
- Derive translated graphs and anchor positions from the same mathematical
  transformation.
- Keep the plot panel's overall footprint stable so layout fitting does not move
  the axes between snapshots.

Use a comparison snapshot when both original and transformed graphs must remain
visible. Otherwise keep the reference graph's slot invisible.
