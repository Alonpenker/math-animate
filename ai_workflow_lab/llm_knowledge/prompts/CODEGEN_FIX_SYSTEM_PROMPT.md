Fix the lesson-specific body of a Manim Community v0.19.2 script.

Return only the complete corrected lesson body. The application prepends the
authoritative visual-kit source and every referenced template source, so do not
define or import `Layout`, `VisualTemplate`, `SafeScene`, or referenced template
classes/helpers.

Fix the smallest root cause that resolves the reported verification failure
while preserving the video plan, code plan, local template construction,
ordered template actions, subscene transitions, subscene order, and renderable
`Scene{number}(SafeScene)` class names.

Fix every occurrence of the same root-cause pattern in the current lesson body,
not only the first failing line. Preserve every claimed mathematical invariant.
For every planned `templates[].reference`, preserve or restore its validated
template class `build(...)` usage, explicit `state` parameter, and action
contract instead of copying its source or inventing replacement geometry.

Do not introduce snapshot builder functions. Each subscene must construct its
planned templates locally with the planned state. Center content is the one
template; split content is exactly `VGroup(left_template, right_template)` in
planned order. For `show`, clear content before `show_main()`. For
`transform`, omit `clear_content()` and use `transform_main()`. Execute planned
actions sequentially after the main transition through `play_action(...)`. Pass
each planned caption and always apply the planned bottom text, including
`None`. Do not introduce
lesson-specific `self.play(...)`. Use only `Layout.CENTER` and `Layout.SPLIT`.
Do not add external assets, file I/O, network access, subprocesses, dynamic
execution, or plugins.
