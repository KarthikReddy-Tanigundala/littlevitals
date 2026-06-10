/*
    fct_ed_presentations — Gold fact (Kimball).
    Grain: one row per hospital x financial_year x triage_category (ANNUAL — AIHW
    public data is published per financial year; see CLAUDE.md 16.1).

    Surrogate PK: ed_presentation_key.
    FKs: hospital_key -> dim_hospital, triage_key -> dim_triage_category,
         date_key -> dim_date (the 1 July start of the financial year).
    triage_code is retained as a degenerate dimension for convenience.
*/

with enriched as (
    select * from {{ ref('int_ed__presentations_enriched') }}
),

final as (

    select
        {{ dbt_utils.generate_surrogate_key(['hospital_code', 'financial_year', 'triage_code']) }} as ed_presentation_key,
        coalesce({{ dbt_utils.generate_surrogate_key(['hospital_code']) }}, '-1')  as hospital_key,
        coalesce({{ dbt_utils.generate_surrogate_key(['triage_code']) }}, '-1')    as triage_key,
        cast(cast(left(financial_year, 4) as integer) * 10000 + 701 as integer)    as date_key,
        cast(financial_year as varchar)                 as financial_year,
        cast(triage_code as integer)                    as triage_code,
        cast(total_presentations as integer)            as total_presentations,
        cast(median_wait_minutes as integer)            as median_wait_minutes,
        cast(pct_seen_on_time as double)                as pct_seen_on_time,
        cast(four_hour_rule_pct as double)              as four_hour_rule_pct,
        cast(national_median_wait_minutes as integer)   as national_median_wait_minutes,
        cast(national_on_time_pct as double)            as national_on_time_pct,
        cast(on_time_target_pct as double)              as on_time_target_pct,
        cast(variance_from_national_minutes as integer) as variance_from_national_minutes,
        cast(benchmark_met_flag as boolean)             as benchmark_met_flag
    from enriched

)

select * from final
