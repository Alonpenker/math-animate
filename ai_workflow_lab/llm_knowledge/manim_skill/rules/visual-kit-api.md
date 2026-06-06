# Visual Kit API

The application prepends the authoritative visual-kit source to the generated
lesson body. Generated code must not import `visual_kit` or redefine `Layout`
or `SafeScene`.

Every renderable class inherits `SafeScene`. Use only:

- `show_title(text, color=WHITE)`
- `set_bottom_text(text_or_none, color=WHITE)`
- `show_main(content, layout=Layout.CENTER, caption=None)`
- `transform_main(content, layout=Layout.CENTER, caption=None)`
- `clear_content()`
- `fade_out_all()`

`content` must be one fully internally arranged snapshot `VGroup`. Builders take
no arguments and return one complete group for each planned subscene.

`Layout.CENTER` fits that complete group into the main region without changing
its internal arrangement.

`Layout.SPLIT` requires exactly:

```python
VGroup(left_panel, right_panel)
```

Both children must be `VGroup`s and must already be internally arranged. The
visual kit only fits the completed panels into left and right regions.

For a `show` subscene, call `clear_content()` and then `show_main(...)`. For a
`transform` subscene, preserve current content and call `transform_main(...)`.
Keep persistent semantic children in compatible order across snapshots that
transform into each other so the whole-group replacement remains understandable.

Use `caption=` only for a short caption near the main region and
`set_bottom_text()` only for a short takeaway. Call `set_bottom_text()` for every
subscene; passing `None` fades out and clears previous bottom text. Generated
lesson code should not call `self.play(...)` directly.
