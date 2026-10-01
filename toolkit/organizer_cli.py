"""Preview and confirm course-file copies from the main CLI."""

from pathlib import Path

from toolkit.organizer import OrganizerError, UNSORTED, copy_planned_files, load_rules, plan_files


RULES_FILE = Path(__file__).resolve().parent.parent / "course_rules.json"
REASON_TEXT = {"matched": "已匹配", "unmatched": "未匹配", "ambiguous": "匹配多个课程"}


def run_organizer(input_func=input, output_func=print) -> None:
    """Show a copy preview and proceed only after an explicit yes."""
    try:
        source_text = input_func("待整理文件夹路径：").strip().strip('"')
        if not source_text:
            output_func("未输入文件夹，已返回主菜单。")
            return
        source = Path(source_text)
        output_text = input_func("目标文件夹（留空 = 待整理文件夹中的 Sorted）：").strip().strip('"')
        target = Path(output_text) if output_text else source / "Sorted"
        rules = load_rules(RULES_FILE)
        plan = plan_files(source, rules)
        output_func(f"规则文件：{RULES_FILE}")
        output_func(f"目标文件夹：{target}")
        output_func(f"识别到 {len(plan.files)} 个可复制文件；跳过 {len(plan.skipped)} 项。")
        for item in plan.files:
            output_func(f"  {item.source.name} -> {item.folder}（{REASON_TEXT[item.reason]}）")
        if not plan.files:
            output_func("没有可整理的文件。")
            return
        answer = input_func("确认复制以上文件？输入 y 继续，其余输入取消：").strip().casefold()
        if answer != "y":
            output_func("已取消；原文件未变。")
            return

        result = copy_planned_files(plan, target)
        unsorted = sum(path.parent.name == UNSORTED for _, path in result.copied)
        output_func(f"完成：复制 {len(result.copied)} 个，其中 {unsorted} 个进入 Unsorted；失败 {len(result.failed)} 个。")
        for _, destination in result.copied:
            output_func(f"  已复制：{destination}")
        for source_file, reason in result.failed:
            output_func(f"  失败：{source_file}（{reason}）")
    except (EOFError, KeyboardInterrupt):
        output_func("\n已取消整理。")
    except OrganizerError as exc:
        output_func(f"整理未完成：{exc}")
