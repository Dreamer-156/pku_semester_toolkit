"""Compile one LaTeX file without overwriting any earlier PDF."""

from pathlib import Path
import shutil
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCAL_TECTONIC = PROJECT_ROOT / "output" / "tectonic-0.17.0" / "tectonic.exe"


def next_output_dir(stem: str) -> Path:
    """Create a new numbered output folder so previous builds stay intact."""
    parent = PROJECT_ROOT / "output" / "latex"
    parent.mkdir(parents=True, exist_ok=True)
    number = 1
    while True:
        name = stem if number == 1 else f"{stem} ({number})"
        destination = parent / name
        try:
            destination.mkdir()
            return destination
        except FileExistsError:
            number += 1


def main() -> int:
    """Compile the given .tex file with local Tectonic or one on PATH."""
    if len(sys.argv) != 2:
        print("用法：python scripts/build_latex.py 模板或作业文件.tex")
        return 2

    source = Path(sys.argv[1]).expanduser().resolve()
    if not source.is_file() or source.suffix.lower() != ".tex":
        print(f"找不到 .tex 文件：{source}")
        return 2

    engine = str(LOCAL_TECTONIC) if LOCAL_TECTONIC.is_file() else shutil.which("tectonic")
    if engine is None:
        print("没有找到 Tectonic。请按 README 的 LaTeX 安装步骤下载，再重试。")
        return 2

    try:
        destination = next_output_dir(source.stem)
        result = subprocess.run(
            [engine, "--outdir", str(destination), str(source)],
            cwd=PROJECT_ROOT,
            check=False,
        )
    except OSError as exc:
        print(f"无法创建输出目录或运行 Tectonic：{exc}")
        return 1
    pdf = destination / f"{source.stem}.pdf"
    if result.returncode != 0 or not pdf.is_file() or pdf.stat().st_size == 0:
        print(f"编译失败；请检查上面的错误信息。输出目录：{destination}")
        return 1

    print(f"已生成：{pdf}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
