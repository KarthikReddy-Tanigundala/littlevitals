"""Unit tests for the Snowflake loader's pure transformation helpers (no network)."""

import pandas as pd

import snowflake_loader as sl


def test_normalize_column_upper_snake_case():
    assert sl.normalize_column("Hospital Name") == "HOSPITAL_NAME"
    assert sl.normalize_column("median-wait.minutes") == "MEDIAN_WAIT_MINUTES"
    assert sl.normalize_column("  state ") == "STATE"


def test_prepare_dataframe_adds_metadata_and_normalises():
    df = pd.DataFrame({"Hospital Code": ["H0001"], "wait min": [10]})
    out = sl.prepare_dataframe(df, "RAW_X", source="unit-test")

    assert "_INGESTED_AT" in out.columns
    assert "_SOURCE" in out.columns
    assert "HOSPITAL_CODE" in out.columns
    assert "WAIT_MIN" in out.columns
    assert out["_SOURCE"].iloc[0] == "unit-test"
    assert len(out) == 1


def test_prepare_dataframe_does_not_mutate_input():
    df = pd.DataFrame({"Hospital Code": ["H0001"]})
    sl.prepare_dataframe(df, "RAW_X")
    assert list(df.columns) == ["Hospital Code"]


def test_source_defaults_to_table_name():
    out = sl.prepare_dataframe(pd.DataFrame({"a": [1]}), "RAW_TABLE")
    assert out["_SOURCE"].iloc[0] == "RAW_TABLE"
