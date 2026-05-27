---
name: axes-and-graphing
description: Axes, NumberPlane, coordinate conversion, plotting, labels, and moving points
metadata:
  tags: axes, numberplane, graphing, plot, c2p, p2c, moving-point
---

# Axes And Graphing

Treat axes, graphs, labels, points, and shaded regions as one plot group.

## Axes And NumberPlane

Set ranges and physical size for the intended region:

```python
axes = Axes(
    x_range=[-3, 3, 1],
    y_range=[-2, 6, 2],
    x_length=6,
    y_length=4,
    tips=False,
)
axes.to_edge(LEFT, buff=0.7)
```

Use `NumberPlane` when the grid itself supports the explanation. Keep labels
sparse; dense tick labels collide with graph annotations.

Complex planes are specialized `NumberPlane` use; retrieve or write that pattern
only when the lesson is explicitly about complex numbers.

## Coordinates

Use coordinate helpers instead of guessing with shifts:

- `axes.c2p(x, y)` converts coordinates to scene points.
- `axes.p2c(point)` converts scene points back to coordinates.
- `axes.i2gp(x, graph)` gets a point on a plotted graph.

```python
dot = Dot(axes.c2p(2, 4), color=YELLOW)
```

## Plotting

Use `axes.plot` for functions:

```python
graph = axes.plot(lambda x: x**2, x_range=[-2, 2], color=TEAL)
label = axes.get_graph_label(graph, label="x^2", x_val=1.5, direction=UR)
self.play(Create(axes), Create(graph), Write(label))
```

Add graph labels after the axes and graph are positioned.

## Moving Point Pattern

Use `ValueTracker` with `always_redraw` for a point that follows a graph:

```python
t = ValueTracker(-2)
dot = always_redraw(lambda: Dot(axes.i2gp(t.get_value(), graph), color=YELLOW))
label = always_redraw(lambda: MathTex("x").next_to(dot, UP, buff=0.12))
self.add(dot, label)
self.play(t.animate.set_value(2), run_time=3, rate_func=linear)
```

Keep moving labels offset from the point so they do not sit on the graph line.

## Layout

Build `plot_group = VGroup(axes, graph, labels, dots, shaded_regions)` and fit
or move it as a unit. If an equation or diagram appears beside the plot, reserve
a separate region before creating labels and callouts.
