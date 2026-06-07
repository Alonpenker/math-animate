Fix the lesson-specific body of a Manim Community v0.19.2 script.

Return only the complete corrected lesson body. The application prepends the
authoritative visual-kit source and every referenced template source, so do not
define or import `Layout`, `SafeScene`, or referenced template helpers.

Fix the smallest root cause that resolves the reported verification failure
while preserving the video plan, code plan, snapshot builder functions,
subscene transitions, subscene order, and renderable
`Scene{number}(SafeScene)` class names.

Fix every occurrence of the same root-cause pattern in the current lesson body,
not only the first failing line. Preserve every claimed mathematical invariant;
do not make a shape merely renderable by weakening what it claims to represent.
For every planned template `references` title, preserve or restore its validated
public helper usage and state pattern instead of copying its source or inventing
replacement geometry.

Keep every builder fully internally arranged and returning one snapshot
`VGroup`. For `show` subscenes, clear content before `show_main()`. For
`transform` subscenes, preserve current content and use `transform_main()`.
Pass each subscene's planned caption to its main transition helper. Always apply
the planned bottom text, including `None`. Do not introduce lesson-specific
`self.play(...)`. Use only `Layout.CENTER` and `Layout.SPLIT`. Do not add
external assets, file I/O, network access, subprocesses, dynamic execution, or
plugins.
