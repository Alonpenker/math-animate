from manim import *


class MatrixTemplate(VisualTemplate):
    VALID_STATES = frozenset({
        "display",
        "product_setup",
        "product_progress",
        "product_complete",
    })

    def __init__(
        self,
        state: str,
        *,
        matrix: list[list[float]] | None = None,
        label: str = "A",
        left_matrix: list[list[float]] | None = None,
        right_matrix: list[list[float]] | None = None,
        left_label: str = "A",
        right_label: str = "B",
        result_label: str = "C",
        active_row: int = 0,
        active_column: int = 0,
    ):
        state = self._validate_state(state)
        self.active_row = active_row
        self.active_column = active_column

        if state == "display":
            values = self._validate_matrix(matrix, "matrix")
            self.display_matrix = self._matrix_bundle(values, label, TEAL_B)
            self.row_highlight = VGroup(VectorizedPoint())
            self.column_highlight = VGroup(VectorizedPoint())
            self.cell_highlight = VGroup(VectorizedPoint())
            super().__init__(
                self.display_matrix["group"],
                self.row_highlight,
                self.column_highlight,
                self.cell_highlight,
                state=state,
            )
            return

        self.left_values = self._validate_matrix(left_matrix, "left_matrix")
        self.right_values = self._validate_matrix(right_matrix, "right_matrix")
        if len(self.left_values[0]) != len(self.right_values):
            raise ValueError("matrix multiplication inner dimensions must match")
        self.result_values = self._multiply(self.left_values, self.right_values)
        self._validate_product_cell(active_row, active_column)

        self.left = self._matrix_bundle(self.left_values, left_label, TEAL_B)
        self.right = self._matrix_bundle(self.right_values, right_label, GOLD)
        result_display = (
            self.result_values
            if state == "product_complete"
            else [["?" for _ in row] for row in self.result_values]
        )
        self.result = self._matrix_bundle(result_display, result_label, GREEN_B)
        times = MathTex(r"\times", color=GREY_A)
        equals = MathTex("=", color=GREY_A)
        product = VGroup(
            self.left["group"],
            times,
            self.right["group"],
            equals,
            self.result["group"],
        ).arrange(RIGHT, buff=0.42)

        self.row_highlight = self._row_highlight(self.left, active_row)
        self.column_highlight = self._column_highlight(self.right, active_column)
        self.cell_highlight = self._cell_highlight(self.result, active_row, active_column)
        self.formula = self._product_formula(active_row, active_column)
        self.formula.next_to(product, DOWN, buff=0.45)
        progress = VGroup(
            self.row_highlight,
            self.column_highlight,
            self.cell_highlight,
            self.formula,
        )
        if state != "product_progress":
            progress.set_opacity(0)
        boundary = Rectangle(width=11.8, height=5.8).move_to(product).set_opacity(0)
        super().__init__(product, progress, boundary, state=state)

    def highlight_row(self, row: int) -> Animation:
        matrix = self.display_matrix if self.state == "display" else self.left
        if not 0 <= row < len(matrix["rows"]):
            raise ValueError("row index is outside the matrix")
        return Transform(self.row_highlight, self._row_highlight(matrix, row))

    def highlight_column(self, column: int) -> Animation:
        matrix = self.display_matrix if self.state == "display" else self.right
        if not 0 <= column < len(matrix["columns"]):
            raise ValueError("column index is outside the matrix")
        return Transform(self.column_highlight, self._column_highlight(matrix, column))

    def highlight_cell(self, row: int, column: int) -> Animation:
        matrix = self.display_matrix if self.state == "display" else self.result
        self._validate_cell(matrix, row, column)
        return Transform(self.cell_highlight, self._cell_highlight(matrix, row, column))

    def select_product_cell(self, row: int, column: int) -> Animation:
        if self.state not in {"product_setup", "product_progress"}:
            raise ValueError("select_product_cell requires a product setup or progress state")
        self._validate_product_cell(row, column)
        self.active_row, self.active_column = row, column
        target_formula = self._product_formula(row, column).move_to(self.formula)
        return AnimationGroup(
            Transform(self.row_highlight, self._row_highlight(self.left, row)),
            Transform(self.column_highlight, self._column_highlight(self.right, column)),
            Transform(self.cell_highlight, self._cell_highlight(self.result, row, column)),
            Transform(self.formula, target_formula),
        )

    def reveal_product_cell(self) -> Animation:
        if self.state not in {"product_setup", "product_progress"}:
            raise ValueError("reveal_product_cell requires a product setup or progress state")
        row, column = self.active_row, self.active_column
        entry = self.result["cells"][row][column]
        target = MathTex(str(self.result_values[row][column]), font_size=30, color=GREEN_B).move_to(entry)
        return AnimationGroup(
            Transform(entry, target),
            Circumscribe(entry, color=YELLOW, buff=0.08, fade_out=True),
        )

    @staticmethod
    def _validate_matrix(values, name: str) -> list[list[float]]:
        if not isinstance(values, list) or not values or not all(isinstance(row, list) and row for row in values):
            raise ValueError(f"{name} must be a non-empty rectangular list")
        width = len(values[0])
        if any(len(row) != width for row in values):
            raise ValueError(f"{name} must be rectangular")
        if not all(isinstance(value, (int, float)) for row in values for value in row):
            raise ValueError(f"{name} entries must be numeric")
        return values

    @staticmethod
    def _multiply(left: list[list[float]], right: list[list[float]]) -> list[list[float]]:
        return [
            [
                sum(left[row][index] * right[index][column] for index in range(len(right)))
                for column in range(len(right[0]))
            ]
            for row in range(len(left))
        ]

    def _validate_product_cell(self, row: int, column: int) -> None:
        if not 0 <= row < len(self.result_values) or not 0 <= column < len(self.result_values[0]):
            raise ValueError("product cell is outside the result matrix")

    @staticmethod
    def _matrix_bundle(values, label: str, color: ManimColor) -> dict:
        rows_count, columns_count = len(values), len(values[0])
        cells = []
        entries = VGroup()
        for row_index, row in enumerate(values):
            cell_row = []
            for column_index, value in enumerate(row):
                entry = MathTex(str(value), font_size=30, color=color)
                entry.move_to(
                    RIGHT * (column_index - (columns_count - 1) / 2) * 0.7
                    + DOWN * (row_index - (rows_count - 1) / 2) * 0.58
                )
                entries.add(entry)
                cell_row.append(entry)
            cells.append(cell_row)
        body = Rectangle(
            width=columns_count * 0.7 + 0.45,
            height=rows_count * 0.58 + 0.42,
        ).set_opacity(0)
        left_line = Line(body.get_corner(UL), body.get_corner(DL), color=color, stroke_width=4)
        right_line = Line(body.get_corner(UR), body.get_corner(DR), color=color, stroke_width=4)
        brackets = VGroup(
            left_line,
            Line(left_line.get_start(), left_line.get_start() + RIGHT * 0.15, color=color, stroke_width=4),
            Line(left_line.get_end(), left_line.get_end() + RIGHT * 0.15, color=color, stroke_width=4),
            right_line,
            Line(right_line.get_start(), right_line.get_start() + LEFT * 0.15, color=color, stroke_width=4),
            Line(right_line.get_end(), right_line.get_end() + LEFT * 0.15, color=color, stroke_width=4),
        )
        name = MathTex(label, font_size=30, color=color).next_to(body, UP, buff=0.12)
        dimensions = MathTex(
            rf"{rows_count}\times{columns_count}",
            font_size=22,
            color=GREY_A,
        ).next_to(body, DOWN, buff=0.12)
        group = VGroup(body, brackets, entries, name, dimensions)
        return {
            "group": group,
            "cells": cells,
            "rows": [VGroup(*row) for row in cells],
            "columns": [VGroup(*[row[column] for row in cells]) for column in range(columns_count)],
        }

    @staticmethod
    def _validate_cell(matrix: dict, row: int, column: int) -> None:
        if not 0 <= row < len(matrix["rows"]) or not 0 <= column < len(matrix["columns"]):
            raise ValueError("cell is outside the matrix")

    @staticmethod
    def _row_highlight(matrix: dict, row: int) -> VGroup:
        return VGroup(SurroundingRectangle(
            matrix["rows"][row],
            color=BLUE_C,
            buff=0.12,
            fill_color=BLUE_C,
            fill_opacity=0.14,
        ))

    @staticmethod
    def _column_highlight(matrix: dict, column: int) -> VGroup:
        return VGroup(SurroundingRectangle(
            matrix["columns"][column],
            color=ORANGE,
            buff=0.12,
            fill_color=ORANGE,
            fill_opacity=0.14,
        ))

    @staticmethod
    def _cell_highlight(matrix: dict, row: int, column: int) -> VGroup:
        return VGroup(SurroundingRectangle(
            matrix["cells"][row][column],
            color=GREEN_B,
            buff=0.1,
            fill_color=GREEN_B,
            fill_opacity=0.14,
        ))

    def _product_formula(self, row: int, column: int) -> MathTex:
        terms = [
            rf"{self.left_values[row][index]}\cdot {self.right_values[index][column]}"
            for index in range(len(self.right_values))
        ]
        return MathTex(
            rf"c_{{{row + 1}{column + 1}}}=" + "+".join(terms),
            font_size=28,
            color=YELLOW,
        )
