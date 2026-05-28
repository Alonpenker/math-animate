from manim import *
import numpy as np


class CircleTangentConstructionBase:
    """Shared geometry and visual language for the tangent construction scenes."""

    def setup_tangent_scene(self):
        self.camera.background_color = "#101820"
        self.O = np.array([-2.65, -0.45, 0.0])
        self.P = np.array([3.25, -0.45, 0.0])
        self.radius = 1.75
        self.M = (self.O + self.P) / 2
        self.aux_radius = np.linalg.norm(self.P - self.O) / 2
        self.T1, self.T2 = self.tangent_points()

        self.colors = {
            "circle": TEAL_B,
            "aux": GOLD,
            "guide": GREY_B,
            "guide_dim": GREY_D,
            "tangent": GREEN_B,
            "point": YELLOW,
            "text": WHITE,
            "muted": GREY_A,
            "proof": BLUE_D,
        }

    def tangent_points(self):
        op = self.P - self.O
        distance = np.linalg.norm(op)
        unit = op / distance
        perpendicular = np.array([-unit[1], unit[0], 0.0])
        along = self.radius**2 / distance
        height = np.sqrt(self.radius**2 - along**2)
        foot = self.O + along * unit
        return foot + height * perpendicular, foot - height * perpendicular

    def make_title(self, title_text, subtitle_text):
        title = Text(title_text, font_size=38, weight=BOLD)
        title.to_edge(UP, buff=0.32)
        subtitle = Text(subtitle_text, font_size=23, color=self.colors["muted"])
        subtitle.next_to(title, DOWN, buff=0.14)
        return VGroup(title, subtitle)

    def make_point(self, point, label, direction, color=None, buff=0.11):
        dot = Dot(point, radius=0.07, color=color or self.colors["point"])
        text = MathTex(label, font_size=31, color=color or self.colors["point"])
        text.next_to(dot, direction, buff=buff)
        return VGroup(dot, text)

    def make_core_diagram(self, faded_guides=False):
        guide_opacity = 0.35 if faded_guides else 0.95
        circle = Circle(
            radius=self.radius,
            color=self.colors["circle"],
            stroke_width=5,
            fill_color=self.colors["circle"],
            fill_opacity=0.08,
        ).move_to(self.O)

        auxiliary_circle = Circle(
            radius=self.aux_radius,
            color=self.colors["aux"],
            stroke_width=3,
            stroke_opacity=guide_opacity,
        ).move_to(self.M)

        op_line = Line(
            self.O,
            self.P,
            color=self.colors["guide"],
            stroke_width=3,
            stroke_opacity=guide_opacity,
        )
        radius_t1 = DashedLine(
            self.O,
            self.T1,
            color=self.colors["guide"],
            stroke_width=2,
            dash_length=0.09,
            stroke_opacity=guide_opacity,
        )
        radius_t2 = DashedLine(
            self.O,
            self.T2,
            color=self.colors["guide"],
            stroke_width=2,
            dash_length=0.09,
            stroke_opacity=guide_opacity,
        )

        tangent_1 = self.make_tangent_segment(self.T1)
        tangent_2 = self.make_tangent_segment(self.T2)

        points = VGroup(
            self.make_point(self.O, "O", DL, color=self.colors["circle"]),
            self.make_point(self.P, "P", DR, color=self.colors["point"]),
            self.make_point(self.M, "M", DOWN, color=self.colors["aux"], buff=0.09),
            self.make_point(self.T1, "T_1", UP, color=self.colors["tangent"], buff=0.1),
            self.make_point(self.T2, "T_2", DOWN, color=self.colors["tangent"], buff=0.1),
        )

        if faded_guides:
            points[2].set_opacity(0.65)

        return {
            "circle": circle,
            "auxiliary_circle": auxiliary_circle,
            "op_line": op_line,
            "radius_t1": radius_t1,
            "radius_t2": radius_t2,
            "tangent_1": tangent_1,
            "tangent_2": tangent_2,
            "points": points,
            "all": VGroup(
                circle,
                auxiliary_circle,
                op_line,
                radius_t1,
                radius_t2,
                tangent_1,
                tangent_2,
                points,
            ),
        }

    def make_tangent_segment(self, tangent_point):
        direction = tangent_point - self.P
        unit = direction / np.linalg.norm(direction)
        return Line(
            self.P - 0.1 * unit,
            tangent_point + 0.62 * unit,
            color=self.colors["tangent"],
            stroke_width=6,
        )

    def make_midpoint_marks(self):
        left_mark = self.short_tick((self.O + self.M) / 2)
        right_mark = self.short_tick((self.M + self.P) / 2)
        return VGroup(left_mark, right_mark)

    def short_tick(self, center):
        return Line(
            center + np.array([-0.055, -0.13, 0.0]),
            center + np.array([0.055, 0.13, 0.0]),
            color=self.colors["aux"],
            stroke_width=4,
        )

    def make_caption(self, text):
        caption = Text(text, font_size=24, color=self.colors["text"])
        caption.to_edge(DOWN, buff=0.42)
        return caption

    def replace_caption(self, old_caption, new_text):
        new_caption = self.make_caption(new_text)
        self.play(ReplacementTransform(old_caption, new_caption), run_time=0.75)
        return new_caption

    def make_right_angle(self, tangent_point, quadrant=(1, 1)):
        return RightAngle(
            Line(tangent_point, self.O),
            Line(tangent_point, self.P),
            length=0.24,
            color=YELLOW,
            stroke_width=4,
            quadrant=quadrant,
        )

    def make_proof_panel(self):
        title = Text("Why this works", font_size=29, weight=BOLD)
        theorem = MathTex(
            r"T_1 \text{ lies on the circle with diameter } OP",
            font_size=28,
        )
        right_angle = MathTex(
            r"\angle OT_1P = 90^\circ",
            font_size=34,
            color=YELLOW,
        )
        tangent_condition = MathTex(
            r"OT_1 \perp PT_1",
            font_size=34,
        )
        result = MathTex(
            r"PT_1 \text{ is tangent to the circle.}",
            font_size=31,
            color=self.colors["tangent"],
        )
        mirror = MathTex(
            r"\text{The same argument gives } PT_2.",
            font_size=29,
            color=self.colors["muted"],
        )

        panel = VGroup(title, theorem, right_angle, tangent_condition, result, mirror)
        panel.arrange(DOWN, aligned_edge=LEFT, buff=0.28)
        panel.to_edge(RIGHT, buff=0.45).shift(UP * 0.15)
        return {
            "group": panel,
            "title": title,
            "theorem": theorem,
            "right_angle": right_angle,
            "tangent_condition": tangent_condition,
            "result": result,
            "mirror": mirror,
        }


