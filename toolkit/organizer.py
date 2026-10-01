"""Plan and copy course files without changing their originals."""

from dataclasses import dataclass
import json
from pathlib import Path
import re
import shutil


SUPPORTED_SUFFIXES = {
    ".pdf", ".ppt", ".pptx", ".doc", ".docx", ".xls", ".xlsx",
    ".csv", ".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp",
    ".tif", ".tiff", ".heic",
}
UNSORTED = "Unsorted"
INVALID_WINDOWS_CHARS = set('<>:"/\\|?*')
RESERVED_WINDOWS_NAME = re.compile(r"^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?$", re.I)


class OrganizerError(ValueError):
    """An expected configuration, folder, or copy problem."""


@dataclass(frozen=True)
class PlannedCopy:
    """One file and the folder chosen from its filename."""

    source: Path
    folder: str
    reason: str


@dataclass(frozen=True)
class ScanPlan:
    """Supported files to copy and top-level entries intentionally skipped."""

    files: tuple[PlannedCopy, ...]
    skipped: tuple[Path, ...]


@dataclass
class CopyResult:
    """Paths copied successfully and failures that need the user's attention."""

    copied: list[tuple[Path, Path]]
    failed: list[tuple[Path, str]]


def _valid_course_folder(name: str) -> bool:
    """Reject names Windows cannot safely use as a directory."""
    return (
        bool(name)
        and name == name.strip()
        and name not in {".", ".."}
        and name.casefold() != UNSORTED.casefold()
        and not name.endswith(".")
        and not any(char in INVALID_WINDOWS_CHARS or ord(char) < 32 for char in name)
        and RESERVED_WINDOWS_NAME.fullmatch(name) is None
    )


def load_rules(file: str | Path) -> dict[str, tuple[str, ...]]:
    """Read a simple JSON mapping from course names to filename keywords."""
    path = Path(file).expanduser()
    try:
        raw = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise OrganizerError(f"无法读取课程规则文件：{path}（{exc}）") from exc
    if not isinstance(raw, dict) or not raw:
        raise OrganizerError("课程规则必须是非空 JSON 对象。")

    rules = {}
    folder_names = set()
    for course, keywords in raw.items():
        if not isinstance(course, str) or not _valid_course_folder(course):
            raise OrganizerError(f"课程文件夹名称无效：{course!r}")
        if course.casefold() in folder_names:
            raise OrganizerError(f"课程文件夹名称重复：{course}")
        folder_names.add(course.casefold())
        if not isinstance(keywords, list) or not keywords:
            raise OrganizerError(f"课程 {course} 需要至少一个关键词列表。")
        cleaned = []
        for keyword in keywords:
            if not isinstance(keyword, str) or not keyword.strip():
                raise OrganizerError(f"课程 {course} 存在空关键词或非文字关键词。")
            cleaned.append(keyword.strip().casefold())
        rules[course] = tuple(cleaned)
    return rules


def plan_files(folder: str | Path, rules: dict[str, tuple[str, ...]]) -> ScanPlan:
    """Scan only top-level files and choose a course or Unsorted for each."""
    source_folder = Path(folder).expanduser()
    if not source_folder.is_dir():
        raise OrganizerError(f"待整理文件夹不存在：{source_folder}")
    try:
        entries = sorted(source_folder.iterdir(), key=lambda path: path.name.casefold())
    except OSError as exc:
        raise OrganizerError(f"无法扫描文件夹：{source_folder}（{exc}）") from exc

    planned = []
    skipped = []
    for path in entries:
        if path.is_symlink() or not path.is_file() or path.suffix.casefold() not in SUPPORTED_SUFFIXES:
            skipped.append(path)
            continue
        filename = path.stem.casefold()
        matches = [
            course for course, keywords in rules.items()
            if any(keyword in filename for keyword in keywords)
        ]
        if len(matches) == 1:
            planned.append(PlannedCopy(path, matches[0], "matched"))
        elif len(matches) > 1:
            planned.append(PlannedCopy(path, UNSORTED, "ambiguous"))
        else:
            planned.append(PlannedCopy(path, UNSORTED, "unmatched"))
    return ScanPlan(tuple(planned), tuple(skipped))


def _copy_without_overwrite(source: Path, target_folder: Path) -> Path:
    """Copy bytes to a new name, using an exclusive create to prevent overwrite."""
    number = 1
    while True:
        suffix = "" if number == 1 else f" ({number})"
        destination = target_folder / f"{source.stem}{suffix}{source.suffix}"
        created = False
        try:
            with source.open("rb") as original:
                with destination.open("xb") as output:
                    created = True
                    shutil.copyfileobj(original, output)
            return destination
        except FileExistsError:
            number += 1
        except OSError:
            if created:
                destination.unlink(missing_ok=True)  # Only our incomplete copy.
            raise


def copy_planned_files(plan: ScanPlan, output_folder: str | Path) -> CopyResult:
    """Copy a previewed plan; continue and report individual file failures."""
    destination_root = Path(output_folder).expanduser()
    try:
        destination_root.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise OrganizerError(f"无法创建目标文件夹：{destination_root}（{exc}）") from exc
    if not destination_root.is_dir():
        raise OrganizerError(f"目标路径不是文件夹：{destination_root}")

    copied = []
    failed = []
    for item in plan.files:
        if item.source.is_symlink() or not item.source.is_file():
            failed.append((item.source, "原文件已移动、删除或变成链接"))
            continue
        target_folder = destination_root / item.folder
        try:
            target_folder.mkdir(exist_ok=True)
            destination = _copy_without_overwrite(item.source, target_folder)
            copied.append((item.source, destination))
        except OSError as exc:
            failed.append((item.source, str(exc)))
    return CopyResult(copied, failed)
