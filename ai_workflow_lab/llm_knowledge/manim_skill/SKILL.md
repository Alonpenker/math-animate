# Manim Scene Structure

Write simple, reliable Manim Community scenes that teach through clear visual
snapshots.

## Required Shape

- Build lesson visuals in named functions before scene classes.
- Every builder takes no arguments and returns one fully arranged snapshot
  `VGroup`.
- Keep labels, markers, and annotations grouped with the object they describe.
- Use `.arrange(...)`, `.next_to(...)`, and geometry-derived positions inside
  builders. Layout fitting does not arrange a group's children.
- Keep persistent semantic children in compatible order across snapshots that
  transform into each other.
- Keep one complete visual and explanation snapshot per subscene.
- When a subscene names references, copy and use their validated construction
  and public state patterns instead of rebuilding complex geometry.

Each `SafeScene.construct()` only shows the title, calls ordered subscene
methods, and fades out. A show subscene clears existing content before showing
its snapshot. A transform subscene preserves existing content and smoothly
replaces the current main snapshot.

## Reliable Manim Choices

- Prefer stable ManimCE primitives, `Text`, `MathTex`, `VGroup`, and safe-scene
  whole-group transforms.
- Use diagrams and notation instead of long explanatory text.
- Remove stale content before showing a new idea.
- Preserve continuity across snapshot transforms when objects represent the same
  semantic roles.
- Avoid advanced camera work, 3D, updaters, plugins, external files, and custom
  choreography unless the lesson clearly requires them.
