{#
    australian_financial_year(date_column)
    --------------------------------------
    Convert a calendar date into an Australian financial-year label.

    The Australian FY runs 1 July -> 30 June and is labelled by the two calendar
    years it spans, e.g. 2023-07-01 .. 2024-06-30  ->  "2023-24".

    Logic: if the month is >= July, the FY starts in the current calendar year;
    otherwise it started in the previous calendar year.

    Args:
        date_column: a column or expression that evaluates to a DATE.
    Returns:
        VARCHAR financial-year label in the form "YYYY-YY".

    Cross-adapter: uses only standard EXTRACT(), so it runs on DuckDB and
    Snowflake unchanged. Covered by unit tests in marts/core/_core__models.yml.
#}
{% macro australian_financial_year(date_column) -%}
    case
        when extract(month from {{ date_column }}) >= 7
            then cast(extract(year from {{ date_column }}) as varchar)
                 || '-' ||
                 right(cast(extract(year from {{ date_column }}) + 1 as varchar), 2)
        else cast(extract(year from {{ date_column }}) - 1 as varchar)
             || '-' ||
             right(cast(extract(year from {{ date_column }}) as varchar), 2)
    end
{%- endmacro %}


{#
    australian_financial_year_start(fy_label)
    -----------------------------------------
    Inverse helper: given an FY label like "2023-24", return the FY start date
    (1 July of the first year) as a DATE. Used to relate annual facts to dim_date.
#}
{% macro australian_financial_year_start(fy_label) -%}
    cast(left({{ fy_label }}, 4) || '-07-01' as date)
{%- endmacro %}
