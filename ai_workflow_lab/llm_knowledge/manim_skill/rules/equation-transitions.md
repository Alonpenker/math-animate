---
name: equation-transitions
description: Showing algebraic and symbolic transformations clearly in Manim
metadata:
  tags: equation, algebra, transform, MathTex, derivation, substitution
---

# Equation Transitions

Equation animation should show what changed between two mathematical forms.

## Replace vs Copy

Use a replacement-style transition when the new expression is the next state of
the same mathematical object. The old form should not remain as a separate
persistent object unless it is still being compared.

Use a copy-style transition when the previous expression is evidence or context,
such as building a derivation line by line.

## Preserve Structure

Keep stable parts visually stable when possible:

- Align equals signs or central operators.
- Keep unchanged terms in similar positions.
- Highlight only the term, factor, or side that changes.
- Move derived expressions near their source before settling them into layout.

## Operation Cues

When showing the same operation applied to both sides of an equation, use a
compact visual cue near the equation or sides being changed. The cue should make
the operation visible without becoming the main object.

Do not use operation cues for one-sided rewrites such as substitution, factoring,
expansion, simplification, or cancellation. In those cases, transform the whole
expression or the affected subexpression.

## Common Algebra Scenes

For solving equations, keep the viewer focused on balance:

- Show both sides before applying an operation.
- Emphasize the operation applied to both sides.
- Replace the equation with the simplified result.
- End with the isolated value or final relationship clearly visible.

For substitution or simplification, keep the viewer focused on identity:

- Highlight the part being replaced.
- Transform it into the equivalent form.
- Then show the simplified expression as the next stable state.
