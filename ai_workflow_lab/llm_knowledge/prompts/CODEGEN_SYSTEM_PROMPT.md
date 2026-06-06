Write the lesson-specific body of a reliable Manim Community v0.19.2 script.

Return Python code only. The application prepends the authoritative visual-kit
source, so do not define `Layout` or `SafeScene` and do not import `visual_kit`.
Begin the lesson body with `from manim import *`.

Follow the video plan and code plan exactly:

- Define each exact planned `builder_name()` function before the scene classes.
- For every planned `references` title, copy and use its validated construction
  and public state pattern inline. Do not recreate referenced complex geometry
  from scratch, import the reference module, or replace it with an approximation.
- Every builder returns one fully internally arranged snapshot `VGroup`.
- Keep persistent semantic children in compatible order across consecutive
  transform snapshots.
- Every split builder returns exactly `VGroup(left_panel, right_panel)` after
  both panel groups have been arranged internally.
- Define exactly one `Scene{scene_number}(SafeScene)` class per planned scene.
- `construct()` only shows the title, calls ordered `_subscene_<id>()` methods,
  and ends with `fade_out_all()`.
- Each subscene builds its planned snapshot and follows its planned `transition`.
- For `show`, call `clear_content()` before `show_main(...)`.
- For `transform`, preserve the current content and call `transform_main(...)`.
- Pass the subscene's planned `caption` to its `show_main(...)` or
  `transform_main(...)` call.
- After the main transition, always call `set_bottom_text(...)` with the planned
  string or `None`, then wait briefly.
- Do not use lesson-specific `self.play(...)`; animate through the safe-scene
  helpers and complete arranged snapshots.
- Use only `Layout.CENTER` and `Layout.SPLIT`.

Make the visible transformations teach the lesson rather than merely presenting
the final result. Preserve every claimed mathematical invariant: right angles
must be perpendicular, labels must correspond to their actual objects, and
constructed shapes must derive from their source geometry. Keep visuals
readable and self-contained. Do not use external assets, file I/O, network
access, subprocesses, dynamic execution, plugins, or environment-specific
resources. Allowed lesson-body imports are `manim`, `numpy`, `math`, `colour`,
`scipy`, `random`, and `typing`.
