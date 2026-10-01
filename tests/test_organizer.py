"""Course sorting checks use temporary files, never personal coursework."""

import json
import tempfile
import unittest
from pathlib import Path

from toolkit.cli import run_cli
from toolkit.organizer import OrganizerError, copy_planned_files, load_rules, plan_files


class OrganizerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.source = self.root / "待整理 文件"
        self.source.mkdir()
        self.target = self.root / "课程资料"
        self.rules = {"微观经济学": ("微观", "micro"), "宏观经济学": ("宏观", "macro")}

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_file(self, name, content=b"original"):
        path = self.source / name
        path.write_bytes(content)
        return path

    def test_common_formats_chinese_spaces_and_unsorted(self):
        names = [
            "微观 讲义.pdf", "微观 课件.ppt", "微观 课件.pptx",
            "微观 阅读.doc", "微观 作业.docx", "微观 成绩.xls",
            "微观 数据.xlsx", "微观 扫描.png",
        ]
        original_files = [self.write_file(name, name.encode("utf-8")) for name in names]
        unknown = self.write_file("不知道课程的 文件.jpg", b"unknown")
        ambiguous = self.write_file("微观 宏观 混合.pptx", b"ambiguous")
        ignored = self.write_file("微观 压缩包.zip", b"skip")
        subfolder = self.source / "旧文件夹"
        subfolder.mkdir()
        (subfolder / "微观 里面.pdf").write_bytes(b"nested")

        plan = plan_files(self.source, self.rules)
        self.assertEqual(len(plan.files), len(names) + 2)
        self.assertIn(ignored, plan.skipped)
        self.assertIn(subfolder, plan.skipped)
        self.assertEqual({item.source: item.reason for item in plan.files}[ambiguous], "ambiguous")
        result = copy_planned_files(plan, self.target)

        self.assertEqual(result.failed, [])
        self.assertEqual(len(result.copied), len(names) + 2)
        for source in original_files:
            self.assertEqual((self.target / "微观经济学" / source.name).read_bytes(), source.read_bytes())
            self.assertTrue(source.exists())
        self.assertEqual((self.target / "Unsorted" / unknown.name).read_bytes(), b"unknown")
        self.assertEqual((self.target / "Unsorted" / ambiguous.name).read_bytes(), b"ambiguous")
        self.assertTrue(ignored.exists())
        self.assertFalse((self.target / "微观经济学" / "微观 里面.pdf").exists())

    def test_existing_target_is_never_overwritten(self):
        source = self.write_file("微观 课件.pdf", b"new content")
        course_folder = self.target / "微观经济学"
        course_folder.mkdir(parents=True)
        existing = course_folder / source.name
        existing.write_bytes(b"keep me")
        plan = plan_files(self.source, self.rules)

        first = copy_planned_files(plan, self.target)
        second = copy_planned_files(plan, self.target)
        self.assertEqual(first.copied[0][1].name, "微观 课件 (2).pdf")
        self.assertEqual(second.copied[0][1].name, "微观 课件 (3).pdf")
        self.assertEqual(existing.read_bytes(), b"keep me")
        self.assertEqual(source.read_bytes(), b"new content")

    def test_missing_source_after_preview_is_reported(self):
        source = self.write_file("微观 讲义.pdf")
        plan = plan_files(self.source, self.rules)
        source.unlink()
        result = copy_planned_files(plan, self.target)
        self.assertEqual(result.copied, [])
        self.assertEqual(len(result.failed), 1)

    def test_rule_file_errors_are_clear(self):
        rules_file = self.root / "rules.json"
        rules_file.write_text("{invalid", encoding="utf-8")
        with self.assertRaisesRegex(OrganizerError, "无法读取课程规则"):
            load_rules(rules_file)
        for bad_rules in [
            {"CON": ["test"]},
            {"Unsorted": ["test"]},
            {"Course": [""]},
            {"Macro": ["one"], "macro": ["two"]},
        ]:
            rules_file.write_text(json.dumps(bad_rules), encoding="utf-8")
            with self.assertRaises(OrganizerError):
                load_rules(rules_file)

    def test_cli_requires_confirmation_before_copying(self):
        source = self.write_file("微观 作业.pdf", b"do not change")

        def run_answers(*answers):
            choices = iter(answers)
            messages = []
            code = run_cli(input_func=lambda _prompt: next(choices), output_func=messages.append)
            return code, "\n".join(messages)

        code, preview = run_answers("2", str(self.source), "", "n", "6")
        self.assertEqual(code, 0)
        self.assertIn("微观经济学", preview)
        self.assertFalse((self.source / "Sorted").exists())

        code, completed = run_answers("2", str(self.source), "", "y", "6")
        self.assertEqual(code, 0)
        self.assertIn("复制 1 个", completed)
        self.assertEqual((self.source / "Sorted" / "微观经济学" / source.name).read_bytes(), b"do not change")
        self.assertEqual(source.read_bytes(), b"do not change")


if __name__ == "__main__":
    unittest.main()
