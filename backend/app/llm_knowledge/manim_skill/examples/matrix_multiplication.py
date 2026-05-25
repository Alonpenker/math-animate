from manim import *


class MatrixMultiplicationBase:
    """Shared visual language for the matrix multiplication scenes."""

    def setup_matrix_scene(self):
        self.camera.background_color = "#101820"
        self.A = [[1, 2, 3], [4, 0, 1]]
        self.B = [[2, 1], [0, 3], [5, 2]]
        self.C = [[17, 13], [13, 6]]
        self.cell_width = 0.68
        self.cell_height = 0.55
        self.colors = {
            "a": TEAL_B,
            "b": GOLD,
            "c": GREEN_B,
            "row": BLUE_C,
            "column": ORANGE,
            "pair": YELLOW,
            "guide": GREY_B,
            "muted": GREY_A,
            "text": WHITE,
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

    def make_matrix_display(self, values, name, color, unknown=False, font_size=31):
        rows = len(values)
        cols = len(values[0])
        entries = VGroup()
        cells = []

        for i, row in enumerate(values):
            cell_row = []
            for j, value in enumerate(row):
                label = "?" if unknown else str(value)
                entry = MathTex(label, font_size=font_size, color=color)
                entry.move_to(
                    RIGHT * (j - (cols - 1) / 2) * self.cell_width
                    + DOWN * (i - (rows - 1) / 2) * self.cell_height
                )
                entries.add(entry)
                cell_row.append(entry)
            cells.append(cell_row)

        body = Rectangle(
            width=cols * self.cell_width + 0.38,
            height=rows * self.cell_height + 0.36,
            color=color,
            stroke_width=0,
            stroke_opacity=0,
            fill_opacity=0,
        )
        left_bracket = Line(body.get_corner(UL), body.get_corner(DL), color=color, stroke_width=4)
        right_bracket = Line(body.get_corner(UR), body.get_corner(DR), color=color, stroke_width=4)
        for bracket, direction in [(left_bracket, RIGHT), (right_bracket, LEFT)]:
            top_tick = Line(
                bracket.get_start(),
                bracket.get_start() + direction * 0.16,
                color=color,
                stroke_width=4,
            )
            bottom_tick = Line(
                bracket.get_end(),
                bracket.get_end() + direction * 0.16,
                color=color,
                stroke_width=4,
            )
            bracket.add(top_tick, bottom_tick)

        label = MathTex(name, font_size=34, color=color)
        label.next_to(body, UP, buff=0.16)
        dims = MathTex(f"{rows}\\times{cols}", font_size=26, color=self.colors["muted"])
        dims.next_to(body, DOWN, buff=0.13)

        matrix = VGroup(body, left_bracket, right_bracket, entries, label, dims)
        return {
            "group": matrix,
            "entries": entries,
            "cells": cells,
            "label": label,
            "dims": dims,
            "body": body,
        }

    def cell(self, matrix, row, col):
        return matrix["cells"][row][col]

    def row_group(self, matrix, row):
        return VGroup(*matrix["cells"][row])

    def column_group(self, matrix, col):
        return VGroup(*[row[col] for row in matrix["cells"]])

    def make_cell_highlight(self, entry, color, buff=0.1, opacity=0.22):
        return SurroundingRectangle(
            entry,
            color=color,
            buff=buff,
            stroke_width=3,
            fill_color=color,
            fill_opacity=opacity,
        )

    def make_row_highlight(self, matrix, row, color=None):
        return SurroundingRectangle(
            self.row_group(matrix, row),
            color=color or self.colors["row"],
            buff=0.14,
            stroke_width=4,
            fill_color=color or self.colors["row"],
            fill_opacity=0.16,
        )

    def make_column_highlight(self, matrix, col, color=None):
        return SurroundingRectangle(
            self.column_group(matrix, col),
            color=color or self.colors["column"],
            buff=0.14,
            stroke_width=4,
            fill_color=color or self.colors["column"],
            fill_opacity=0.16,
        )

    def make_result_highlight(self, matrix, row, col):
        return self.make_cell_highlight(self.cell(matrix, row, col), self.colors["c"], buff=0.13, opacity=0.18)

    def place_matrices_for_product(self, a_matrix, b_matrix, c_matrix=None):
        product = VGroup(a_matrix["group"], b_matrix["group"])
        product.arrange(RIGHT, buff=0.65)

        times = MathTex(r"\times", font_size=36, color=self.colors["muted"])
        times.move_to((a_matrix["body"].get_right() + b_matrix["body"].get_left()) / 2)
        group = VGroup(a_matrix["group"], times, b_matrix["group"])

        if c_matrix is not None:
            equals = MathTex(r"=", font_size=36, color=self.colors["muted"])
            c_matrix["group"].next_to(b_matrix["group"], RIGHT, buff=0.72)
            equals.move_to((b_matrix["body"].get_right() + c_matrix["body"].get_left()) / 2)
            group.add(equals, c_matrix["group"])

        group.move_to(UP * 0.45)
        return group

    def make_dot_product_formula(self, row, col, value, font_size=32):
        a_values = self.A[row]
        b_values = [self.B[k][col] for k in range(len(self.B))]
        terms = [
            rf"{a_values[k]}\cdot {b_values[k]}"
            for k in range(len(a_values))
        ]
        formula = MathTex(
            rf"c_{{{row + 1}{col + 1}}}",
            "=",
            terms[0],
            "+",
            terms[1],
            "+",
            terms[2],
            "=",
            str(value),
            font_size=font_size,
        )
        formula[0].set_color(self.colors["c"])
        formula[2].set_color(self.colors["pair"])
        formula[4].set_color(self.colors["pair"])
        formula[6].set_color(self.colors["pair"])
        formula[8].set_color(self.colors["c"])
        return formula

    def make_index_rule(self):
        rule = MathTex(
            r"c_{ij}",
            r"=",
            r"\sum_{k=1}^{3}",
            r"a_{ik}",
            r"b_{kj}",
            font_size=38,
        )
        rule[0].set_color(self.colors["c"])
        rule[2].set_color(self.colors["pair"])
        rule[3].set_color(self.colors["a"])
        rule[4].set_color(self.colors["b"])
        return rule

    def make_pair_connectors(self, a_matrix, b_matrix, row, col):
        connectors = VGroup()
        for k in range(3):
            a_cell = self.cell(a_matrix, row, k)
            b_cell = self.cell(b_matrix, k, col)
            connector = DashedLine(
                a_cell.get_center(),
                b_cell.get_center(),
                color=self.colors["pair"],
                stroke_width=2,
                dash_length=0.08,
            )
            connectors.add(connector)
        return connectors

    def set_unknown_result_entries(self, c_matrix, opacity=0.45):
        for entry in c_matrix["entries"]:
            entry.set_color(self.colors["muted"])
            entry.set_opacity(opacity)


class MatrixMultiplicationIdea(MatrixMultiplicationBase, Scene):
    """Scene 1: dimensions and the row-column idea."""

    def construct(self):
        self.setup_matrix_scene()

        title = self.make_title(
            "Matrix Multiplication",
            "A row of A combines with a column of B to make one entry.",
        )
        self.play(Write(title[0]), FadeIn(title[1], shift=DOWN * 0.14), run_time=1.3)

        a_matrix = self.make_matrix_display(self.A, "A", self.colors["a"])
        b_matrix = self.make_matrix_display(self.B, "B", self.colors["b"])
        product = self.place_matrices_for_product(a_matrix, b_matrix)
        product.shift(DOWN * 0.15)
        times = product[1]

        caption = self.make_caption("The inner dimensions must match: 2x3 times 3x2.")
        self.play(
            FadeIn(a_matrix["group"], shift=RIGHT * 0.2),
            Write(times),
            FadeIn(b_matrix["group"], shift=LEFT * 0.2),
            Write(caption),
            run_time=1.25,
        )

        inner_left = SurroundingRectangle(a_matrix["dims"][0][2], color=self.colors["pair"], buff=0.06)
        inner_right = SurroundingRectangle(b_matrix["dims"][0][0], color=self.colors["pair"], buff=0.06)
        self.play(Create(inner_left), Create(inner_right), run_time=0.75)
        self.play(
            Indicate(a_matrix["dims"][0][2], color=self.colors["pair"]),
            Indicate(b_matrix["dims"][0][0], color=self.colors["pair"]),
            run_time=1.0,
        )

        output_dims = MathTex(r"2\times", r"3", r"\cdot", r"3", r"\times2", r"\rightarrow", r"2\times2")
        output_dims.set_color(self.colors["muted"])
        output_dims[1].set_color(self.colors["pair"])
        output_dims[3].set_color(self.colors["pair"])
        output_dims[6].set_color(self.colors["c"])
        output_dims.next_to(product, DOWN, buff=0.55)
        self.play(Write(output_dims), run_time=1.0)
        self.wait(0.35)

        caption = self.replace_caption(caption, "The outside dimensions tell us the answer will be 2x2.")
        self.play(Circumscribe(output_dims[6], color=self.colors["c"]), run_time=0.9)
        self.wait(0.25)

        caption = self.replace_caption(caption, "To get c11, use row 1 of A and column 1 of B.")
        row_highlight = self.make_row_highlight(a_matrix, 0)
        col_highlight = self.make_column_highlight(b_matrix, 0)
        connectors = self.make_pair_connectors(a_matrix, b_matrix, 0, 0)
        rule = self.make_index_rule()
        rule.to_edge(RIGHT, buff=0.62).shift(DOWN * 1.95)

        self.play(
            FadeOut(inner_left),
            FadeOut(inner_right),
            Create(row_highlight),
            Create(col_highlight),
            run_time=0.85,
        )
        self.play(LaggedStart(*[Create(line) for line in connectors], lag_ratio=0.18), run_time=1.0)
        self.play(Write(rule), run_time=1.2)
        self.play(
            Indicate(rule[3], color=self.colors["a"]),
            Indicate(rule[4], color=self.colors["b"]),
            run_time=1.0,
        )

        formula = self.make_dot_product_formula(0, 0, self.C[0][0], font_size=34)
        formula.next_to(product, DOWN, buff=0.6).shift(LEFT * 0.3)
        self.play(FadeOut(output_dims), Write(formula), run_time=1.05)
        self.play(Circumscribe(formula[-1], color=self.colors["c"]), run_time=0.8)
        self.wait(0.7)

        self.play(
            FadeOut(VGroup(title, product, caption, row_highlight, col_highlight, connectors, rule, formula)),
            run_time=1.0,
        )
        self.wait(0.4)


class MatrixMultiplicationStepByStep(MatrixMultiplicationBase, Scene):
    """Scene 2: compute every entry of the product matrix."""

    def construct(self):
        self.setup_matrix_scene()

        title = self.make_title(
            "Build the Product Matrix",
            "Each output cell is one row-column dot product.",
        )
        self.play(Write(title[0]), FadeIn(title[1], shift=DOWN * 0.14), run_time=1.2)

        a_matrix = self.make_matrix_display(self.A, "A", self.colors["a"], font_size=29)
        b_matrix = self.make_matrix_display(self.B, "B", self.colors["b"], font_size=29)
        c_matrix = self.make_matrix_display(self.C, "C", self.colors["c"], unknown=True, font_size=29)
        self.set_unknown_result_entries(c_matrix)

        product = self.place_matrices_for_product(a_matrix, b_matrix, c_matrix)
        product.scale(0.96).shift(UP * 0.2)
        times = product[1]
        equals = product[3]

        caption = self.make_caption("We will fill C one entry at a time.")
        self.play(
            LaggedStart(
                FadeIn(a_matrix["group"], shift=RIGHT * 0.16),
                Write(times),
                FadeIn(b_matrix["group"], shift=LEFT * 0.16),
                Write(equals),
                FadeIn(c_matrix["group"], shift=LEFT * 0.16),
                lag_ratio=0.15,
            ),
            Write(caption),
            run_time=1.7,
        )

        formula_slot = MathTex(r"c_{ij}=\text{row }i\cdot\text{column }j", font_size=30)
        formula_slot.next_to(product, DOWN, buff=0.48)
        formula_slot.set_color(self.colors["muted"])
        self.play(Write(formula_slot), run_time=0.85)
        self.wait(0.25)

        result_entries = {}
        steps = [
            (0, 0, "c11 uses row 1 of A and column 1 of B."),
            (0, 1, "c12 uses row 1 of A and column 2 of B."),
            (1, 0, "c21 uses row 2 of A and column 1 of B."),
            (1, 1, "c22 uses row 2 of A and column 2 of B."),
        ]

        for row, col, caption_text in steps:
            caption = self.replace_caption(caption, caption_text)
            row_highlight = self.make_row_highlight(a_matrix, row)
            col_highlight = self.make_column_highlight(b_matrix, col)
            result_highlight = self.make_result_highlight(c_matrix, row, col)
            connectors = self.make_pair_connectors(a_matrix, b_matrix, row, col)
            formula = self.make_dot_product_formula(row, col, self.C[row][col], font_size=31)
            formula.move_to(formula_slot)

            self.play(
                Create(row_highlight),
                Create(col_highlight),
                Create(result_highlight),
                run_time=0.75,
            )
            self.play(LaggedStart(*[Create(line) for line in connectors], lag_ratio=0.16), run_time=0.9)
            self.play(ReplacementTransform(formula_slot, formula), run_time=0.85)
            formula_slot = formula

            value = MathTex(str(self.C[row][col]), font_size=29, color=self.colors["c"])
            value.move_to(self.cell(c_matrix, row, col))
            old_unknown = self.cell(c_matrix, row, col)
            self.play(
                ReplacementTransform(formula[-1].copy(), value),
                old_unknown.animate.set_opacity(0),
                run_time=0.8,
            )
            result_entries[(row, col)] = value
            self.play(Circumscribe(value, color=self.colors["c"]), run_time=0.55)
            self.wait(0.16)
            self.play(
                FadeOut(VGroup(row_highlight, col_highlight, result_highlight, connectors)),
                run_time=0.45,
            )

        final_caption = self.make_caption("The product is complete.")
        completed_c = VGroup(*result_entries.values())
        final_equation = MathTex(r"AB", "=", "C", font_size=42)
        final_equation[0].set_color(self.colors["pair"])
        final_equation[2].set_color(self.colors["c"])
        final_equation.next_to(product, DOWN, buff=0.52)

        self.play(ReplacementTransform(caption, final_caption), run_time=0.65)
        self.play(ReplacementTransform(formula_slot, final_equation), run_time=0.9)
        self.play(
            Circumscribe(completed_c, color=self.colors["c"]),
            Indicate(final_equation[2], color=self.colors["c"]),
            run_time=1.1,
        )
        self.wait(1.0)

        self.play(
            FadeOut(VGroup(title, product, final_caption, final_equation, completed_c)),
            run_time=1.0,
        )
        self.wait(0.4)
