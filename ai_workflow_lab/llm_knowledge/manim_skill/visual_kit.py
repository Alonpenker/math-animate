from __future__ import annotations

import random
from typing import Sequence

import numpy as np
from manim import *


__all__ = ["SafeScene", "fit_to_region"]


class _Region:
    def __init__(self, center: Sequence[float], width: float, height: float) -> None:
        self.center = np.array(center, dtype=float)
        self.width = float(width)
        self.height = float(height)


def fit_to_region(mobject: Mobject, region: _Region, buff: float = 0.0) -> Mobject:
    max_width = max(region.width - 2 * buff, 0.1)
    max_height = max(region.height - 2 * buff, 0.1)
    if mobject.width > max_width and mobject.width > 0:
        mobject.scale(max_width / mobject.width)
    if mobject.height > max_height and mobject.height > 0:
        mobject.scale(max_height / mobject.height)
    mobject.move_to(region.center)
    return mobject


def _one_line_text(text: str, max_chars: int = 92) -> str:
    collapsed = " ".join(str(text).split())
    if len(collapsed) <= max_chars:
        return collapsed
    return collapsed[: max_chars - 3].rstrip() + "..."


class SafeScene(Scene):
    title_font_size = 40
    bottom_font_size = 28
    background_palette = (
        "#101820",
        "#0E1B2A",
        "#111827",
        "#10231F",
        "#1B1A27",
        "#171923",
    )

    def setup(self) -> None:
        super().setup()
        self.camera.background_color = random.choice(self.background_palette)
        frame_width = float(config.frame_width)
        frame_height = float(config.frame_height)
        self.title_region = _Region(
            center=(0, frame_height / 2 - 0.55, 0),
            width=frame_width - 1.0,
            height=0.75,
        )
        self.main_region = _Region(
            center=(0, 0.05, 0),
            width=frame_width - 1.0,
            height=frame_height - 2.25,
        )
        self.bottom_region = _Region(
            center=(0, -frame_height / 2 + 0.5, 0),
            width=frame_width - 1.2,
            height=0.7,
        )
        self.left_main_region = _Region(
            center=(-frame_width * 0.24, 0.05, 0),
            width=frame_width * 0.46,
            height=frame_height - 2.35,
        )
        self.right_main_region = _Region(
            center=(frame_width * 0.24, 0.05, 0),
            width=frame_width * 0.46,
            height=frame_height - 2.35,
        )
        self.title_mobject: Mobject | None = None
        self.main_mobject: Mobject | None = None
        self.bottom_mobject: Mobject | None = None

    def show_title(self, text: str, color: ManimColor = WHITE) -> Mobject:
        title = Text(_one_line_text(text, 70), font_size=self.title_font_size, color=color)
        fit_to_region(title, self.title_region)
        if self.title_mobject is None:
            self.play(Write(title))
        else:
            self.play(ReplacementTransform(self.title_mobject, title))
        self.title_mobject = title
        return title

    def set_bottom_text(
        self,
        text: str,
        color: ManimColor = WHITE,
    ) -> Mobject:
        bottom = Text(_one_line_text(text), font_size=self.bottom_font_size, color=color)
        fit_to_region(bottom, self.bottom_region)
        if self.bottom_mobject is None:
            self.play(FadeIn(bottom, shift=UP * 0.12))
        else:
            self.play(FadeOut(self.bottom_mobject, shift=DOWN * 0.08))
            self.play(FadeIn(bottom, shift=UP * 0.12))
        self.bottom_mobject = bottom
        return bottom

    def clear_subscene(self) -> None:
        targets = [
            mobject
            for mobject in (self.main_mobject, self.bottom_mobject)
            if mobject is not None
        ]
        if targets:
            self.play(*[FadeOut(mobject) for mobject in targets])
        self.main_mobject = None
        self.bottom_mobject = None

    def fade_out_all(self) -> None:
        if self.mobjects:
            self.play(*[FadeOut(mobject) for mobject in list(self.mobjects)])
        self.title_mobject = None
        self.main_mobject = None
        self.bottom_mobject = None

    def _replace_main(self, content: Mobject, *, fit: bool = True) -> Mobject:
        if self.main_mobject is not None:
            self.play(FadeOut(self.main_mobject))
            self.main_mobject = None
        if fit:
            fit_to_region(content, self.main_region)
        self.play(FadeIn(content))
        self.main_mobject = content
        return content

    def _transform_main(self, content: Mobject, *, fit: bool = True) -> Mobject:
        if fit:
            fit_to_region(content, self.main_region)
        if self.main_mobject is None:
            self.play(FadeIn(content))
        else:
            self.play(ReplacementTransform(self.main_mobject, content))
        self.main_mobject = content
        return content

    def show_center(self, content: Mobject) -> Mobject:
        return self._replace_main(content)

    def transform_center(self, content: Mobject) -> Mobject:
        return self._transform_main(content)

    def show_center_with_caption(
        self,
        content: Mobject,
        caption: str | Mobject,
        *,
        caption_color: ManimColor = WHITE,
        caption_font_size: int = 24,
    ) -> Mobject:
        return self._replace_main(
            self._center_caption_group(
                content,
                caption,
                caption_color=caption_color,
                caption_font_size=caption_font_size,
            ),
            fit=False,
        )

    def transform_center_with_caption(
        self,
        content: Mobject,
        caption: str | Mobject,
        *,
        caption_color: ManimColor = WHITE,
        caption_font_size: int = 24,
    ) -> Mobject:
        return self._transform_main(
            self._center_caption_group(
                content,
                caption,
                caption_color=caption_color,
                caption_font_size=caption_font_size,
            ),
            fit=False,
        )

    def _center_caption_group(
        self,
        content: Mobject,
        caption: str | Mobject,
        *,
        caption_color: ManimColor = WHITE,
        caption_font_size: int = 24,
    ) -> Group:
        if isinstance(caption, str):
            caption_mobject = Text(
                _one_line_text(caption, 82),
                font_size=caption_font_size,
                color=caption_color,
            )
        else:
            caption_mobject = caption

        caption_region = _Region(
            center=(
                self.main_region.center[0],
                self.main_region.center[1] - self.main_region.height / 2 + 0.35,
                0,
            ),
            width=self.main_region.width,
            height=0.55,
        )
        content_region = _Region(
            center=(
                self.main_region.center[0],
                self.main_region.center[1] + 0.22,
                0,
            ),
            width=self.main_region.width,
            height=self.main_region.height - 0.85,
        )
        fit_to_region(content, content_region, buff=0.1)
        fit_to_region(caption_mobject, caption_region, buff=0.05)
        return Group(content, caption_mobject)

    def show_left_right(
        self,
        left: Mobject,
        right: Mobject | None = None,
    ) -> Mobject:
        if right is None:
            return self.show_center(left)
        fit_to_region(left, self.left_main_region, buff=0.12)
        fit_to_region(right, self.right_main_region, buff=0.15)
        return self._replace_main(Group(left, right), fit=False)

    def transform_left_right(
        self,
        left: Mobject,
        right: Mobject | None = None,
    ) -> Mobject:
        if right is None:
            return self.transform_center(left)
        fit_to_region(left, self.left_main_region, buff=0.12)
        fit_to_region(right, self.right_main_region, buff=0.15)
        return self._transform_main(Group(left, right), fit=False)

    def show_stack(
        self,
        items: Mobject | Sequence[Mobject],
        direction: np.ndarray = DOWN,
        buff: float = 0.35,
    ) -> Mobject:
        if isinstance(items, Mobject):
            stack = items
        else:
            stack = Group(*items).arrange(direction, buff=buff, aligned_edge=LEFT)
        return self._replace_main(stack)

    def transform_stack(
        self,
        items: Mobject | Sequence[Mobject],
        direction: np.ndarray = DOWN,
        buff: float = 0.35,
    ) -> Mobject:
        if isinstance(items, Mobject):
            stack = items
        else:
            stack = Group(*items).arrange(direction, buff=buff, aligned_edge=LEFT)
        return self._transform_main(stack)
          