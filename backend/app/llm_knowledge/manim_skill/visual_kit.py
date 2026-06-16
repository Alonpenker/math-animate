import enum as _enum
import random as _random

import manim as _m
import numpy as _np


_TEXT = {
    "title": (40, 70),
    "bottom": (28, 92),
    "caption": (24, 82),
}
_REGION = {
    "side": 0.5,
    "bottom_side": 0.6,
    "title_y": 0.55,
    "title_h": 0.75,
    "bottom_y": 0.5,
    "bottom_h": 0.7,
    "main_y": 0.05,
    "main_reserve": 2.25,
    "caption_h": 0.55,
    "caption_gap": 0.25,
    "split_gap": 0.6,
}
_FIT = {
    "min": 0.1,
    "center": 0.0,
    "split": 0.14,
    "caption_body": 0.1,
    "caption": 0.05,
}
_BOTTOM_SHIFT = {"in": 0.12, "out": 0.08}
_BACKGROUNDS = ("#101820", "#0E1B2A", "#111827", "#10231F", "#1B1A27", "#171923")


class Layout(_enum.Enum):
    CENTER = "center"
    SPLIT = "split"


class VisualTemplate(_m.VGroup):
    VALID_STATES: frozenset[str] = frozenset()

    @classmethod
    def build(cls, *, state: str, **parameters):
        return cls(state=state, **parameters)

    def __init__(self, *mobjects, state: str):
        self.state = self._validate_state(state)
        super().__init__(*mobjects)

    @classmethod
    def _validate_state(cls, state: str) -> str:
        if not isinstance(state, str):
            raise TypeError("template state must be a string")
        if not cls.VALID_STATES:
            raise TypeError(f"{cls.__name__} must declare VALID_STATES")
        if state not in cls.VALID_STATES:
            states = ", ".join(sorted(cls.VALID_STATES))
            raise ValueError(f"{cls.__name__} state must be one of: {states}")
        return state


def _one_line(text, max_chars):
    text = " ".join(str(text).split())
    return text if len(text) <= max_chars else text[: max_chars - 3].rstrip() + "..."


def _text(kind, value, color=_m.WHITE):
    font_size, max_chars = _TEXT[kind]
    return _m.Text(_one_line(value, max_chars), font_size=font_size, color=color)


def _region(center, width, height):
    return (_np.array(center, dtype=float), float(width), float(height))


def _screen_regions():
    frame_w = float(_m.config.frame_width)
    frame_h = float(_m.config.frame_height)
    return {
        "title": _region(
            (0, frame_h / 2 - _REGION["title_y"], 0),
            frame_w - 2 * _REGION["side"],
            _REGION["title_h"],
        ),
        "main": _region(
            (0, _REGION["main_y"], 0),
            frame_w - 2 * _REGION["side"],
            frame_h - _REGION["main_reserve"],
        ),
        "bottom": _region(
            (0, -frame_h / 2 + _REGION["bottom_y"], 0),
            frame_w - 2 * _REGION["bottom_side"],
            _REGION["bottom_h"],
        ),
    }


def _fit(mobject, region, buff=0.0):
    center, width, height = region
    max_w = max(width - 2 * buff, _FIT["min"])
    max_h = max(height - 2 * buff, _FIT["min"])
    if mobject.width > max_w and mobject.width > 0:
        mobject.scale(max_w / mobject.width)
    if mobject.height > max_h and mobject.height > 0:
        mobject.scale(max_h / mobject.height)
    return mobject.move_to(center)


def _layout(value):
    if isinstance(value, Layout):
        return value
    try:
        return Layout(str(value).lower())
    except ValueError as exc:
        raise ValueError("layout must be Layout.CENTER or Layout.SPLIT") from exc


def _caption_regions(main_region):
    center, width, height = main_region
    caption_h = _REGION["caption_h"]
    body_h = max(height - caption_h - _REGION["caption_gap"], _FIT["min"])
    return (
        _region((center[0], center[1] + (height - body_h) / 2, 0), width, body_h),
        _region((center[0], center[1] - height / 2 + caption_h / 2, 0), width, caption_h),
    )


