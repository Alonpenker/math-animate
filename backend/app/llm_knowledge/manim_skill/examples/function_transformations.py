from manim import *


def parent_function(x):
    return x**2


class FunctionTransformationBase:
    """Shared visual language for the function transformation scenes."""

    def setup_transformation_scene(self):
        self.camera.background_color = "#101820"
        self.colors = {
            "parent": TEAL_B,
            "translation": ORANGE,
            "scale": GREEN_B,
            "reflection": RED,
            "combined": YELLOW,
            "guide": GREY_B,
            "muted": GREY_A,
            "text": WHITE,
            "panel": BLUE_D,
        }

    def make_title(self, title_text, subtitle_text):
        title = Text(title_text, font_size=38, weight=BOLD)
        title.to_edge(UP, buff=0.32)

        subtitle = Text(subtitle_text, font_size=23, color=self.colors["muted"])
        subtitle.next_to(title, DOWN, buff=0.14)

        return VGroup(title, subtitle)

    def make_caption(self, text, font_size=24):
        caption = Text(text, font_size=font_size, color=self.colors["text"])
        caption.to_edge(DOWN, buff=0.42)
        return caption

    def replace_caption(self, old_caption, new_text):
        new_caption = self.make_caption(new_text)
        self.play(ReplacementTransform(old_caption, new_caption), run_time=0.75)
        return new_caption

    def make_axes(self):
        axes = Axes(
            x_range=[-4, 5, 1],
            y_range=[-5, 7, 1],
            x_length=6.6,
            y_length=5.25,
            axis_config={
                "color": self.colors["guide"],
                "stroke_width": 2,
                "include_tip": True,
            },
            x_axis_config={
                "numbers_to_include": [-4, -2, 0, 2, 4],
                "font_size": 21,
            },
            y_axis_config={
                "numbers_to_include": [-4, -2, 0, 2, 4, 6],
                "font_size": 21,
            },
        )
        axes.to_edge(LEFT, buff=0.48).shift(DOWN * 0.35)

        x_label = axes.get_x_axis_label(MathTex("x", font_size=25))
        y_label = axes.get_y_axis_label(MathTex("y", font_size=25))

        return axes, VGroup(x_label, y_label)

    def make_parent_graph(self, axes, opacity=1.0, stroke_width=5):
        graph = axes.plot(
            parent_function,
            x_range=[-2.55, 2.55],
            color=self.colors["parent"],
            stroke_width=stroke_width,
        )
        graph.set_opacity(opacity)

        label = axes.get_graph_label(
            graph,
            label=MathTex(r"f(x)=x^2", font_size=29, color=self.colors["parent"]),
            x_val=2.12,
            direction=UR,
        )
        label.shift(RIGHT * 0.16 + DOWN * 0.04)
        label.set_opacity(opacity)

        return graph, label

    def make_vertex_marker(self, axes, x, y, label, color, direction=UR):
        dot = Dot(axes.c2p(x, y), radius=0.07, color=color)
        text = MathTex(label, font_size=29, color=color)
        text.next_to(dot, direction, buff=0.1)
        return VGroup(dot, text)

    def make_equation_panel(self, equation, color, notes=None, font_size=34):
        equation_mob = MathTex(equation, font_size=font_size, color=color)
        equation_mob.to_edge(RIGHT, buff=0.98).shift(UP * 1.55)

        items = VGroup()
        if notes:
            for note in notes:
                item = Text(note, font_size=22, color=self.colors["text"])
                items.add(item)
            items.arrange(DOWN, aligned_edge=LEFT, buff=0.18)
            items.next_to(equation_mob, DOWN, buff=0.35).align_to(equation_mob, LEFT)

        return VGroup(equation_mob, items)

    def make_rule_panel(self):
        equation = MathTex(
            r"g(x)=",
            r"a",
            r"f(",
            r"b",
            r"(x-",
            r"h",
            r"))+",
            r"k",
            font_size=38,
        )
        equation[1].set_color(self.colors["scale"])
        equation[3].set_color(self.colors["reflection"])
        equation[5].set_color(self.colors["translation"])
        equation[7].set_color(self.colors["combined"])
        equation.to_edge(RIGHT, buff=0.98).shift(UP * 1.35)

        rows = VGroup(
            self.make_parameter_row("a", "vertical scale or x-axis reflection", self.colors["scale"]),
            self.make_parameter_row("b", "horizontal scale or y-axis reflection", self.colors["reflection"]),
            self.make_parameter_row("h", "horizontal shift", self.colors["translation"]),
            self.make_parameter_row("k", "vertical shift", self.colors["combined"]),
        )
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        rows.next_to(equation, DOWN, buff=0.35).align_to(equation, LEFT)

        return VGroup(equation, rows), equation, rows

    def make_parameter_row(self, symbol, description, color):
        symbol_mob = MathTex(symbol, font_size=28, color=color)
        desc = Text(description, font_size=20, color=self.colors["text"])
        row = VGroup(symbol_mob, desc)
        row.arrange(RIGHT, buff=0.18)
        return row

    def make_graph_setup(self, parent_opacity=1.0):
        axes, axis_labels = self.make_axes()
        parent_graph, parent_label = self.make_parent_graph(axes, opacity=parent_opacity)
        origin_vertex = self.make_vertex_marker(
            axes,
            0,
            0,
            r"(0,0)",
            self.colors["parent"],
            direction=DL,
        )

        return {
            "axes": axes,
            "axis_labels": axis_labels,
            "parent_graph": parent_graph,
            "parent_label": parent_label,
            "origin_vertex": origin_vertex,
        }

    def make_translation_annotation(self, axes):
        color = self.colors["translation"]
        start = axes.c2p(0, 0)
        mid = axes.c2p(2, 0)
        end = axes.c2p(2, 1)
        right_arrow = Arrow(start, mid, buff=0.12, color=color, stroke_width=4, max_tip_length_to_length_ratio=0.14)
        up_arrow = Arrow(mid, end, buff=0.12, color=color, stroke_width=4, max_tip_length_to_length_ratio=0.22)

        right_label = Text("right 2", font_size=21, color=color)
        right_label.next_to(right_arrow, DOWN, buff=0.08)
        up_label = Text("up 1", font_size=21, color=color)
        up_label.next_to(up_arrow, RIGHT, buff=0.08)

        old_vertex = Dot(start, radius=0.06, color=self.colors["parent"])
        new_vertex = self.make_vertex_marker(axes, 2, 1, r"(2,1)", color, direction=UR)
        return VGroup(right_arrow, up_arrow, right_label, up_label, old_vertex, new_vertex)

    def make_scale_annotation(self, axes):
        color = self.colors["scale"]
        left_arrow = Arrow(
            axes.c2p(-1, 1),
            axes.c2p(-1, 2),
            buff=0.08,
            color=color,
            stroke_width=4,
            max_tip_length_to_length_ratio=0.25,
        )
        right_arrow = Arrow(
            axes.c2p(1, 1),
            axes.c2p(1, 2),
            buff=0.08,
            color=color,
            stroke_width=4,
            max_tip_length_to_length_ratio=0.25,
        )
        points = VGroup(
            Dot(axes.c2p(-1, 1), radius=0.045, color=self.colors["parent"]),
            Dot(axes.c2p(1, 1), radius=0.045, color=self.colors["parent"]),
            Dot(axes.c2p(-1, 2), radius=0.055, color=color),
            Dot(axes.c2p(1, 2), radius=0.055, color=color),
        )
        label = Text("same x, double y", font_size=21, color=color)
        label.move_to(axes.c2p(0, 2.7))
        return VGroup(left_arrow, right_arrow, points, label)

    def make_reflection_annotation(self, axes):
        color = self.colors["reflection"]
        x_axis_highlight = DashedLine(
            axes.c2p(-3.75, 0),
            axes.c2p(4.75, 0),
            color=color,
            stroke_width=3,
            dash_length=0.13,
        )
        mirror_arrow = Arrow(
            axes.c2p(1, 1),
            axes.c2p(1, -1),
            buff=0.08,
            color=color,
            stroke_width=4,
            max_tip_length_to_length_ratio=0.16,
        )
        source_dot = Dot(axes.c2p(1, 1), radius=0.05, color=self.colors["parent"])
        reflected_dot = Dot(axes.c2p(1, -1), radius=0.06, color=color)
        label = Text("mirror over x-axis", font_size=21, color=color)
        label.next_to(x_axis_highlight, DOWN, buff=0.16).shift(RIGHT * 1.35)
        return VGroup(x_axis_highlight, mirror_arrow, source_dot, reflected_dot, label)

    def make_combined_annotation(self, axes):
        color = self.colors["combined"]
        vertex = self.make_vertex_marker(axes, 2, 3, r"(2,3)", color, direction=UR)
        guide_x = DashedLine(
            axes.c2p(2, 0),
            axes.c2p(2, 3),
            color=self.colors["guide"],
            stroke_width=2,
            dash_length=0.09,
        )
        guide_y = DashedLine(
            axes.c2p(0, 3),
            axes.c2p(2, 3),
            color=self.colors["guide"],
            stroke_width=2,
            dash_length=0.09,
        )
        vertex_label = Text("new vertex", font_size=21, color=color)
        vertex_label.next_to(vertex, UP, buff=0.08)
        return VGroup(guide_x, guide_y, vertex, vertex_label)


