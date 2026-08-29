"""Приёмка модуля timelog.

Источник истины — examples/03-время-из-логов/expected.md.
Критерий заказчика 4NNT — docs/interview-4NNT.md (в main):
цифра времени не выдаётся без указанного порога склейки N.
"""

import json
import subprocess
import sys
from pathlib import Path

from timelog.blocks import build_blocks, total_minutes

REPO = Path(__file__).resolve().parents[1]
SAMPLE = REPO / "examples" / "03-время-из-логов" / "input" / "sessions.jsonl"


def events():
    with SAMPLE.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def pairs(blocks):
    return [tuple(b.label.split("–")) for b in blocks]


def test_n10_block_boundaries():
    assert pairs(build_blocks(events(), 10)) == [
        ("09:00", "09:05"),
        ("09:41", "09:44"),
        ("11:10", "11:59"),
        ("14:00", "14:03"),
    ]


def test_n10_total_is_60_minutes_not_the_56_written_in_expected_md():
    """expected.md называет ~56 мин, но перечисленные там же четыре блока
    дают ~60. Разница ровно 3.3 — это последний блок 14:00–14:03, который
    в их сумме потерян, а в списке блоков присутствует. Границы блоков
    воспроизводим точно; сумму считаем по этим же границам. См. issue."""
    assert round(total_minutes(build_blocks(events(), 10))) == 60


def test_n40_merges_the_first_two_blocks():
    assert pairs(build_blocks(events(), 40)) == [
        ("09:00", "09:44"),
        ("11:10", "11:59"),
        ("14:00", "14:03"),
    ]


def test_n40_total_is_96_minutes():
    assert round(total_minutes(build_blocks(events(), 40))) == 96


def test_block_closes_on_last_event_not_on_now():
    """Висящая сессия не тянет время до конца суток."""
    assert pairs(build_blocks(events(), 10))[-1][1] == "14:03"


def test_gap_exactly_n_joins():
    """expected.md говорит «пауза ≤ N» — граница включительно."""
    evs = [{"ts": "2026-08-27T09:00:00"}, {"ts": "2026-08-27T09:10:00"}]
    assert len(build_blocks(evs, 10)) == 1


def test_gap_one_second_over_n_splits():
    evs = [{"ts": "2026-08-27T09:00:00"}, {"ts": "2026-08-27T09:10:01"}]
    assert len(build_blocks(evs, 10)) == 2


def test_single_event_block_is_zero_and_flagged():
    blocks = build_blocks([{"ts": "2026-08-27T09:00:00"}], 10)
    assert len(blocks) == 1
    assert blocks[0].minutes == 0.0
    assert blocks[0].single_event is True


def test_events_out_of_order_are_sorted():
    evs = [{"ts": "2026-08-27T09:05:00"}, {"ts": "2026-08-27T09:00:00"}]
    assert pairs(build_blocks(evs, 10)) == [("09:00", "09:05")]


def test_empty_input_gives_no_blocks():
    assert build_blocks([], 10) == []


def test_cli_prints_both_thresholds_named():
    out = subprocess.run(
        [sys.executable, "-m", "timelog", str(SAMPLE)],
        capture_output=True, text=True, cwd=REPO, check=True,
    ).stdout
    assert "N = 10" in out and "N = 40" in out
    assert "60" in out and "96" in out
    assert "разброс" in out


def test_cli_refuses_a_bare_number_without_a_threshold():
    """Жёсткое требование заказчика."""
    res = subprocess.run(
        [sys.executable, "-m", "timelog", str(SAMPLE), "--total-only"],
        capture_output=True, text=True, cwd=REPO,
    )
    assert res.returncode != 0
    assert "порог" in (res.stdout + res.stderr).lower()
