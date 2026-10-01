"""Text prompts for temporary grade calculations."""

from decimal import Decimal, ROUND_HALF_UP

from toolkit.grades import (
    GradeError, GradeItem, calculate_current, make_grade_item,
    minimum_hundredth, required_final_score,
)


GRADE_MENU = """\n--- 成绩计算器 ---
1. 录入或重新录入已知成绩
2. 查看当前加权成绩
3. 反推目标总评所需的期末分数
4. 返回主菜单"""


def _display_number(value: Decimal) -> str:
    """Show an ordinary score or percentage with two decimal places."""
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _read_items(input_func, output_func) -> list[GradeItem]:
    """Collect graded components, rejecting invalid entries as they appear."""
    output_func("逐项输入已知成绩；权重填百分数，例如 30 表示 30%。项目名称留空结束。")
    items = []
    while True:
        name = input_func("项目名称：").strip()
        if not name:
            return items
        score = input_func("成绩（0-100）：").strip()
        weight = input_func("权重百分比（大于 0）：").strip()
        try:
            candidate = make_grade_item(name, score, weight)
            calculate_current([*items, candidate])
            items.append(candidate)
            output_func(f"已录入：{candidate.name}。")
        except GradeError as exc:
            output_func(f"该项未录入：{exc}")


def run_grade_menu(input_func=input, output_func=print) -> None:
    """Calculate grades in memory; leaving the menu clears entered items."""
    items: list[GradeItem] = []
    while True:
        output_func(GRADE_MENU)
        try:
            choice = input_func("请选择（1-4）：").strip()
            if choice == "4":
                return
            if choice == "1":
                entered = _read_items(input_func, output_func)
                if entered:
                    items = entered
                    output_func(f"已保存本次输入的 {len(items)} 项成绩；退出成绩菜单后会清除。")
                else:
                    output_func("没有有效的新项目，原有输入保持不变。")
            elif choice == "2":
                current = calculate_current(items)
                remaining = Decimal("100") - current.completed_weight
                output_func(f"已录入权重：{_display_number(current.completed_weight)}%。")
                output_func(f"已计入总评：{_display_number(current.contribution)} / 100 分。")
                output_func(f"已录入项目的加权平均：{_display_number(current.completed_average)} / 100 分。")
                output_func(f"尚未录入权重：{_display_number(remaining)}%。")
            elif choice == "3":
                if not items:
                    raise GradeError("请先录入已知成绩。")
                final_weight = input_func("期末考试权重百分比：").strip()
                target = input_func("目标总评（0-100）：").strip()
                needed = required_final_score(items, final_weight, target)
                minimum = minimum_hundredth(needed)
                if needed > 100:
                    output_func(f"目标无法达到：期末需要至少 {minimum} 分，超过 100 分。")
                else:
                    output_func(f"期末至少需要 {minimum} 分（按 0.01 分向上取整）。")
            else:
                output_func("无效选项：请输入 1 到 4。")
        except (EOFError, KeyboardInterrupt):
            output_func("\n已返回主菜单；本次输入的成绩已清除。")
            return
        except GradeError as exc:
            output_func(f"无法计算：{exc}")