class ParentFunctionIntro(FunctionTransformationBase, Scene):
    """Scene 1: introduce the parent graph and transformation rule."""

    def construct(self):
        self.setup_transformation_scene()

        title = self.make_title(
            "Parent Function Transformations",
            "Start with one familiar graph, then move, stretch, and reflect it.",
        )
        setup = self.make_graph_setup(parent_opacity=1.0)
        graph_group = VGroup(
            setup["axes"],
            setup["axis_labels"],
            setup["parent_graph"],
            setup["parent_label"],
            setup["origin_vertex"],
        )

        self.play(Write(title[0]), FadeIn(title[1], shift=DOWN * 0.14), run_time=1.2)
        self.play(Create(setup["axes"]), FadeIn(setup["axis_labels"]), run_time=1.0)
        self.play(Create(setup["parent_graph"]), FadeIn(setup["parent_label"]), run_time=1.25)
        self.play(FadeIn(setup["origin_vertex"], scale=1.15), run_time=0.75)

        caption = self.make_caption("The parent graph is the starting shape.")
        self.play(Write(caption), run_time=0.8)
        self.play(Circumscribe(setup["origin_vertex"][0], color=self.colors["parent"]), run_time=0.8)

        rule_panel, rule_equation, rows = self.make_rule_panel()
        caption = self.replace_caption(caption, "Each parameter changes the parent in a predictable way.")
        self.play(Write(rule_equation), run_time=1.15)
        self.play(LaggedStart(*[FadeIn(row, shift=UP * 0.08) for row in rows], lag_ratio=0.18), run_time=1.6)

        for row in rows:
            self.play(Indicate(row, color=row[0].get_color()), run_time=0.55)
            self.wait(0.08)

        takeaway = MathTex(r"g(x)\text{ is still built from }f(x)", font_size=34, color=self.colors["text"])
        takeaway.next_to(rule_panel, DOWN, buff=0.42).align_to(rule_panel, LEFT)
        self.play(Write(takeaway), run_time=1.0)
        self.wait(0.9)

        self.play(FadeOut(VGroup(title, graph_group, caption, rule_panel, takeaway)), run_time=1.0)
        self.wait(0.4)


