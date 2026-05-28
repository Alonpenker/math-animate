from manim import *


def quadratic(x):
    return x**2


class DerivativeLimitBase:
    """Shared visual language for the derivative-from-limits scenes."""

    def setup_derivative_scene(self):
        self.camera.background_color = "#101820"
        self.x0 = 1.0
        self.y0 = self.f(self.x0)
        self.colors = {
            "curve": TEAL_B,
            "point_p": YELLOW,
            "point_q": ORANGE,
            "secant": ORANGE,
            "tangent": GREEN_B,
            "guide": GREY_B,
            "text": WHITE,
            "muted": GREY_A,
        }

    def f(self, x):
        return quadratic(x)

    def make_title(self, title_text, subtitle_text):
        title = Text(title_text, font_size=38, weight=BOLD)
        title.to_edge(UP, buff=0.32)

        subtitle = Text(subtitle_text, font_size=24, color=self.colors["muted"])
        subtitle.next_to(title, DOWN, buff=0.14)

        return VGroup(title, subtitle)

    def make_graph_setup(self):
        axes = Axes(
            x_range=[-0.2, 2.8, 0.5],
            y_range=[-0.2, 6.6, 1],
            x_length=6.35,
            y_length=4.85,
            axis_config={
                "color": self.colors["guide"],
                "stroke_width": 2,
                "include_tip": True,
            },
            x_axis_config={
                "numbers_to_include": [0, 1, 2],
                "font_size": 22,
            },
            y_axis_config={
                "numbers_to_include": [0, 1, 4, 6],
                "font_size": 22,
            },
        )
        axes.to_edge(LEFT, buff=0.55).shift(DOWN * 0.35)

        graph = axes.plot(
            quadratic,
            x_range=[0, 2.55],
            color=self.colors["curve"],
            stroke_width=5,
        )
        graph_label = axes.get_graph_label(
            graph,
            label=MathTex(r"f(x)=x^2", font_size=30, color=self.colors["curve"]),
            x_val=2.25,
            direction=UR,
        )
        graph_label.shift(RIGHT * 0.28)

        x_label = axes.get_x_axis_label(MathTex("x", font_size=26))
        y_label = axes.get_y_axis_label(MathTex("y", font_size=26))

        p_dot = Dot(self.point_on_curve(axes, self.x0), radius=0.07, color=self.colors["point_p"])
        p_label = MathTex("P", font_size=32, color=self.colors["point_p"])
        p_label.next_to(p_dot, UL, buff=0.12)

        return {
            "axes": axes,
            "graph": graph,
            "graph_label": graph_label,
            "axis_labels": VGroup(x_label, y_label),
            "p_dot": p_dot,
            "p_label": p_label,
        }

    def point_on_curve(self, axes, x):
        return axes.c2p(x, self.f(x))

    def point_at_height(self, axes, x, y):
        return axes.c2p(x, y)

    def secant_slope(self, h):
        return (self.f(self.x0 + h) - self.y0) / h

    def make_secant_line(self, axes, h, color=None, stroke_width=5):
        slope = self.secant_slope(h)
        x_left = 0.55
        x_right = 2.45
        y_left = self.y0 + slope * (x_left - self.x0)
        y_right = self.y0 + slope * (x_right - self.x0)
        return Line(
            axes.c2p(x_left, y_left),
            axes.c2p(x_right, y_right),
            color=color or self.colors["secant"],
            stroke_width=stroke_width,
        )

    def make_tangent_line(self, axes, color=None, stroke_width=6):
        slope = 2 * self.x0
        x_left = 0.5
        x_right = 2.5
        y_left = self.y0 + slope * (x_left - self.x0)
        y_right = self.y0 + slope * (x_right - self.x0)
        return Line(
            axes.c2p(x_left, y_left),
            axes.c2p(x_right, y_right),
            color=color or self.colors["tangent"],
            stroke_width=stroke_width,
        )

    def make_moving_secant_group(self, axes, h_tracker, include_guides=True):
        q_dot = always_redraw(
            lambda: Dot(
                self.point_on_curve(axes, self.x0 + h_tracker.get_value()),
                radius=0.07,
                color=self.colors["point_q"],
            )
        )
        q_label = MathTex("Q", font_size=32, color=self.colors["point_q"])
        q_label.add_updater(lambda mob: mob.next_to(q_dot, UR, buff=0.12))

        secant = always_redraw(
            lambda: self.make_secant_line(
                axes,
                h_tracker.get_value(),
                color=self.colors["secant"],
            )
        )

        group = VGroup(secant, q_dot, q_label)
        result = {"secant": secant, "q_dot": q_dot, "q_label": q_label, "group": group}

        if include_guides:
            run_line = always_redraw(
                lambda: DashedLine(
                    self.point_at_height(axes, self.x0, self.y0),
                    self.point_at_height(axes, self.x0 + h_tracker.get_value(), self.y0),
                    color=self.colors["guide"],
                    stroke_width=2,
                    dash_length=0.09,
                )
            )
            rise_line = always_redraw(
                lambda: DashedLine(
                    self.point_at_height(axes, self.x0 + h_tracker.get_value(), self.y0),
                    self.point_on_curve(axes, self.x0 + h_tracker.get_value()),
                    color=self.colors["guide"],
                    stroke_width=2,
                    dash_length=0.09,
                )
            )
            h_label = MathTex("h", font_size=26, color=self.colors["point_q"])
            h_label.add_updater(lambda mob: mob.next_to(run_line, DOWN, buff=0.08))
            rise_label = Text("rise", font_size=20, color=self.colors["muted"])
            rise_label.add_updater(lambda mob: mob.next_to(rise_line, RIGHT, buff=0.08))
            guides = VGroup(run_line, rise_line, h_label, rise_label)
            group.add(guides)
            result["guides"] = guides

        return result

    def make_average_slope_panel(self, h_tracker):
        title = Text("Average slope", font_size=27, weight=BOLD)
        formula = MathTex(
            r"\frac{\text{rise}}{\text{run}}",
            r"=",
            r"\frac{f(1+h)-f(1)}{h}",
            font_size=34,
        )
        formula[0].set_color(self.colors["guide"])
        formula[2].set_color(self.colors["secant"])

        h_text = Text("h =", font_size=23, color=self.colors["muted"])
        h_number = DecimalNumber(
            h_tracker.get_value(),
            num_decimal_places=2,
            font_size=28,
            color=self.colors["point_q"],
        )
        h_number.next_to(h_text, RIGHT, buff=0.12)
        h_number.add_updater(
            lambda mob: mob.set_value(h_tracker.get_value()).next_to(h_text, RIGHT, buff=0.12)
        )

        slope_text = Text("secant slope =", font_size=23, color=self.colors["muted"])
        slope_number = DecimalNumber(
            self.secant_slope(h_tracker.get_value()),
            num_decimal_places=2,
            font_size=28,
            color=self.colors["secant"],
        )
        slope_number.next_to(slope_text, RIGHT, buff=0.12)
        slope_number.add_updater(
            lambda mob: mob.set_value(self.secant_slope(h_tracker.get_value())).next_to(
                slope_text, RIGHT, buff=0.12
            )
        )

        h_row = VGroup(h_text, h_number)
        slope_row = VGroup(slope_text, slope_number)
        panel = VGroup(title, formula, h_row, slope_row).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        panel.move_to(RIGHT * 3.35 + UP * 0.55)

        return panel

    def make_limit_panel(self):
        title = Text("Limit of secant slopes", font_size=27, weight=BOLD)

        definition = MathTex(
            r"f'(1)",
            r"=",
            r"\lim_{h\to 0}",
            r"\frac{f(1+h)-f(1)}{h}",
            font_size=33,
        )
        definition[0].set_color(self.colors["tangent"])
        definition[2].set_color(self.colors["point_q"])
        definition[3].set_color(self.colors["secant"])

        step_one = MathTex(
            r"=",
            r"\lim_{h\to 0}",
            r"\frac{(1+h)^2-1}{h}",
            font_size=32,
        )
        step_one[1].set_color(self.colors["point_q"])

        step_two = MathTex(
            r"=",
            r"\lim_{h\to 0}",
            r"(2+h)",
            font_size=32,
        )
        step_two[1].set_color(self.colors["point_q"])

        result = MathTex(r"f'(1)", r"=", r"2", font_size=46)
        result[0].set_color(self.colors["tangent"])
        result[2].set_color(self.colors["point_p"])

        panel = VGroup(title, definition, step_one, step_two, result).arrange(
            DOWN,
            aligned_edge=LEFT,
            buff=0.32,
        )
        panel.move_to(RIGHT * 3.25 + UP * 0.25)
        return {
            "group": panel,
            "title": title,
            "definition": definition,
            "step_one": step_one,
            "step_two": step_two,
            "result": result,
        }


