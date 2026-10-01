"""Small text menu for local homework and deadline records."""

from datetime import date
from pathlib import Path

from toolkit.deadlines import (
    DeadlineError, DeadlineStore, all_assignments, due_next_7_days, overdue, unfinished,
)


DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "deadlines.json"
DEADLINE_MENU = """\n--- 作业 / Deadline ---
1. 添加作业
2. 查看全部作业
3. 查看未完成作业
4. 查看未来 7 天截止的作业
5. 查看已逾期作业
6. 修改完成状态
7. 返回主菜单"""


def _show_items(items, output_func) -> None:
    """Print assignment fields in a compact, readable form."""
    if not items:
        output_func("没有符合条件的作业。")
        return
    for item in items:
        marker = "已完成" if item.completed else "未完成"
        output_func(f"#{item.id} [{marker}] {item.due_date} | {item.course} | {item.title}")
        if item.notes:
            output_func(f"    备注：{item.notes}")


def run_deadline_menu(
    input_func=input, output_func=print,
    store: DeadlineStore | None = None, today: date | None = None,
) -> None:
    """Run Deadline actions, using a supplied store for isolated tests."""
    active_store = store or DeadlineStore(DATA_FILE)
    while True:
        output_func(DEADLINE_MENU)
        try:
            choice = input_func("请选择（1-7）：").strip()
            if choice == "7":
                return
            if choice == "1":
                course = input_func("课程名称：")
                title = input_func("作业名称：")
                deadline = input_func("截止日期（YYYY-MM-DD）：").strip()
                notes = input_func("备注（可留空）：")
                done = input_func("已经完成？输入 y 表示是，留空或 n 表示否：").strip().casefold()
                if done not in {"", "y", "n"}:
                    raise DeadlineError("完成状态请输入 y、n 或留空。")
                item = active_store.add(course, title, deadline, done == "y", notes)
                output_func(f"已保存作业 #{item.id}。")
            elif choice in {"2", "3", "4", "5"}:
                records = active_store.load()
                if choice == "2":
                    selected = all_assignments(records)
                elif choice == "3":
                    selected = unfinished(records)
                elif choice == "4":
                    selected = due_next_7_days(records, today)
                else:
                    selected = overdue(records, today)
                _show_items(selected, output_func)
            elif choice == "6":
                text = input_func("作业编号：").strip()
                if not text.isdecimal() or int(text) < 1:
                    raise DeadlineError("作业编号请输入正整数。")
                done = input_func("输入 y 标记完成，输入 n 标记未完成：").strip().casefold()
                if done not in {"y", "n"}:
                    raise DeadlineError("完成状态请输入 y 或 n。")
                item = active_store.set_completed(int(text), done == "y")
                output_func(f"已更新作业 #{item.id}：{'已完成' if item.completed else '未完成'}。")
            else:
                output_func("无效选项：请输入 1 到 7。")
        except (EOFError, KeyboardInterrupt):
            output_func("\n已返回主菜单。")
            return
        except DeadlineError as exc:
            output_func(f"操作未完成：{exc}")