class ExternalTangentConstruction(CircleTangentConstructionBase, Scene):
    """Scene 1: compass-and-straightedge construction of two tangents."""

    def construct(self):
        self.setup_tangent_scene()

        title = self.make_title(
            "Tangents from an External Point",
            "Construct the two lines from P that just touch the circle.",
        )
        self.play(Write(title[0]), FadeIn(title[1], shift=DOWN * 0.14), run_time=1.3)

        diagram = self.make_core_diagram()
        o_group = diagram["points"][0]
        p_group = diagram["points"][1]
        m_group = diagram["points"][2]
        tangent_points = VGroup(diagram["points"][3], diagram["points"][4])

        caption = self.make_caption("Start with a circle centered at O and an external point P.")
        self.play(Create(diagram["circle"]), FadeIn(o_group, scale=1.15), run_time=1.1)
        self.play(FadeIn(p_group, scale=1.15), Write(caption), run_time=0.9)
        self.wait(0.35)

        caption = self.replace_caption(caption, "Draw the segment OP.")
        self.play(Create(diagram["op_line"]), run_time=0.85)
        self.wait(0.25)

        midpoint_marks = self.make_midpoint_marks()
        caption = self.replace_caption(caption, "Construct the midpoint M of OP.")
        self.play(FadeIn(m_group, scale=1.2), Create(midpoint_marks), run_time=0.95)
        self.play(Indicate(m_group, color=self.colors["aux"]), run_time=0.8)
        self.wait(0.3)

        caption = self.replace_caption(caption, "With center M, draw the circle through O and P.")
        radius_hint = VGroup(
            DashedLine(self.M, self.O, color=self.colors["aux"], stroke_width=2, dash_length=0.08),
            DashedLine(self.M, self.P, color=self.colors["aux"], stroke_width=2, dash_length=0.08),
        )
        self.play(Create(radius_hint), run_time=0.6)
        self.play(Create(diagram["auxiliary_circle"]), run_time=1.45)
        self.wait(0.3)

        caption = self.replace_caption(
            caption,
            "The two circles meet at the tangent points T1 and T2.",
        )
        self.play(
            LaggedStart(
                FadeIn(tangent_points[0], scale=1.2),
                FadeIn(tangent_points[1], scale=1.2),
                lag_ratio=0.22,
            ),
            run_time=1.05,
        )
        self.play(
            Circumscribe(tangent_points[0][0], color=self.colors["tangent"]),
            Circumscribe(tangent_points[1][0], color=self.colors["tangent"]),
            run_time=1.0,
        )
        self.wait(0.3)

        caption = self.replace_caption(caption, "Draw PT1 and PT2. These are the tangents.")
        self.play(
            LaggedStart(
                Create(diagram["tangent_1"]),
                Create(diagram["tangent_2"]),
                lag_ratio=0.2,
            ),
            run_time=1.35,
        )
        self.play(
            Create(diagram["radius_t1"]),
            Create(diagram["radius_t2"]),
            run_time=0.85,
        )
        self.play(
            diagram["auxiliary_circle"].animate.set_stroke(opacity=0.32),
            diagram["op_line"].animate.set_stroke(opacity=0.45),
            radius_hint.animate.set_opacity(0.25),
            midpoint_marks.animate.set_opacity(0.45),
            m_group.animate.set_opacity(0.65),
            run_time=0.8,
        )

        final_note = MathTex(
            r"PT_1 \text{ and } PT_2 \text{ touch the circle exactly once.}",
            font_size=34,
            color=self.colors["tangent"],
        )
        final_note.next_to(title, DOWN, buff=0.34)
        self.play(FadeOut(title[1]), Transform(caption, final_note), run_time=0.95)
        self.play(
            Circumscribe(diagram["tangent_1"], color=self.colors["tangent"]),
            Circumscribe(diagram["tangent_2"], color=self.colors["tangent"]),
            run_time=1.15,
        )
        self.wait(1.0)
        self.play(FadeOut(VGroup(title[0], caption, diagram["all"], radius_hint, midpoint_marks)), run_time=1.0)
        self.wait(0.5)