class SecantSlopeAsAverageChange(DerivativeLimitBase, Scene):
    """Scene 1: a secant line measures average change."""

    def construct(self):
        self.setup_derivative_scene()

        title = self.make_title(
            "Derivatives From Limits",
            "Start with the slope between two nearby points.",
        )
        setup = self.make_graph_setup()
        graph_group = VGroup(
            setup["axes"],
            setup["axis_labels"],
            setup["graph"],
            setup["graph_label"],
            setup["p_dot"],
            setup["p_label"],
        )

        self.play(Write(title[0]), FadeIn(title[1], shift=DOWN * 0.15), run_time=1.3)
        self.play(Create(setup["axes"]), Write(setup["axis_labels"]), run_time=1.0)
        self.play(Create(setup["graph"]), FadeIn(setup["graph_label"]), run_time=1.5)
        self.play(FadeIn(setup["p_dot"], scale=1.25), Write(setup["p_label"]), run_time=0.75)

        h_tracker = ValueTracker(1.15)
        secant_parts = self.make_moving_secant_group(setup["axes"], h_tracker, include_guides=True)
        panel = self.make_average_slope_panel(h_tracker)

        self.play(
            FadeIn(secant_parts["q_dot"], scale=1.2),
            Write(secant_parts["q_label"]),
            Create(secant_parts["secant"]),
            run_time=1.0,
        )
        self.play(Create(secant_parts["guides"]), run_time=0.85)
        self.play(Write(panel[0]), Write(panel[1]), run_time=1.25)
        self.play(FadeIn(panel[2], shift=UP * 0.08), FadeIn(panel[3], shift=UP * 0.08), run_time=0.8)
        self.wait(0.35)

        for value, runtime in [(0.75, 1.25), (0.42, 1.25), (0.2, 1.45)]:
            self.play(h_tracker.animate.set_value(value), run_time=runtime, rate_func=smooth)
            self.wait(0.18)

        note = Text(
            "As Q gets closer to P, the secant slope approaches one special slope.",
            font_size=24,
            color=self.colors["text"],
        )
        note.to_edge(DOWN, buff=0.45)
        self.play(FadeIn(note, shift=UP * 0.15), run_time=0.9)
        self.play(Indicate(secant_parts["secant"], color=self.colors["point_p"]), run_time=1.0)
        self.wait(0.85)

        self.play(FadeOut(VGroup(title, graph_group, secant_parts["group"], panel, note)), run_time=1.0)
        self.wait(0.4)