def _split_regions(region):
    center, width, height = region
    pane_w = max((width - _REGION["split_gap"]) / 2, _FIT["min"])
    offset = (pane_w + _REGION["split_gap"]) / 2
    return (
        _region((center[0] - offset, center[1], 0), pane_w, height),
        _region((center[0] + offset, center[1], 0), pane_w, height),
    )


class SafeScene(_m.Scene):
    def setup(self):
        super().setup()
        self.camera.background_color = _random.choice(_BACKGROUNDS)
        self._regions = _screen_regions()
        self._title = None
        self._main = None
        self._bottom = None

    def show_title(self, text: str, color: _m.ManimColor = _m.WHITE):
        title = _fit(_text("title", text, color), self._regions["title"])
        animation = _m.Write(title) if self._title is None else _m.ReplacementTransform(self._title, title)
        self.play(animation)
        self._title = title
        return title

    def set_bottom_text(self, text: str | None, color: _m.ManimColor = _m.WHITE):
        if text is None:
            if self._bottom is not None:
                self.play(_m.FadeOut(self._bottom, shift=_m.DOWN * _BOTTOM_SHIFT["out"]))
            self._bottom = None
            return None

        bottom = _fit(_text("bottom", text, color), self._regions["bottom"])
        if self._bottom is not None:
            self.play(_m.FadeOut(self._bottom, shift=_m.DOWN * _BOTTOM_SHIFT["out"]))
        self.play(_m.FadeIn(bottom, shift=_m.UP * _BOTTOM_SHIFT["in"]))
        self._bottom = bottom
        return bottom

    def show_main(self, content, *, layout=Layout.CENTER, caption=None):
        group = self._prepare_main(content, layout, caption)
        if self._main is not None:
            self.play(_m.FadeOut(self._main))
        self.play(_m.FadeIn(group))
        self._main = group
        return group

    def transform_main(self, content, *, layout=Layout.CENTER, caption=None):
        group = self._prepare_main(content, layout, caption)
        animation = (
            _m.FadeIn(group)
            if self._main is None
            else _m.ReplacementTransform(self._main, group)
        )
        self.play(animation)
        self._main = group
        return group

    def play_action(self, animation):
        if not isinstance(animation, _m.Animation):
            raise TypeError("template actions must return a Manim Animation")
        self.play(animation)
        return animation

    def clear_content(self):
        visible = [m for m in (self._main, self._bottom) if m is not None]
        if visible:
            self.play(*[_m.FadeOut(m) for m in visible])
        self._main = None
        self._bottom = None

    def fade_out_all(self):
        if self.mobjects:
            self.play(*[_m.FadeOut(m) for m in list(self.mobjects)])
        self._title = None
        self._main = None
        self._bottom = None

    def _prepare_main(self, content, layout, caption):
        if not isinstance(content, _m.VGroup):
            raise TypeError("content must be a VGroup")

        layout = _layout(layout)
        content_region = self._regions["main"]
        caption_mobject = _text("caption", caption) if isinstance(caption, str) else caption

        if caption_mobject is not None:
            content_region, caption_region = _caption_regions(content_region)

        if layout is Layout.CENTER:
            if not isinstance(content, VisualTemplate):
                raise ValueError("Layout.CENTER content must be one VisualTemplate")
            buff = _FIT["caption_body"] if caption_mobject is not None else _FIT["center"]
            _fit(content, content_region, buff)
        elif layout is Layout.SPLIT:
            self._fit_split(content, content_region)
        if caption_mobject is None:
            return content
        _fit(caption_mobject, caption_region, _FIT["caption"])
        return _m.VGroup(content, caption_mobject)

    def _fit_split(self, content, region):
        children = list(content.submobjects)
        if len(children) != 2 or not all(isinstance(child, VisualTemplate) for child in children):
            raise ValueError(
                "Layout.SPLIT content must be "
                "VGroup(left_template, right_template)"
            )
        left_region, right_region = _split_regions(region)
        _fit(children[0], left_region, _FIT["split"])
        _fit(children[1], right_region, _FIT["split"])
