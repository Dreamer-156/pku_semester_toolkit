"""Small, precise calculations for course grades and final exam targets."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_CEILING
from typing import Sequence


HUNDRED = Decimal("100")
HUNDREDTH = Decimal("0.01")


class GradeError(ValueError):
    """An expected score or weight problem shown in the CLI."""


@dataclass(frozen=True)
class GradeItem:
    """One graded component with a score and a percentage of the final grade."""

    name: str
    score: Decimal
    weight: Decimal


@dataclass(frozen=True)
class CurrentGrade:
    """Current contribution and average of the items already graded."""

    completed_weight: Decimal
    contribution: Decimal
    completed_average: Decimal


def _number(value: object, label: str, allow_zero: bool = True) -> Decimal:
    """Parse a finite 0–100 number, with zero disallowed for weights."""
    try:
        number = Decimal(str(value).strip())
    except (InvalidOperation, ValueError) as exc:
        raise GradeError(f"{label}请输入 0 到 100 之间的数字。") from exc
    if not number.is_finite() or number < 0 or number > HUNDRED:
        raise GradeError(f"{label}请输入 0 到 100 之间的有限数字。")
    if not allow_zero and number == 0:
        raise GradeError(f"{label}必须大于 0。")
    return number


def make_grade_item(name: str, score: object, weight: object) -> GradeItem:
    """Validate one entered score and percentage weight."""
    if not isinstance(name, str) or not name.strip():
        raise GradeError("项目名称不能为空。")
    return GradeItem(
        name.strip(),
        _number(score, "成绩"),
        _number(weight, "权重百分比", allow_zero=False),
    )


def calculate_current(items: Sequence[GradeItem]) -> CurrentGrade:
    """Return contribution to 100 points and average over completed weight."""
    if not items:
        raise GradeError("请先录入至少一项成绩。")
    checked = [make_grade_item(item.name, item.score, item.weight) for item in items]
    names = [item.name.casefold() for item in checked]
    if len(names) != len(set(names)):
        raise GradeError("项目名称不能重复。")
    total_weight = sum((item.weight for item in checked), Decimal(0))
    if total_weight > HUNDRED:
        raise GradeError("已录入项目的权重之和不能超过 100%。")
    contribution = sum(
        (item.score * item.weight / HUNDRED for item in checked), Decimal(0)
    )
    average = contribution * HUNDRED / total_weight
    return CurrentGrade(total_weight, contribution, average)


def required_final_score(
    items: Sequence[GradeItem], final_weight: object, target_total: object,
) -> Decimal:
    """Find the exact exam score needed when known items plus exam total 100%."""
    current = calculate_current(items)
    exam_weight = _number(final_weight, "期末权重百分比", allow_zero=False)
    target = _number(target_total, "目标总评")
    if current.completed_weight + exam_weight != HUNDRED:
        raise GradeError("已录入权重与期末权重之和必须恰好为 100%；请检查是否漏了项目。")
    needed = (target - current.contribution) * HUNDRED / exam_weight
    return max(Decimal(0), needed)


def minimum_hundredth(score: Decimal) -> Decimal:
    """Round a required score upward to the nearest 0.01 point."""
    return score.quantize(HUNDREDTH, rounding=ROUND_CEILING)
