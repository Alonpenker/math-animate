---
name: latex
description: Reliable MathTex and Tex construction for snapshots
metadata:
  tags: latex, mathtex, tex, equation, formula, math
---

# LaTeX In Manim

Use `MathTex` for mathematical notation and `Tex` only when mixed text and math
are genuinely useful. Prefer raw strings and simple, reliable LaTeX.

Use separate `MathTex` arguments when terms need distinct colors or stable
semantic grouping. Use `set_color_by_tex(...)` for repeated symbols when
appropriate. Arrange related equations into one internally arranged `VGroup`.

Across transform snapshots, keep related formulas at compatible scale and
position. Avoid custom packages, debug labels, and fragile direct glyph indexing
unless the selected template requires them.
