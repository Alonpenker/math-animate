---
name: matrix-drawing-patterns
description: Matrix rendering, layout, and highlighting patterns for Manim
metadata:
  tags: matrix, matrices, multiplication, grid, highlight, cells
---

# Matrix Drawing Patterns

Matrices should read as structured mathematical objects. Keep brackets, entries,
labels, and highlights aligned and grouped.

## Built-In First

Prefer `Matrix`/`MobjectMatrix` for standard matrices; use a custom grouped
display only when exact cell geometry, connector lines, or custom highlight
behavior is needed.

```python
m = Matrix([["a", "b"], ["c", "d"]])
self.play(Write(m))
```

For numeric content, pass Python lists of strings or numbers directly. For
custom displays, keep entries, brackets, labels, dimensions, and cell references
in one semantic group or dictionary.

## Rows, Columns, And Cells

Use built-in accessors when using `Matrix`:

```python
m.get_rows()[0].set_color(YELLOW)
m.get_columns()[1].set_color(TEAL)
```

For custom grouped displays, provide helpers such as `cell(matrix, i, j)`,
`row_group(matrix, i)`, and `column_group(matrix, j)` so highlights and
connectors target the actual entry mobjects.

## Fit And Spacing

Scale large matrices before showing them:

```python
if m.get_width() > 5.5:
    m.scale_to_fit_width(5.5)
```

For `A \times B = C` layouts, align matrices horizontally and leave enough
space for operators, result entries, row/column highlights, and connector lines:

```python
eq = VGroup(m_a, times_sign, m_b, equals_sign, m_c).arrange(RIGHT, buff=0.5)
eq.move_to(ORIGIN)
```

## Keep Brackets and Entries Together

Do not animate brackets separately from entries unless teaching bracket
construction. The visible matrix is one object. Animate the whole matrix or the
semantic matrix group with `Write`, `FadeIn`, `Create`, or `ReplacementTransform`.

## Transform Choices

Use matching transforms only when entries have clear visual continuity.
Otherwise use `ReplacementTransform`, `TransformFromCopy`, or explicit value
placement so the viewer can track what changed.

`TransformFromCopy` works well when copying row/column evidence into a formula.
`ReplacementTransform` works well when a placeholder cell becomes its computed
value.

## Multiplication Highlights

During multiplication walkthroughs, highlight one active row, one active column,
and one result cell at a time:

```python
row_box = SurroundingRectangle(m_a.get_rows()[0], color=YELLOW, buff=0.05)
col_box = SurroundingRectangle(m_b.get_columns()[0], color=TEAL, buff=0.05)
cell_box = SurroundingRectangle(m_c.get_entries()[0], color=GREEN, buff=0.08)
self.play(Create(row_box), Create(col_box), Create(cell_box))
```

Use short `DashedLine` connectors only when they clarify which entries form the
current dot product. Fade row, column, cell, and connector highlights before
moving to the next cell.