class WhyTheConstructionWorks(CircleTangentConstructionBase, Scene):
    """Scene 2: proof that the constructed lines are tangent."""

    def construct(self):
        self.setup_tangent_scene()

        title = self.make_title(
            "Why the Lines Are Tangents",
            "A circle with diameter OP forces a right angle at T.",
        )
        self.play(Write(title[0]), FadeIn(title[1], shift=DOWN * 0.14), run_time=1.2)

        diagram = self.make_core_diagram(faded_guides=True)
        diagram["all"].scale(0.88).to_edge(LEFT, buff=0.4).shift(DOWN * 0.18)
        self.play(FadeIn(diagram["all"], shift=RIGHT * 0.15), run_time=1.1)

        panel = self.make_proof_panel()
        panel["group"].next_to(diagram["all"], RIGHT, buff=0.45).shift(UP * 0.25)
        self.play(Write(panel["title"]), run_time=0.7)

        t1_group = diagram["points"][3]
        t2_group = diagram["points"][4]
        triangle_t1 = Polygon(
            diagram["points"][0][0].get_center(),
            t1_group[0].get_center(),
            diagram["points"][1][0].get_center(),
            color=self.colors["proof"],
            stroke_width=4,
            fill_color=self.colors["proof"],
            fill_opacity=0.16,
        )
        right_angle_t1 = RightAngle(
            Line(t1_group[0].get_center(), diagram["points"][0][0].get_center()),
            Line(t1_group[0].get_center(), diagram["points"][1][0].get_center()),
            length=0.22,
            color=YELLOW,
            stroke_width=4,
        )

        self.play(Create(triangle_t1), run_time=0.85)
        self.play(
            Circumscribe(diagram["auxiliary_circle"], color=self.colors["aux"]),
            Indicate(t1_group, color=self.colors["tangent"]),
            Write(panel["theorem"]),
            run_time=1.4,
        )
        self.wait(0.25)

        self.play(Create(right_angle_t1), Write(panel["right_angle"]), run_time=1.05)
        self.play(
            Indicate(right_angle_t1, color=YELLOW),
            Circumscribe(panel["right_angle"], color=YELLOW),
            run_time=0.9,
        )
        self.wait(0.25)

        radius_highlight = Line(
            diagram["points"][0][0].get_center(),
            t1_group[0].get_center(),
            color=self.colors["circle"],
            stroke_width=6,
        )
        tangent_highlight = Line(
            diagram["points"][1][0].get_center(),
            t1_group[0].get_center(),
            color=self.colors["tangent"],
            stroke_width=7,
        )
        self.play(Create(radius_highlight), Create(tangent_highlight), run_time=0.85)
        self.play(Write(panel["tangent_condition"]), run_time=0.8)
        self.play(Write(panel["result"]), run_time=0.9)
        self.wait(0.35)

        triangle_t2 = Polygon(
            diagram["points"][0][0].get_center(),
            t2_group[0].get_center(),
            diagram["points"][1][0].get_center(),
            color=self.colors["proof"],
            stroke_width=4,
            fill_color=self.colors["proof"],
            fill_opacity=0.14,
        )
        right_angle_t2 = RightAngle(
            Line(t2_group[0].get_center(), diagram["points"][0][0].get_center()),
            Line(t2_group[0].get_center(), diagram["points"][1][0].get_center()),
            length=0.22,
            color=YELLOW,
            stroke_width=4,
            quadrant=(-1, -1),
        )
        self.play(
            FadeOut(triangle_t1),
            FadeOut(radius_highlight),
            FadeOut(tangent_highlight),
            Create(triangle_t2),
            Create(right_angle_t2),
            Indicate(t2_group, color=self.colors["tangent"]),
            Write(panel["mirror"]),
            run_time=1.25,
        )
        self.wait(0.4)

        conclusion = Text(
            "A tangent is perpendicular to the radius at the point of contact.",
            font_size=26,
            color=self.colors["text"],
        )
        conclusion.to_edge(DOWN, buff=0.42)
        self.play(FadeIn(conclusion, shift=UP * 0.15), run_time=0.9)
        self.play(
            Circumscribe(diagram["tangent_1"], color=self.colors["tangent"]),
            Circumscribe(diagram["tangent_2"], color=self.colors["tangent"]),
            run_time=1.2,
        )
        self.wait(1.1)
        self.play(
            FadeOut(
                VGroup(
                    title,
                    diagram["all"],
                    panel["group"],
                    right_angle_t1,
                    right_angle_t2,
                    triangle_t2,
                    conclusion,
                )
            ),
            run_time=1.0,
        )
        self.wait(0.5)
