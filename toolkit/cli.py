"""Text menu for the first version of the toolkit."""

from toolkit.pdf_cli import run_pdf_menu
from toolkit.organizer_cli import run_organizer
from toolkit.deadlines_cli import run_deadline_menu
from toolkit.grades_cli import run_grade_menu

MENU = """\n=== PKU Semester Toolkit ===
1. PDF 工具
2. 整理课程文件
3. 作业 / Deadline
4. 成绩计算器
5. 查看使用帮助
6. 退出"""

HELP = (
    "PDF 工具、课程整理、Deadline 管理和成绩计算器已经可用。\n"
    "可双击 start-toolkit.cmd 启动，也可在项目目录运行 python main.py。\n"
    "PDF 子菜单按提示逐行输入文件路径。\n"
    "课程整理会先预览，再在你输入 y 后复制；规则见 course_rules.json。\n"
    "Deadline 数据保存在本机 data/deadlines.json。\n"
    "成绩计算器的数据仅在本次菜单会话中保留。\n"
    "LaTeX 作业模板在 templates/，示例在 examples/；用法见 README.md。\n"
    "文件名含空格或中文可直接粘贴；输入 6 退出主菜单。\n"
    "安装与开发说明请查看 README.md。"
)


def run_cli(input_func=input, output_func=print) -> int:
    """Show the menu until the user exits; return a process exit code.

    The input and output functions are parameters so the menu can be tested
    without opening an interactive terminal.
    """
    while True:
        output_func(MENU)
        try:
            choice = input_func("请选择（1-6）：").strip()
        except (EOFError, KeyboardInterrupt):
            output_func("\n已退出。")
            return 0

        if choice == "6":
            output_func("已退出。")
            return 0
        if choice == "1":
            run_pdf_menu(input_func=input_func, output_func=output_func)
        elif choice == "2":
            run_organizer(input_func=input_func, output_func=output_func)
        elif choice == "3":
            run_deadline_menu(input_func=input_func, output_func=output_func)
        elif choice == "4":
            run_grade_menu(input_func=input_func, output_func=output_func)
        elif choice == "5":
            output_func(HELP)
        else:
            output_func("无效选项：请输入 1 到 6。")