class TransformationSuite(FunctionTransformationBase, Scene):
    """Scene 2: overlay transformed graphs against the parent graph."""

    def construct(self):
        self.setup_transformation_scene()

        title = self.make_title(
            "Overlay the Transformations",
            "The blue parent graph stays visible as every new graph appears.",
        )
        setup = self.make_graph_setup(parent_opacity=0.32)
        axes = setup["axes"]
        parent_reference = VGroup(setup["parent_graph"], setup["parent_label"], setup["origin_vertex"])
        base_group = VGroup(axes, setup["axis_labels"], parent_reference)

        self.play(Write(title[0]), FadeIn(title[1], shift=DOWN * 0.14), run_time=1.2)
        self.play(Create(axes), FadeIn(setup["axis_labels"]), run_time=1.0)
        self.play(Create(setup["parent_graph"]), FadeIn(setup["parent_label"]), FadeIn(setup["origin_vertex"]), run_time=1.1)

        caption = self.make_caption("The blue graph is f(x)=x^2, our reference.")
        self.play(Write(caption), run_time=0.75)
        self.wait(0.25)

        active_graph = None
        active_label = None
        active_annotation = None
        active_panel = None

        steps = [
            {
                "function": lambda x: (x - 2) ** 2 + 1,
                "x_range": [-0.45, 4.45],
                "color": self.colors["translation"],
                "label": r"g(x)=(x-2)^2+1",
                "label_x": 3.35,
                "direction": UR,
                "label_shift": LEFT * 0.35,
                "panel": self.make_equation_panel(
                    r"g(x)=(x-2)^2+1",
                    self.colors["translation"],
                    ["right 2", "up 1"],
                ),
                "annotation": self.make_translation_annotation(axes),
                "caption": "Inside minus 2 moves the graph right; outside plus 1 moves it up.",
            },
            {
                "function": lambda x: 2 * x**2,
                "x_range": [-1.82, 1.82],
                "color": self.colors["scale"],
                "label": r"g(x)=2x^2",
                "label_x": 1.55,
                "direction": UR,
                "label_shift": ORIGIN,
                "panel": self.make_equation_panel(
                    r"g(x)=2x^2",
                    self.colors["scale"],
                    ["outside multiplier", "doubles y-values"],
                ),
                "annotation": self.make_scale_annotation(axes),
                "caption": "Multiplying outside f(x) changes vertical distances from the x-axis.",
            },
            {
                "function": lambda x: -(x**2),
                "x_range": [-2.22, 2.22],
                "color": self.colors["reflection"],
                "label": r"g(x)=-x^2",
                "label_x": 1.25,
                "direction": DR,
                "label_shift": LEFT * 0.35,
                "panel": self.make_equation_panel(
                    r"g(x)=-x^2",
                    self.colors["reflection"],
                    ["negative outside", "reflect across x-axis"],
                ),
                "annotation": self.make_reflection_annotation(axes),
                "caption": "A negative outside flips every y-value to the other side of the x-axis.",
            },
            {
                "function": lambda x: -0.5 * (x - 2) ** 2 + 3,
                "x_range": [-2.0, 5.0],
                "color": self.colors["combined"],
                "label": r"g(x)=-\frac12(x-2)^2+3",
                "label_x": 4.35,
                "direction": DOWN,
                "label_shift": ORIGIN,
                "panel": self.make_equation_panel(
                    r"g(x)=-\frac12(x-2)^2+3",
                    self.colors["combined"],
                    ["reflect", "compress by 1/2", "right 2", "up 3"],
                    font_size=30,
                ),
                "annotation": self.make_combined_annotation(axes),
                "caption": "The final graph combines reflection, compression, and translation.",
            },
        ]

        for index, step in enumerate(steps):
            graph = axes.plot(
                step["function"],
                x_range=step["x_range"],
                color=step["color"],
                stroke_width=5,
            )
            graph_label = axes.get_graph_label(
                graph,
                label=MathTex(step["label"], font_size=27, color=step["color"]),
                x_val=step["label_x"],
                direction=step["direction"],
            )
            graph_label.shift(step["label_shift"])
            annotation = step["annotation"]
            panel = step["panel"]
            graph_bundle = VGroup(graph, graph_label)
            support_bundle = VGroup(annotation, panel)

            caption = self.replace_caption(caption, step["caption"])
            if index == 0:
                self.play(Create(graph), FadeIn(graph_label), run_time=1.15)
                self.play(LaggedStart(FadeIn(panel), Create(annotation), lag_ratio=0.22), run_time=1.25)
            else:
                self.play(
                    ReplacementTransform(active_graph, graph),
                    ReplacementTransform(active_label, graph_label),
                    FadeOut(VGroup(active_annotation, active_panel), shift=DOWN * 0.08),
                    run_time=0.95,
                )
                self.play(LaggedStart(FadeIn(panel), Create(annotation), lag_ratio=0.22), run_time=1.2)

            self.play(Circumscribe(graph_label, color=step["color"]), run_time=0.65)
            self.wait(0.5)

            active_graph = graph
            active_label = graph_label
            active_annotation = annotation
            active_panel = panel

        final_note = MathTex(
            r"g(x)=a f(b(x-h))+k",
            font_size=36,
            color=self.colors["text"],
        )
        final_note.to_edge(DOWN, buff=0.42)
        self.play(ReplacementTransform(caption, final_note), run_time=0.85)
        self.play(
            Indicate(active_graph, color=self.colors["combined"]),
            Indicate(parent_reference, color=self.colors["parent"]),
            run_time=1.2,
        )
        self.wait(1.0)

        self.play(
            FadeOut(VGroup(title, base_group, active_graph, active_label, active_annotation, active_panel, final_note)),
            run_time=1.0,
        )
        self.wait(0.4)
