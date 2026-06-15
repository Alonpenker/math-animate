# Visual Kit API

The application prepends the authoritative visual-kit and referenced-template
sources to the generated lesson body. Generated code must not import or
redefine `Layout`, `VisualTemplate`, `SafeScene`, or referenced template
classes/helpers.

Every maintained template inherits `VisualTemplate`, so each constructed
template instance is a self-contained `VGroup`. A template's `__init__` method
initializes that group through `super().__init__(..., state=state)`; Python
constructors do not return a value.

Every template declares named `VALID_STATES` and accepts an explicit `state`.
Construct it with `TemplateClass.build(state="...", ...)`. State selects the
object's visual form; other parameters provide its mathematical content or
dimensions.

Templates own their geometry, labels, markers, and annotations. They must not
position themselves for center, split, comparison, captions, or any other scene
layout. To compare an object in two states, construct the same template class
twice and let `SafeScene` apply the requested layout.

Templates may expose meaningful public action methods. Every exposed action
must return one Manim `Animation` object and must animate only template-owned
content.

Every renderable class inherits `SafeScene`. Use only:

- `show_title(text, color=WHITE)`
- `set_bottom_text(text_or_none, color=WHITE)`
- `show_main(content, layout=Layout.CENTER, caption=None)`
- `transform_main(content, layout=Layout.CENTER, caption=None)`
- `play_action(animation)`
- `clear_content()`
- `fade_out_all()`

Construct templates locally inside each subscene. Do not define snapshot
builder functions or call compatibility `make_*` wrappers.

`Layout.CENTER` requires one template instance passed directly as `content`.

`Layout.SPLIT` requires exactly:

```python
VGroup(left_template, right_template)
```

Both children must be `VisualTemplate` instances in planned left-to-right
order. The visual kit only fits them into left and right regions.

For a `show` subscene, call `clear_content()` and then `show_main(...)`. For a
`transform` subscene, omit `clear_content()` and call `transform_main(...)`.
After the main transition, execute planned actions sequentially:

```python
self.play_action(template.safe_action(...))
```

In this general pattern, replace `template` with the planned local template
instance name and replace `safe_action` with the exact public action method
named by the code plan. Call that method on the template instance and pass its
returned animation to `play_action(...)`; `play_action(...)` is the only allowed
way for lesson code to play template-owned animations. Call `set_bottom_text()`
for every subscene; passing
`None` fades out and clears previous bottom text. Generated lesson code must not
call `self.play(...)` directly.
