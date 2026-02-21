from manim import *


class SineWaveTransformation(Scene):
    def construct(self):
        axes = Axes(
            x_range=[-PI, PI, PI / 2],
            y_range=[-1.5, 1.5, 0.5],
            axis_config={"include_numbers": True},
        )
        labels = axes.get_axis_labels(x_label="x", y_label="y")

        sin_graph = axes.plot(lambda x: np.sin(x), color=BLUE)
        sin_label = axes.get_graph_label(sin_graph, label="\\sin(x)")

        cos_graph = axes.plot(lambda x: np.cos(x), color=RED)
        cos_label = axes.get_graph_label(cos_graph, label="\\cos(x)")

        self.play(Create(axes), Write(labels))
        self.play(Create(sin_graph), Write(sin_label))
        self.wait(1)
        self.play(
            Transform(sin_graph, cos_graph),
            Transform(sin_label, cos_label),
        )
        self.wait(2)
