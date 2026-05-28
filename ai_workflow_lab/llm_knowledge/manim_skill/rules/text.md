---
name: text
description: Reliable Text, MarkupText, Paragraph, and MathTex usage in Manim
metadata:
  tags: text, markup, paragraph, mathtex, font-size
---

# Text in Manim

Use text sparingly. Most educational scenes are clearer when text acts as a
title, caption, label, or short mathematical descriptor.

## Choose The Right Object

- `Text`: regular plain text rendered through Pango/Cairo.
- `MarkupText`: text with simple inline styling such as color, bold, or italic.
- `Paragraph`: multiple text lines with consistent alignment and line spacing.
- `MathTex`: mathematical notation and LaTeX expressions.

Do not use `Text` for LaTeX math. Do not use `MathTex` for long prose.

## Basic Usage

```python
title = Text("Quadratic Formula", font_size=40)
caption = Text("Complete the square.", font_size=26, color=GREY_A)
equation = MathTex(r"x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}", font_size=42)
```

Use `MarkupText` only when mixed styling is useful:

```python
note = MarkupText('Area stays <span fgcolor="yellow">constant</span>', font_size=28)
```

Escape markup-sensitive characters as `&lt;`, `&gt;`, and `&amp;`.

## Font Size

Keep text sizes predictable:

- Titles: `font_size=36` to `48`.
- Subtitles and captions: `font_size=22` to `34`.
- Diagram labels: `font_size=24` to `32`.
- Dense explanatory text: rewrite shorter before shrinking below `22`.

Fit wide text before showing it:

```python
if title.get_width() > config.frame_width - 1.0:
    title.scale_to_fit_width(config.frame_width - 1.0)
```

## Concise Text

Prefer short phrases over full sentences inside the frame. If prose needs more
than two compact lines, split the idea into multiple animation steps or move the
explanation into narration.

Group related text and position the group:

```python
title.to_edge(UP, buff=0.35)
caption.to_edge(DOWN, buff=0.4)
```
