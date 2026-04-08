"""
Extraction quality evaluation — regression test suite.

Two complementary test layers:

1. test_case_[id]  (parametrized)
   One test per dataset entry; fails immediately on the first field mismatch.
   Use this for rapid debugging after a patch:
       pytest tests/test_extraction_quality.py -v -k "anr"

2. test_extraction_quality_report  (aggregate)
   Runs every case, computes per-field accuracy, prints a summary table,
   and fails if any field drops below FIELD_THRESHOLDS.
   Use this for a global health check after a major refactor:
       pytest tests/test_extraction_quality.py -v -s -k "report"
"""

import textwrap
from datetime import date

import pytest

from tests.fixtures.extraction_dataset import DATASET

# Minimum accuracy required per field (0.0 → 1.0).
# Set to 1.0 (100 %) because the dataset is synthetic and fully controlled;
# any regression should fail CI.
FIELD_THRESHOLDS: dict[str, float] = {
    "date_limite": 1.0,
    "montant_min": 1.0,
    "montant_max": 1.0,
    "statut": 1.0,
    "domaine": 1.0,
    "source": 1.0,
    "mots_cles_include": 1.0,
}

# ─── helpers ──────────────────────────────────────────────────────────────────


def _run_case(case: dict):
    """Instantiate the scraper and normalize the raw dict. Returns AppelOffre."""
    scraper = case["scraper_cls"]()
    return scraper.normalize(case["raw"])


def _check_fields(result, expected: dict) -> dict[str, tuple[bool, str]]:
    """
    For each key in `expected`, compare with the corresponding field in `result`.
    Returns a dict: field → (passed: bool, detail: str).
    """
    checks = {}

    for field, exp_val in expected.items():
        if field == "mots_cles_include":
            # Subset check: all listed keywords must appear in result.mots_cles
            missing = [kw for kw in exp_val if kw not in result.mots_cles]
            passed = len(missing) == 0
            detail = (
                f"missing keywords: {missing!r}  (got {result.mots_cles!r})"
                if not passed
                else ""
            )
        else:
            actual = getattr(result, field, "FIELD_MISSING")
            passed = actual == exp_val
            detail = (
                f"expected {exp_val!r}, got {actual!r}" if not passed else ""
            )
        checks[field] = (passed, detail)

    return checks


# ─── parametrized per-case tests ──────────────────────────────────────────────


@pytest.mark.parametrize("case", DATASET, ids=[c["id"] for c in DATASET])
def test_case(case):
    """Each dataset entry must produce the declared expected fields."""
    result = _run_case(case)
    checks = _check_fields(result, case["expected"])

    failures = [
        f"  [{field}] {detail}"
        for field, (passed, detail) in checks.items()
        if not passed
    ]
    if failures:
        lines = "\n".join(failures)
        pytest.fail(
            f"[{case['id']}] {case['description']}\n{lines}"
        )


# ─── aggregate report ─────────────────────────────────────────────────────────


def test_extraction_quality_report():
    """
    Run all cases, compute per-field accuracy and print a summary table.
    Fails if any field accuracy drops below its threshold in FIELD_THRESHOLDS.
    """
    # Accumulators: field → (total_checked, total_passed, list_of_failures)
    stats: dict[str, list] = {}  # field → [total, passed, failures]

    case_failures: list[str] = []

    for case in DATASET:
        result = _run_case(case)
        checks = _check_fields(result, case["expected"])

        for field, (passed, detail) in checks.items():
            if field not in stats:
                stats[field] = [0, 0, []]
            stats[field][0] += 1
            if passed:
                stats[field][1] += 1
            else:
                stats[field][2].append(f"[{case['id']}] {field}: {detail}")
                case_failures.append(f"[{case['id']}] {field}: {detail}")

    # ── Print table ────────────────────────────────────────────────────────────
    header = f"\n{'═' * 62}"
    header += "\n  EXTRACTION QUALITY REPORT"
    header += f"\n  Dataset: {len(DATASET)} cases — {sum(s[0] for s in stats.values())} field checks"
    header += f"\n{'═' * 62}"

    col_field = "Field"
    col_checked = "Checked"
    col_passed = "Passed"
    col_pct = "Accuracy"
    col_threshold = "Threshold"
    row_fmt = "  {:<22} {:>7}  {:>6}  {:>8}  {:>9}"
    separator = "  " + "-" * 58

    table_lines = [
        header,
        row_fmt.format(col_field, col_checked, col_passed, col_pct, col_threshold),
        separator,
    ]

    all_failed_fields: list[str] = []

    for field in [
        "source",
        "date_limite",
        "montant_min",
        "montant_max",
        "statut",
        "domaine",
        "mots_cles_include",
    ]:
        if field not in stats:
            continue
        total, passed, _ = stats[field]
        accuracy = passed / total if total > 0 else 0.0
        threshold = FIELD_THRESHOLDS.get(field, 1.0)
        ok = "✓" if accuracy >= threshold else "✗"
        pct_str = f"{accuracy * 100:.1f} %"
        thr_str = f"{threshold * 100:.0f} % {ok}"
        table_lines.append(
            row_fmt.format(field, total, passed, pct_str, thr_str)
        )
        if accuracy < threshold:
            all_failed_fields.append(field)

    # Overall
    total_all = sum(s[0] for s in stats.values())
    passed_all = sum(s[1] for s in stats.values())
    overall_pct = passed_all / total_all * 100 if total_all > 0 else 0.0
    table_lines.append(separator)
    table_lines.append(
        row_fmt.format("OVERALL", total_all, passed_all, f"{overall_pct:.1f} %", "")
    )
    table_lines.append("═" * 62)

    if case_failures:
        table_lines.append("\n  Failures:")
        for f in case_failures:
            table_lines.append(textwrap.indent(f"• {f}", "    "))
    else:
        table_lines.append("\n  All checks passed ✓")

    table_lines.append("")
    print("\n".join(table_lines))

    # ── Assert thresholds ──────────────────────────────────────────────────────
    if all_failed_fields:
        failing_details = []
        for field in all_failed_fields:
            total, passed, failures = stats[field]
            accuracy = passed / total * 100
            threshold = FIELD_THRESHOLDS[field] * 100
            failing_details.append(
                f"  {field}: {accuracy:.1f}% < {threshold:.0f}% threshold"
            )
            for msg in failures:
                failing_details.append(f"    → {msg}")

        pytest.fail(
            "Extraction quality below threshold for:\n"
            + "\n".join(failing_details)
        )
