# Manim Scene Structure

Write simple, reliable Manim Community scenes that teach through maintained
visual templates and safe template-owned actions.

## Required Shape

- Construct planned templates locally inside each subscene with
  `TemplateClass.build(state="...", ...)`.
- Every template state describes one self-contained visual object. Construct
  the same template class more than once when a comparison needs multiple
  objects or states.
- Do not define lesson snapshot builder functions.
- Use the Equation Template for mathematical expressions, multi-step symbolic
  derivations, and final-formula highlights.
- Keep labels, markers, and annotations grouped inside their owning template.
- Use one template for center layout.
- Use exactly `VGroup(left_template, right_template)` for split layout.
- Execute planned template actions sequentially after the main show or
  transform through `SafeScene.play_action(...)`.

Each `SafeScene.construct()` only shows the title, calls ordered subscene
methods, and fades out. A show subscene clears existing content before showing
its newly constructed templates. A transform subscene preserves existing
content and smoothly replaces the current main content before actions run.

## Reliable Manim Choices

- Prefer maintained templates, stable ManimCE primitives, and safe-scene
  transitions/actions.
- Use diagrams and notation instead of long explanatory text.
- Remove stale content before showing a new idea.
- Avoid advanced camera work, 3D, updaters, plugins, external files, and custom
  choreography unless the lesson clearly requires them.
