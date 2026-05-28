from manim import *
import numpy as np


class PythagoreanTheoremProof(Scene):
    """Visual rearrangement proof of a^2 + b^2 = c^2."""

    def construct(self):
        self.camera.background_color = "#101820"

        self.a = 1.45
        self.b = 2.35
        self.side = self.a + self.b
        self.origin = np.array([-5.25, -2.25, 0.0])

        self.colors = {
            "a": GOLD,
            "b": TEAL_B,
            "c": RED_C,
            "triangle": BLUE_D,
            "outline": GREY_B,
            "text": WHITE,
        }

        title = Text("Pythagorean Theorem", font_size=40, weight=BOLD)
        title.to_edge(UP, buff=0.35)
        subtitle = MathTex(r"a^2 + b^2 = c^2", font_size=42)
        subtitle.next_to(title, DOWN, buff=0.18)
        subtitle[0][0].set_color(self.colors["a"])
        subtitle[0][3].set_color(self.colors["b"])
        subtitle[0][6].set_color(self.colors["c"])

        self.play(Write(title), FadeIn(subtitle, shift=DOWN * 0.2), run_time=1.4)
        self.wait(0.4)

        intro = self.make_intro_triangle()
        self.play(Create(intro["triangle"]), Create(intro["right_angle"]), run_time=1.0)
        self.play(
            LaggedStart(
                Write(intro["labels"]),
                Write(intro["caption"]),
                lag_ratio=0.2,
            ),
            run_time=1.5,
        )
        self.wait(0.8)

        subtitle_target = subtitle.copy()
        subtitle_target.scale(0.78)
        subtitle_target.next_to(title, RIGHT, buff=0.9).shift(DOWN * 0.18)

        self.play(
            FadeOut(intro["group"], shift=LEFT * 0.3),
            Transform(subtitle, subtitle_target),
            run_time=1.0,
        )

        arrangement_one = self.make_c_square_arrangement()
        outer_title = Text("Same outer square", font_size=24, color=GREY_A)
        outer_title.next_to(arrangement_one["outer"], UP, buff=0.25)

        self.play(Create(arrangement_one["outer"]), Write(outer_title), run_time=1.0)
        self.play(
            LaggedStart(
                *[FadeIn(triangle, shift=0.12 * OUT) for triangle in arrangement_one["triangles"]],
                lag_ratio=0.12,
            ),
            run_time=1.6,
        )
        self.play(Write(arrangement_one["side_labels"]), run_time=0.7)
        self.play(
            FadeIn(arrangement_one["c_square"]),
            Create(arrangement_one["c_outline"]),
            Write(arrangement_one["c_label"]),
            run_time=1.0,
        )
        self.play(self.pulse_c_square(arrangement_one), run_time=1.1)
        self.wait(0.5)

        equation_group = self.make_area_equations()
        self.play(Write(equation_group["eq1"]), run_time=1.2)
        self.wait(0.4)
        self.play(
            Indicate(equation_group["eq1"][0], color=YELLOW),
            Circumscribe(arrangement_one["outer"], color=YELLOW),
            run_time=1.2,
        )
        self.play(
            Indicate(equation_group["eq1"][2], color=self.colors["triangle"]),
            self.pulse_triangles(arrangement_one["triangles"]),
            run_time=1.2,
        )
        self.play(
            Indicate(equation_group["eq1"][4], color=self.colors["c"]),
            self.pulse_c_square(arrangement_one),
            run_time=1.1,
        )
        self.wait(0.5)

        move_caption = Text("Now rearrange the same four triangles.", font_size=25)
        move_caption.next_to(equation_group["eq1"], DOWN, buff=0.55)
        self.play(FadeIn(move_caption, shift=UP * 0.2), run_time=0.8)

        arrangement_two = self.make_ab_square_arrangement()
        self.play(
            FadeOut(arrangement_one["c_square"]),
            FadeOut(arrangement_one["c_outline"]),
            FadeOut(arrangement_one["c_label"]),
            FadeOut(move_caption),
            Transform(arrangement_one["triangles"], arrangement_two["triangles"]),
            run_time=2.2,
            rate_func=smooth,
        )
        self.play(
            FadeIn(arrangement_two["b_square"]),
            FadeIn(arrangement_two["a_square"]),
            Create(arrangement_two["b_outline"]),
            Create(arrangement_two["a_outline"]),
            Write(arrangement_two["b_label"]),
            Write(arrangement_two["a_label"]),
            run_time=1.1,
        )
        self.play(
            Circumscribe(arrangement_two["a_outline"], color=self.colors["a"]),
            Circumscribe(arrangement_two["b_outline"], color=self.colors["b"]),
            run_time=1.1,
        )
        self.wait(0.4)

        eq2 = equation_group["eq2"]
        same_area_note = Text("Outer square and triangles did not change.", font_size=23, color=GREY_A)
        same_area_note.next_to(eq2, DOWN, buff=0.35)
        self.play(FadeOut(equation_group["eq1"], shift=UP * 0.08), run_time=0.45)
        self.play(Write(eq2), FadeIn(same_area_note, shift=UP * 0.15), run_time=1.1)
        self.wait(0.5)

        conclusion = equation_group["conclusion"]
        self.play(
            ReplacementTransform(eq2, conclusion),
            FadeOut(same_area_note),
            run_time=1.2,
        )
        self.play(Circumscribe(conclusion, color=YELLOW), run_time=1.0)
        self.wait(0.5)

        derivation = self.make_algebra_derivation()
        self.play(
            FadeOut(arrangement_one["outer"]),
            FadeOut(outer_title),
            FadeOut(arrangement_one["side_labels"]),
            FadeOut(arrangement_one["triangles"]),
            FadeOut(arrangement_two["a_square"]),
            FadeOut(arrangement_two["b_square"]),
            FadeOut(arrangement_two["a_outline"]),
            FadeOut(arrangement_two["b_outline"]),
            FadeOut(arrangement_two["a_label"]),
            FadeOut(arrangement_two["b_label"]),
            FadeOut(conclusion),
            run_time=1.0,
        )
        self.play(LaggedStart(*[Write(row) for row in derivation], lag_ratio=0.2), run_time=2.6)

        final_box = SurroundingRectangle(derivation[-1], color=YELLOW, buff=0.2)
        self.play(Create(final_box), run_time=0.8)
        self.wait(0.6)
        self.play(FadeOut(VGroup(title, subtitle, derivation, final_box)), run_time=1.0)
        self.wait(1.0)

    def point(self, x, y):
        return self.origin + np.array([x, y, 0.0])

    def make_polygon(self, coords, **kwargs):
        return Polygon(*[self.point(x, y) for x, y in coords], **kwargs)

    def pulse_triangles(self, triangles):
        return AnimationGroup(
            *[
                triangle.animate(rate_func=there_and_back)
                .set_fill(self.colors["triangle"], opacity=0.84)
                .set_stroke(WHITE, width=5)
                for triangle in triangles
            ],
            lag_ratio=0,
        )

    def pulse_c_square(self, arrangement):
        return AnimationGroup(
            arrangement["c_square"].animate(rate_func=there_and_back)
            .set_fill(self.colors["c"], opacity=0.62)
            .scale(1.035),
            arrangement["c_outline"].animate(rate_func=there_and_back)
            .set_stroke(self.colors["c"], width=7)
            .scale(1.035),
            arrangement["c_label"].animate(rate_func=there_and_back).scale(1.18),
            lag_ratio=0,
        )

    def make_outer_side_labels(self):
        a = self.a
        b = self.b
        s = self.side

        b_segment = Line(self.point(0, 0), self.point(b, 0))
        a_segment = Line(self.point(b, 0), self.point(s, 0))

        b_label = MathTex("b", font_size=30, color=self.colors["b"])
        b_label.next_to(b_segment, DOWN, buff=0.11)
        a_label = MathTex("a", font_size=30, color=self.colors["a"])
        a_label.next_to(a_segment, DOWN, buff=0.11)

        return VGroup(b_label, a_label)

    def make_intro_triangle(self):
        scale = 1.2
        origin = LEFT * 2.0 + DOWN * 1.0
        p0 = origin
        p1 = origin + RIGHT * self.b * scale
        p2 = origin + UP * self.a * scale

        triangle = Polygon(
            p0,
            p1,
            p2,
            color=WHITE,
            fill_color=self.colors["triangle"],
            fill_opacity=0.45,
            stroke_width=4,
        )
        right_angle = RightAngle(Line(p0, p1), Line(p0, p2), length=0.22, color=YELLOW)

        b_label = MathTex("b", font_size=38, color=self.colors["b"])
        b_label.next_to(Line(p0, p1), DOWN, buff=0.12)
        a_label = MathTex("a", font_size=38, color=self.colors["a"])
        a_label.next_to(Line(p0, p2), LEFT, buff=0.12)
        c_label = MathTex("c", font_size=38, color=self.colors["c"])
        hypotenuse = Line(p1, p2)
        c_label.move_to(hypotenuse.get_center() + UP * 0.16 + RIGHT * 0.07)
        labels = VGroup(a_label, b_label, c_label)

        caption = Text("A right triangle has leg lengths a and b, and hypotenuse c.", font_size=26)
        caption.to_edge(DOWN, buff=0.55)

        return {
            "triangle": triangle,
            "right_angle": right_angle,
            "labels": labels,
            "caption": caption,
            "group": VGroup(triangle, right_angle, labels, caption),
        }

    def make_c_square_arrangement(self):
        a = self.a
        b = self.b
        s = self.side

        outer = Square(side_length=s, color=self.colors["outline"], stroke_width=4)
        outer.move_to(self.point(s / 2, s / 2))

        triangle_coords = [
            [(0, 0), (b, 0), (0, a)],
            [(s, 0), (b, 0), (s, b)],
            [(s, s), (s, b), (a, s)],
            [(0, s), (a, s), (0, a)],
        ]
        triangles = VGroup(
            *[
                self.make_polygon(
                    coords,
                    color=WHITE,
                    fill_color=self.colors["triangle"],
                    fill_opacity=0.55,
                    stroke_width=2.5,
                )
                for coords in triangle_coords
            ]
        )

        c_square_coords = [(b, 0), (s, b), (a, s), (0, a)]
        c_square = self.make_polygon(
            c_square_coords,
            color=self.colors["c"],
            fill_color=self.colors["c"],
            fill_opacity=0.34,
            stroke_width=0,
        )
        c_outline = self.make_polygon(
            c_square_coords,
            color=self.colors["c"],
            fill_opacity=0,
            stroke_width=4,
        )
        c_label = MathTex("c^2", font_size=42, color=self.colors["c"])
        c_label.move_to(c_square.get_center())
        side_labels = self.make_outer_side_labels()

        return {
            "outer": outer,
            "triangles": triangles,
            "side_labels": side_labels,
            "c_square": c_square,
            "c_outline": c_outline,
            "c_label": c_label,
        }

    def make_ab_square_arrangement(self):
        a = self.a
        b = self.b
        s = self.side

        triangle_coords = [
            [(0, b), (0, s), (b, s)],
            [(0, b), (b, b), (b, s)],
            [(b, 0), (s, 0), (s, b)],
            [(b, 0), (b, b), (s, b)],
        ]
        triangles = VGroup(
            *[
                self.make_polygon(
                    coords,
                    color=WHITE,
                    fill_color=self.colors["triangle"],
                    fill_opacity=0.55,
                    stroke_width=2.5,
                )
                for coords in triangle_coords
            ]
        )

        b_square_coords = [(0, 0), (b, 0), (b, b), (0, b)]
        a_square_coords = [(b, b), (s, b), (s, s), (b, s)]

        b_square = self.make_polygon(
            b_square_coords,
            color=self.colors["b"],
            fill_color=self.colors["b"],
            fill_opacity=0.35,
            stroke_width=0,
        )
        a_square = self.make_polygon(
            a_square_coords,
            color=self.colors["a"],
            fill_color=self.colors["a"],
            fill_opacity=0.35,
            stroke_width=0,
        )
        b_outline = self.make_polygon(
            b_square_coords,
            color=self.colors["b"],
            fill_opacity=0,
            stroke_width=4,
        )
        a_outline = self.make_polygon(
            a_square_coords,
            color=self.colors["a"],
            fill_opacity=0,
            stroke_width=4,
        )

        b_label = MathTex("b^2", font_size=42, color=self.colors["b"])
        b_label.move_to(b_square.get_center())
        a_label = MathTex("a^2", font_size=42, color=self.colors["a"])
        a_label.move_to(a_square.get_center())

        return {
            "triangles": triangles,
            "b_square": b_square,
            "a_square": a_square,
            "b_outline": b_outline,
            "a_outline": a_outline,
            "b_label": b_label,
            "a_label": a_label,
        }

    def make_area_equations(self):
        eq1 = MathTex(
            r"(a+b)^2",
            r"=",
            r"4\left(\frac12 ab\right)",
            r"+",
            r"c^2",
            font_size=36,
        )
        eq1.move_to(RIGHT * 3.0 + UP * 0.65)
        eq1.set_color_by_tex("a", self.colors["a"])
        eq1.set_color_by_tex("b", self.colors["b"])
        eq1[2].set_color(self.colors["triangle"])
        eq1[4].set_color(self.colors["c"])

        eq2 = MathTex(
            r"(a+b)^2",
            r"=",
            r"4\left(\frac12 ab\right)",
            r"+",
            r"a^2",
            r"+",
            r"b^2",
            font_size=36,
        )
        eq2.move_to(eq1)
        eq2.set_color_by_tex("a", self.colors["a"])
        eq2.set_color_by_tex("b", self.colors["b"])
        eq2[2].set_color(self.colors["triangle"])
        eq2[4].set_color(self.colors["a"])
        eq2[6].set_color(self.colors["b"])

        conclusion = MathTex(r"c^2", r"=", r"a^2", r"+", r"b^2", font_size=48)
        conclusion.move_to(eq1).shift(DOWN * 0.2)
        conclusion[0].set_color(self.colors["c"])
        conclusion[2].set_color(self.colors["a"])
        conclusion[4].set_color(self.colors["b"])

        return {"eq1": eq1, "eq2": eq2, "conclusion": conclusion}

    def make_algebra_derivation(self):
        rows = VGroup(
            MathTex(r"(a+b)^2", r"=", r"4\left(\frac12 ab\right)", r"+", r"c^2", font_size=38),
            MathTex(r"a^2 + 2ab + b^2", r"=", r"2ab", r"+", r"c^2", font_size=38),
            MathTex(r"a^2 + b^2", r"=", r"c^2", font_size=48),
        )
        rows.arrange(DOWN, buff=0.42)
        rows.move_to(DOWN * 0.65)

        rows[0].set_color_by_tex("a", self.colors["a"])
        rows[0].set_color_by_tex("b", self.colors["b"])
        rows[0][2].set_color(self.colors["triangle"])
        rows[0][4].set_color(self.colors["c"])

        rows[1].set_color_by_tex("a", self.colors["a"])
        rows[1].set_color_by_tex("b", self.colors["b"])
        rows[1][2].set_color(self.colors["triangle"])
        rows[1][4].set_color(self.colors["c"])

        rows[2].set_color_by_tex("a", self.colors["a"])
        rows[2].set_color_by_tex("b", self.colors["b"])
        rows[2][2].set_color(self.colors["c"])

        return rows
