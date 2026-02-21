from manim import *


class AnimatedBarChart(Scene):
    def construct(self):
        chart = BarChart(
            values=[4, 6, 2, 8, 5],
            bar_names=["A", "B", "C", "D", "E"],
            y_range=[0, 10, 2],
            bar_colors=[BLUE, TEAL, GREEN, YELLOW, RED],
        )
        title = Text("Quarterly Sales", font_size=36).to_edge(UP)

        self.play(Write(title))
        self.play(Create(chart))
        self.wait(1)

        new_values = [7, 3, 9, 4, 6]
        self.play(chart.animate.change_bar_values(new_values))
        updated_title = Text("Updated Sales", font_size=36).to_edge(UP)
        self.play(Transform(title, updated_title))
        self.wait(2)
