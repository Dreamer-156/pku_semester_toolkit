"""Deadline tests keep all data in a temporary directory."""

from datetime import date
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from toolkit.deadlines import (
    DeadlineError, DeadlineStore, all_assignments, due_next_7_days,
    overdue, parse_due_date, unfinished,
)
from toolkit.deadlines_cli import run_deadline_menu


class DeadlineTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name) / "data" / "deadlines.json"
        self.store = DeadlineStore(self.path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_reload_status_and_previous_version_backup(self):
        self.assertEqual(self.store.load(), [])
        first = self.store.add("微观经济学", "问题集 1", "2026-10-01", notes="第 3 章")
        self.assertEqual(first.id, 1)
        self.assertFalse(first.completed)
        self.assertTrue(self.path.exists())
        self.assertFalse(self.path.with_suffix(".json.bak").exists())

        second = self.store.add("高等数学", "练习", "2026-10-03", completed=True)
        self.assertEqual(second.id, 2)
        backup = json.loads(self.path.with_suffix(".json.bak").read_text(encoding="utf-8"))
        self.assertEqual(len(backup["assignments"]), 1)
        self.assertEqual(self.store.load()[0].notes, "第 3 章")

        updated = self.store.set_completed(1, True)
        self.assertTrue(updated.completed)
        self.assertEqual(self.store.load()[0].course, "微观经济学")
        self.assertEqual(len(self.store.load()), 2)
        self.assertEqual(self.store.load()[0].due_date, date(2026, 10, 1))

    def test_unfinished_next_seven_days_and_overdue_boundaries(self):
        self.store.add("A", "昨天", "2026-09-27")
        self.store.add("A", "今天", "2026-09-28")
        self.store.add("B", "第七个日历日", "2026-10-04")
        self.store.add("B", "再下一天", "2026-10-05")
        self.store.add("C", "已完成", "2026-09-29", completed=True)
        items = self.store.load()
        today = date(2026, 9, 28)

        self.assertEqual(len(all_assignments(items)), 5)
        self.assertEqual([item.title for item in unfinished(items)], [
            "昨天", "今天", "第七个日历日", "再下一天",
        ])
        self.assertEqual([item.title for item in due_next_7_days(items, today)], [
            "今天", "第七个日历日",
        ])
        self.assertEqual([item.title for item in overdue(items, today)], ["昨天"])

    def test_bad_inputs_never_create_data(self):
        for args in [
            ("", "作业", "2026-10-01"),
            ("课程", "", "2026-10-01"),
            ("课程", "作业", "2026-02-30"),
            ("课程", "作业", "2026-9-1"),
        ]:
            with self.assertRaises(DeadlineError):
                self.store.add(*args)
        self.assertFalse(self.path.exists())
        with self.assertRaises(DeadlineError):
            parse_due_date("not a date")
        with self.assertRaises(DeadlineError):
            self.store.set_completed(1, True)

    def test_corrupt_data_is_not_overwritten(self):
        self.path.parent.mkdir()
        self.path.write_bytes(b"{broken json")
        before = self.path.read_bytes()
        with self.assertRaisesRegex(DeadlineError, "无法读取作业数据"):
            self.store.add("课程", "作业", "2026-10-01")
        self.assertEqual(self.path.read_bytes(), before)

    def test_failed_atomic_replace_preserves_current_file(self):
        self.store.add("课程", "第一份", "2026-10-01")
        before = self.path.read_bytes()
        real_replace = os.replace

        def fail_main_replace(source, target):
            if Path(target) == self.path:
                raise OSError("simulated write failure")
            real_replace(source, target)

        with mock.patch("toolkit.deadlines.os.replace", side_effect=fail_main_replace):
            with self.assertRaisesRegex(DeadlineError, "无法保存作业数据"):
                self.store.add("课程", "第二份", "2026-10-02")
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(list(self.path.parent.glob("*.tmp")), [])

    def test_cli_add_view_and_update_using_temp_store(self):
        answers = iter([
            "1", "微观经济学", "问题集", "2026-10-01", "复习第 3 章", "",
            "3", "4", "6", "1", "y", "2", "7",
        ])
        messages = []
        run_deadline_menu(
            input_func=lambda _prompt: next(answers),
            output_func=messages.append,
            store=self.store,
            today=date(2026, 9, 28),
        )
        output = "\n".join(messages)
        self.assertIn("已保存作业 #1", output)
        self.assertIn("微观经济学 | 问题集", output)
        self.assertIn("已更新作业 #1：已完成", output)
        self.assertTrue(self.store.load()[0].completed)


if __name__ == "__main__":
    unittest.main()
