Write the lesson-specific body of a reliable Manim Community v0.19.2 script.

Return Python code only. The application prepends the authoritative visual-kit
source and every referenced template source, so do not define `Layout`,
`VisualTemplate`, `SafeScene`, or referenced template classes/helpers, and do
not import them. Begin the lesson body with `from manim import *`.

Follow the video plan and code plan exactly:

- Do not define snapshot builder functions.
- Define exactly one `Scene{scene_number}(SafeScene)` class per planned scene.
- `construct()` only shows the title, calls ordered `_subscene_<id>()` methods,
  and ends with `fade_out_all()`.
- Each subscene constructs every planned template locally by calling the
  referenced template class's `build(...)` with the planned parameters and
  assigning it to the planned local name.
- Every template build includes an explicit named `state`.
- For `Layout.CENTER`, pass the one template directly to the main transition.
- For `Layout.SPLIT`, pass exactly
  `VGroup(left_template, right_template)` in planned left-to-right order.
- For `show`, call `clear_content()` before `show_main(...)`.
- For `transform`, omit `clear_content()` and call `transform_main(...)`.
- Pass the planned caption to the main transition helper.
- After the main transition, execute every planned action sequentially as
  `self.play_action(target.action(...))`.
- After all actions, always call `set_bottom_text(...)` with the planned string
  or `None`, then wait long enough for the completed phase to be read.
- Do not use lesson-specific `self.play(...)`; `play_action(...)` is the only
  allowed way to play template-owned animations.
- Use only `Layout.CENTER` and `Layout.SPLIT`.

Use every planned referenced template and its validated build/action contract.
Do not copy, redefine, import, recreate, or approximate referenced complex
geometry.

Make the visible transformations teach the lesson rather than merely presenting
the final result. Preserve every claimed mathematical invariant. Keep visuals
readable and self-contained. Do not use external assets, file I/O, network
access, subprocesses, dynamic execution, plugins, or environment-specific
resources. Allowed lesson-body imports are `manim`, `numpy`, `math`, `colour`,
`scipy`, `random`, `typing`, and `enum`.
