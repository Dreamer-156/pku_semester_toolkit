"""Local JSON storage and date filters for homework deadlines."""

from dataclasses import dataclass, replace
from datetime import date, timedelta
import json
import os
from pathlib import Path
import tempfile


class DeadlineError(ValueError):
    """An expected data, date, or storage problem shown in the CLI."""


def parse_due_date(value: str) -> date:
    """Accept only a real date written exactly as YYYY-MM-DD."""
    if not isinstance(value, str):
        raise DeadlineError("截止日期请使用 YYYY-MM-DD 格式。")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise DeadlineError("截止日期无效，请使用 YYYY-MM-DD 格式。") from exc
    if parsed.isoformat() != value:
        raise DeadlineError("截止日期请使用 YYYY-MM-DD 格式。")
    return parsed


@dataclass(frozen=True)
class Assignment:
    """One homework item; its numeric ID stays stable after status changes."""

    id: int
    course: str
    title: str
    due_date: date
    completed: bool
    notes: str

    def to_dict(self) -> dict:
        """Convert this item to plain JSON-compatible values."""
        return {
            "id": self.id,
            "course": self.course,
            "title": self.title,
            "due_date": self.due_date.isoformat(),
            "completed": self.completed,
            "notes": self.notes,
        }


def _read_assignment(raw: object) -> Assignment:
    """Validate one saved item before the program uses or rewrites it."""
    if not isinstance(raw, dict):
        raise DeadlineError("作业数据格式损坏：条目必须是对象。")
    identifier = raw.get("id")
    course = raw.get("course")
    title = raw.get("title")
    completed = raw.get("completed")
    notes = raw.get("notes")
    if type(identifier) is not int or identifier < 1:
        raise DeadlineError("作业数据格式损坏：编号无效。")
    if not isinstance(course, str) or not course.strip():
        raise DeadlineError("作业数据格式损坏：课程名称无效。")
    if not isinstance(title, str) or not title.strip():
        raise DeadlineError("作业数据格式损坏：作业名称无效。")
    if type(completed) is not bool or not isinstance(notes, str):
        raise DeadlineError("作业数据格式损坏：完成状态或备注无效。")
    return Assignment(identifier, course, title, parse_due_date(raw.get("due_date")), completed, notes)


def _atomic_write(path: Path, content: bytes) -> None:
    """Replace one app-owned JSON file only after its new bytes are complete."""
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    finally:
        Path(temp_name).unlink(missing_ok=True)  # Only the temporary file we made.


class DeadlineStore:
    """Read and update one local JSON file, keeping its previous version."""

    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser()

    def load(self) -> list[Assignment]:
        """Return saved work, or an empty list before the first save."""
        if not self.path.exists():
            return []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise DeadlineError(f"无法读取作业数据：{self.path}（{exc}）") from exc
        if (
            not isinstance(raw, dict)
            or type(raw.get("version")) is not int
            or raw["version"] != 1
            or not isinstance(raw.get("assignments"), list)
        ):
            raise DeadlineError("作业数据格式损坏或版本不受支持；原文件未修改。")
        assignments = [_read_assignment(item) for item in raw["assignments"]]
        identifiers = [item.id for item in assignments]
        if len(identifiers) != len(set(identifiers)):
            raise DeadlineError("作业数据格式损坏：存在重复编号；原文件未修改。")
        return assignments

    def _save(self, assignments: list[Assignment]) -> None:
        """Write JSON atomically and save the previous file as .bak first."""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            payload = json.dumps(
                {"version": 1, "assignments": [item.to_dict() for item in assignments]},
                ensure_ascii=False, indent=2,
            ).encode("utf-8") + b"\n"
            if self.path.exists():
                previous = self.path.read_bytes()
                _atomic_write(self.path.with_suffix(self.path.suffix + ".bak"), previous)
            _atomic_write(self.path, payload)
        except OSError as exc:
            raise DeadlineError(f"无法保存作业数据：{self.path}（{exc}）") from exc

    def add(
        self, course: str, title: str, due_date: str,
        completed: bool = False, notes: str = "",
    ) -> Assignment:
        """Validate and save a new assignment with the next stable ID."""
        if not isinstance(course, str) or not course.strip():
            raise DeadlineError("课程名称不能为空。")
        if not isinstance(title, str) or not title.strip():
            raise DeadlineError("作业名称不能为空。")
        if type(completed) is not bool or not isinstance(notes, str):
            raise DeadlineError("完成状态或备注无效。")
        deadline = parse_due_date(due_date)
        assignments = self.load()
        next_id = max((item.id for item in assignments), default=0) + 1
        item = Assignment(next_id, course.strip(), title.strip(), deadline, completed, notes.strip())
        self._save([*assignments, item])
        return item

    def set_completed(self, identifier: int, completed: bool) -> Assignment:
        """Change only one item's completed status, retaining its other fields."""
        if type(identifier) is not int or identifier < 1 or type(completed) is not bool:
            raise DeadlineError("作业编号或完成状态无效。")
        assignments = self.load()
        for index, item in enumerate(assignments):
            if item.id == identifier:
                updated = replace(item, completed=completed)
                assignments[index] = updated
                self._save(assignments)
                return updated
        raise DeadlineError(f"找不到编号为 {identifier} 的作业。")


def all_assignments(assignments: list[Assignment]) -> list[Assignment]:
    """Sort all work by due date, then by stable ID."""
    return sorted(assignments, key=lambda item: (item.due_date, item.id))


def unfinished(assignments: list[Assignment]) -> list[Assignment]:
    """Show every incomplete assignment, including overdue work."""
    return all_assignments([item for item in assignments if not item.completed])


def due_next_7_days(assignments: list[Assignment], today: date | None = None) -> list[Assignment]:
    """Show incomplete work due today through the next six calendar days."""
    start = today or date.today()
    end = start + timedelta(days=6)
    return all_assignments([
        item for item in assignments
        if not item.completed and start <= item.due_date <= end
    ])


def overdue(assignments: list[Assignment], today: date | None = None) -> list[Assignment]:
    """Show incomplete work with a due date before the local calendar day."""
    current = today or date.today()
    return all_assignments([
        item for item in assignments
        if not item.completed and item.due_date < current
    ])
