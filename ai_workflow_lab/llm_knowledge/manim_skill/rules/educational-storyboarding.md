---
name: educational-storyboarding
description: Structuring Manim scenes as clear educational storyboards
metadata:
  tags: education, storyboard, scene-planning, pedagogy, lesson
---

# Educational Storyboarding

Educational Manim scenes should communicate one idea at a time. The animation is
not just a sequence of effects; it is the visual argument for the concept.

## Scene Focus

Give each scene a single instructional purpose:

- Introduce a representation.
- Transform one expression into another.
- Compare two related objects.
- Show how a quantity changes.
- Reveal why a result follows.

If a scene needs multiple unrelated explanations, split it into multiple scenes.

## Step Design

Each step should make exactly one meaningful visual change:

1. Introduce a new object.
2. Highlight a relevant part.
3. Transform the current form.
4. Move or copy an object to show a relationship.
5. Remove stale context.

Prefer short, ordered steps over a large simultaneous reveal. The viewer should
always know what changed and why it matters.

## Visual Continuity

When one mathematical form becomes another, preserve continuity:

- Use transforms when the new object replaces the old one.
- Use copy-style animations when the old object should remain as evidence.
- Keep related objects near each other.
- Maintain consistent colors for the same concept across the scene.

Avoid teleporting important objects without a visible transition.

## Scene Architecture

Reusable helpers can make a generated scene clearer, but they are guidance, not
a required framework.

Useful patterns include:

- A `setup_*_scene` method for constants, data, and background setup.
- A `self.colors` role map so the same concept keeps the same color.
- Small helpers such as `make_title`, `make_caption`, and `replace_caption`.
- Semantic helper methods for repeated structures, such as graph groups,
  matrix displays, construction marks, or equation rows.
- Grouped cleanup with `FadeOut(VGroup(...))` so stale scene content leaves
  together.

## Final State

End each scene with a visually stable conclusion. The final frame should make the
main takeaway easy to identify without relying on narration.
