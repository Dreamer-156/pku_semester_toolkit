"""Basic behavior checks for the Phase 1 menu."""

import unittest

from toolkit.cli import run_cli


class CliTests(unittest.TestCase):
    def run_choices(self, *choices):
        """Run a sequence of menu choices and collect visible messages."""
        answers = iter(choices)
        messages = []
        result = run_cli(input_func=lambda _prompt: next(answers), output_func=messages.append)
        return result, "\n".join(messages)

    def test_exit(self):
        result, messages = self.run_choices("6")
        self.assertEqual(result, 0)
        self.assertIn("已退出", messages)

    def test_grade_menu_returns_to_main_menu(self):
        result, messages = self.run_choices("4", "4", "6")
        self.assertEqual(result, 0)
        self.assertIn("成绩计算器", messages)
        self.assertEqual(messages.count("=== PKU Semester Toolkit ==="), 2)

    def test_deadline_menu_can_return(self):
        result, messages = self.run_choices("3", "7", "6")
        self.assertEqual(result, 0)
        self.assertIn("添加作业", messages)

    def test_pdf_menu_can_return_without_changing_files(self):
        result, messages = self.run_choices("1", "5", "6")
        self.assertEqual(result, 0)
        self.assertIn("合并多个 PDF", messages)
        self.assertEqual(messages.count("=== PKU Semester Toolkit ==="), 2)

    def test_help_and_invalid_choice(self):
        result, messages = self.run_choices("x", "5", "6")
        self.assertEqual(result, 0)
        self.assertIn("无效选项", messages)
        self.assertIn("README.md", messages)

    def test_eof_exits_cleanly(self):
        messages = []

        def end_input(_prompt):
            raise EOFError

        result = run_cli(input_func=end_input, output_func=messages.append)
        self.assertEqual(result, 0)
        self.assertIn("已退出", "\n".join(messages))


if __name__ == "__main__":
    unittest.main()