class LimitBecomesTangent(DerivativeLimitBase, Scene):
    """Scene 2: the limiting secant line is the tangent line."""

    def construct(self):
        self.setup_derivative_scene()

        title = self.make_title(
            "The Limit Becomes the Tangent",
            "Let the horizontal gap h shrink toward zero.",
        )
        setup = self.make_graph_setup()
        graph_group = VGroup(
            setup["axes"],
            setup["axis_labels"],
            setup["graph"],
            setup["graph_label"],
            setup["p_dot"],
            setup["p_label"],
        )

        h_tracker = ValueTracker(0.7)
        secant_parts = self.make_moving_secant_group(setup["axes"], h_tracker, include_guides=False)
        limit_hint = MathTex(r"h\to 0", font_size=38, color=self.colors["point_q"])
        limit_hint.move_to(RIGHT * 3.3 + UP * 1.95)

        self.play(Write(title[0]), FadeIn(title[1], shift=DOWN * 0.15), run_time=1.2)
        self.play(Create(setup["axes"]), Create(setup["graph"]), FadeIn(setup["axis_labels"]), run_time=1.35)
        self.play(
            FadeIn(setup["graph_label"]),
            FadeIn(setup["p_dot"], scale=1.2),
            Write(setup["p_label"]),
            run_time=0.8,
        )
        self.play(
            Create(secant_parts["secant"]),
            FadeIn(secant_parts["q_dot"], scale=1.2),
            Write(secant_parts["q_label"]),
            Write(limit_hint),
            run_time=1.1,
        )
        self.wait(0.25)

        self.play(h_tracker.animate.set_value(0.28), run_time=1.8, rate_func=smooth)
        self.play(h_tracker.animate.set_value(0.08), run_time=1.7, rate_func=smooth)
        self.wait(0.2)

        tangent = self.make_tangent_line(setup["axes"])
        tangent_label = Text("tangent slope", font_size=24, color=self.colors["tangent"])
        tangent_label.move_to(setup["axes"].c2p(1.78, 1.6))

        secant_parts["secant"].clear_updaters()
        self.play(
            Transform(secant_parts["secant"], tangent),
            FadeOut(secant_parts["q_dot"], scale=0.6),
            FadeOut(secant_parts["q_label"]),
            FadeOut(limit_hint, shift=UP * 0.1),
            run_time=1.0,
        )
        self.play(Write(tangent_label), run_time=0.7)

        panel = self.make_limit_panel()
        self.play(Write(panel["title"]), Write(panel["definition"]), run_time=1.35)
        self.wait(0.3)
        self.play(Write(panel["step_one"]), run_time=1.0)
        self.play(Write(panel["step_two"]), run_time=0.9)
        self.play(Write(panel["result"]), run_time=0.9)
        self.play(
            Circumscribe(panel["result"], color=self.colors["point_p"]),
            Indicate(secant_parts["secant"], color=self.colors["tangent"]),
            run_time=1.2,
        )

        takeaway = Text(
            "A derivative is the limit of slopes of secant lines.",
            font_size=26,
            color=self.colors["text"],
        )
        takeaway.to_edge(DOWN, buff=0.45)
        self.play(FadeIn(takeaway, shift=UP * 0.15), run_time=0.85)
        self.wait(1.0)

        self.play(
            FadeOut(VGroup(title, graph_group, secant_parts["secant"], tangent_label, panel["group"], takeaway)),
            run_time=1.0,
        )
        self.wait(0.4)
