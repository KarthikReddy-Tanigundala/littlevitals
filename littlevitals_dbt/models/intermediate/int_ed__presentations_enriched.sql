/*
    Intermediate (Silver): enrich ED presentations with hospital attributes,
    national benchmarks, and the ATS on-time target, then derive the comparison
    measures consumed by the Gold fact. One row per hospital x FY x triage.
*/

with ed as (
    select * from {{ ref('stg_aihw__ed_presentations') }}
),

units as (
    select * from {{ ref('stg_aihw__reporting_units') }}
),

benchmarks as (
    select * from {{ ref('seed_national_benchmarks') }}
),

triage as (
    select * from {{ ref('seed_triage_categories') }}
),

joined as (

    select
        ed.hospital_code,
        ed.hospital_name,
        ed.state_code,
        ed.financial_year,
        ed.triage_code,
        ed.total_presentations,
        ed.median_wait_minutes,
        ed.pct_seen_on_time,
        ed.four_hour_rule_pct,
        units.lhn_name,
        units.peer_group,
        units.latitude,
        units.longitude,
        benchmarks.national_median_wait_minutes,
        benchmarks.national_on_time_pct,
        triage.on_time_target_pct,
        ed.median_wait_minutes - benchmarks.national_median_wait_minutes
            as variance_from_national_minutes,
        case
            when ed.pct_seen_on_time >= triage.on_time_target_pct then true
            else false
        end as benchmark_met_flag

    from ed
    left join units      on ed.hospital_code  = units.hospital_code
    left join benchmarks on ed.financial_year = benchmarks.financial_year
                        and ed.triage_code    = benchmarks.triage_code
    left join triage     on ed.triage_code    = triage.triage_code

)

select * from joined
