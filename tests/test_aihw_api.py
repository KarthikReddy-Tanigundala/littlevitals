"""Unit tests for AIHW ingestion in offline snapshot mode (no network)."""

import ingest_aihw_api as api


def test_parse_csv_roundtrip():
    df = api.parse_csv("a,b\n1,2\n3,4\n")
    assert list(df.columns) == ["a", "b"]
    assert len(df) == 2


def test_fetch_ed_data_snapshot_is_offline():
    df = api.fetch_ed_data(source="snapshot")
    assert len(df) > 0
    for col in ("hospital_code", "financial_year", "triage_category", "total_presentations"):
        assert col in df.columns


def test_fetch_reporting_units_snapshot():
    df = api.fetch_reporting_units(source="snapshot")
    assert "hospital_code" in df.columns
    assert len(df) > 0


def test_main_snapshot_dry_run_counts():
    result = api.main(source="snapshot", load=False)
    assert result["ed"] > 0
    assert result["reporting_units"] > 0


def test_missing_snapshot_raises(monkeypatch, tmp_path):
    # Point all search dirs at an empty folder to force the not-found path.
    monkeypatch.setattr(api.config, "SNAPSHOT_SEARCH_DIRS", [tmp_path])
    try:
        api.fetch_ed_data(source="snapshot")
        assert False, "expected FileNotFoundError"
    except FileNotFoundError:
        pass
