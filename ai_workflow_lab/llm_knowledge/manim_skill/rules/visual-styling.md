---
name: visual-styling
description: Role-based color, contrast, opacity, fill, stroke, and readable styling
metadata:
  tags: color, styling, contrast, fill, stroke, opacity, background
---

# Visual Styling

Styling should clarify mathematical roles and preserve readability.

## Role-Based Colors

Assign colors by meaning inside a scene:

```python
self.colors = {
    "input": TEAL_B,
    "output": GOLD,
    "result": GREEN_B,
    "guide": GREY_B,
}
```

Use the same color for the same role throughout the scene. Avoid random colors
or coloring many unrelated objects at once.

## Contrast

Choose foreground colors that remain visible on the scene background. If text or
math sits over busy geometry, add a readable backing:

```python
label.add_background_rectangle(color=BLACK, opacity=0.65, buff=0.08)
```

`BackgroundRectangle` is useful for labels over graphs, shaded regions, or dense
diagrams.

## Fill And Stroke

Use `fill_opacity` for areas and `stroke_width` for outlines:

```python
region = Polygon(*points, fill_color=BLUE, fill_opacity=0.25, stroke_width=2)
outline = SurroundingRectangle(answer, color=YELLOW, buff=0.12, stroke_width=4)
```

Filled regions should not hide labels or important construction lines. Lower
opacity when layering multiple shapes.

## Highlights

Use bright or high-contrast colors for temporary focus, final answers, or
critical transitions. Strong yellow emphasis should be rare enough that it means
something when it appears.

Fade or remove highlight objects after the step they explain.

## Gradients

Use gradients sparingly. They are decorative unless the gradient encodes a real
quantity or transition. Prefer flat role colors for reliability and clarity.
