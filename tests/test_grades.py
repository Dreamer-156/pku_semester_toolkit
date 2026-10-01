"""Grades use exact decimal arithmetic; no personal scores are stored."""

from decimal import Decimal
import unittest

from toolkit.grades import (
    GradeError, calculate_current, make_grade_item,
    minimum_hundredth, required_final_score,
)
from toolkit.grades_cli import run_grade_menu


class GradeTests(unittest.TestCase):
    def test_current_weighted_contribution_and_average(self):
        items = [
            make_grade_item("平时作业", "80", "30"),
            make_grade_item("期中考试", "90", "20"),
        ]
        current = calculate_current(items)
        self.assertEqual(current.completed_weight, Decimal("50"))
        self.assertEqual(current.contribution, Decimal("42"))
        self.assertEqual(current.completed_average, Decimal("84"))
        self.assertEqual(required_final_score(items, "50", "85"), Decimal("86"))

    def test_target_rounds_up_and_impossible_target_is_detectable(self):
        items = [make_grade_item("作业", "70", "70")]
        exact = required_final_score(items, "30", "75")
        minimum = minimum_hundredth(exact)
        self.assertEqual(minimum, Decimal("86.67"))
        self.assertGreaterEqual(Decimal("49") + minimum * Decimal("0.3"), Decimal("75"))
        impossible = required_final_score(items, "30", "90")
        self.assertGreater(impossible, Decimal("100"))
        self.assertEqual(required_final_score([make_grade_item("作业", 90, 70)], 30, 60), 0)

    def test_bad_scores_weights_and_missing_items(self):
        for score, weight in [
            ("abc", "20"), ("NaN", "20"), ("Infinity", "20"),
            ("-1", "20"), ("101", "20"), ("80", "0"), ("80", "-1"),
        ]:
            with self.assertRaises(GradeError):
                make_grade_item("项目", score, weight)
        with self.assertRaisesRegex(GradeError, "至少一项"):
            calculate_current([])
        with self.assertRaisesRegex(GradeError, "不能重复"):
            calculate_current([
                make_grade_item("Quiz", 90, 30),
                make_grade_item("quiz", 80, 20),
            ])
        with self.assertRaisesRegex(GradeError, "不能超过 100"):
            calculate_current([
                make_grade_item("A", 90, 60),
                make_grade_item("B", 80, 50),
            ])

    def test_final_requires_all_weights_and_valid_target(self):
        items = [make_grade_item("作业", 80, 40)]
        with self.assertRaisesRegex(GradeError, "恰好为 100"):
            required_final_score(items, 50, 80)
        with self.assertRaises(GradeError):
            required_final_score(items, 60, 101)
        with self.assertRaises(GradeError):
            required_final_score(items, 0, 80)

    def test_cli_input_current_and_target(self):
        answers = iter([
            "1", "平时作业", "80", "30", "期中", "90", "20", "",
            "2", "3", "50", "85", "4",
        ])
        messages = []
        run_grade_menu(input_func=lambda _prompt: next(answers), output_func=messages.append)
        output = "\n".join(messages)
        self.assertIn("已计入总评：42.00", output)
        self.assertIn("加权平均：84.00", output)
        self.assertIn("期末至少需要 86.00 分", output)

    def test_cli_invalid_item_does_not_erase_valid_entries(self):
        answers = iter([
            "1", "错误项", "NaN", "20", "有效项", "80", "40", "",
            "2", "4",
        ])
        messages = []
        run_grade_menu(input_func=lambda _prompt: next(answers), output_func=messages.append)
        output = "\n".join(messages)
        self.assertIn("该项未录入", output)
        self.assertIn("已计入总评：32.00", output)


if __name__ == "__main__":
    unittest.main()
