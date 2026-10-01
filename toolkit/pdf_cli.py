"""Beginner-friendly prompts for the PDF functions."""

from pathlib import Path

from toolkit.pdf_tools import (
    PdfToolError,
    combine_scans,
    extract_pdf_pages,
    images_to_pdf,
    merge_pdfs,
    split_pdf_pages,
)


PDF_MENU = """\n--- PDF 工具 ---
1. 合并多个 PDF
2. 拆分 PDF
3. 图片转 PDF
4. 按指定顺序合并扫描作业（PDF / 图片）
5. 返回主菜单"""


def _ask_files(input_func, output_func) -> list[Path]:
    """Collect paths one line at a time so spaces and Chinese work naturally."""
    output_func("按目标顺序逐行输入文件路径；直接按 Enter 结束。")
    paths = []
    while True:
        value = input_func(f"文件 {len(paths) + 1}：").strip().strip('"')
        if not value:
            return paths
        paths.append(Path(value))


def _ask_output_dir(input_func) -> Path | None:
    """Read an optional existing output folder without creating directories."""
    value = input_func("输出文件夹（留空 = 第一个文件所在文件夹）：").strip().strip('"')
    return Path(value) if value else None


def run_pdf_menu(input_func=input, output_func=print) -> None:
    """Run PDF actions and return to the main menu when requested."""
    while True:
        output_func(PDF_MENU)
        try:
            choice = input_func("请选择（1-5）：").strip()
            if choice == "5":
                return
            if choice not in {"1", "2", "3", "4"}:
                output_func("无效选项：请输入 1 到 5。")
                continue

            if choice == "2":
                source = Path(input_func("PDF 文件路径：").strip().strip('"'))
                mode = input_func("输入 1 逐页拆分，输入 2 提取连续页码：").strip()
                if mode == "1":
                    folder = _ask_output_dir(input_func)
                    outputs = split_pdf_pages(source, folder)
                    output_func(f"已生成 {len(outputs)} 个文件：")
                    for path in outputs:
                        output_func(str(path))
                elif mode == "2":
                    first = int(input_func("起始页码（从 1 开始）：").strip())
                    last = int(input_func("结束页码（包含该页）：").strip())
                    folder = _ask_output_dir(input_func)
                    output_func(f"已生成：{extract_pdf_pages(source, first, last, folder)}")
                else:
                    output_func("无效拆分方式：请输入 1 或 2。")
                continue

            paths = _ask_files(input_func, output_func)
            folder = _ask_output_dir(input_func)
            if choice == "1":
                output = merge_pdfs(paths, folder)
            elif choice == "3":
                output = images_to_pdf(paths, folder)
            else:
                output = combine_scans(paths, folder)
            output_func(f"已生成：{output}")
        except (EOFError, KeyboardInterrupt):
            output_func("\n已返回主菜单。")
            return
        except (PdfToolError, ValueError) as exc:
            output_func(f"操作未完成：{exc}")
