/*
    mart_hospital_scorecard — one row per hospital per financial year.
    Primary mart for the Power BI executive scorecard. Aggregates the triage-grain
    fact up to hospital x FY, pivots out the closely-watched Cat 2 / Cat 3 on-time
    rates, applies a rating, and adds year-on-year deltas.
*/

with fct as (
    select * from {{ ref('fct_ed_presentations') }}
),

hosp as (
    select * from {{ ref('dim_hospital') }}
),

joined as (
    select
        f.financial_year,
        f.triage_code,
        f.total_presentations,
        f.median_wait_minutes,
        f.pct_seen_on_time,
        f.four_hour_rule_pct,
        h.hospital_name,
        h.lhn_name,
        h.peer_group,
        h.state_name,
        h.state_code,
        h.latitude,
        h.longitude
    from fct f
    inner join hosp h on f.hospital_key = h.hospital_key
),

agg as (

    select
        hospital_name,
        lhn_name,
        peer_group,
        state_name,
        state_code,
        financial_year,
        sum(total_presentations) as total_ed_presentations,
        cast(round(
            sum(median_wait_minutes * total_presentations)
            / nullif(sum(total_presentations), 0)
        ) as integer) as median_ed_wait_all_triage,
        max(case when triage_code = 2 then pct_seen_on_time end) as pct_ed_seen_on_time_cat2,
        max(case when triage_code = 3 then pct_seen_on_time end) as pct_ed_seen_on_time_cat3,
        max(four_hour_rule_pct) as four_hour_rule_pct,
        max(latitude) as latitude,
        max(longitude) as longitude
    from joined
    group by hospital_name, lhn_name, peer_group, state_name, state_code, financial_year

),

scored as (

    select
        *,
        case
            when pct_ed_seen_on_time_cat2 >= 0.80 then 'Meets Benchmark'
            when pct_ed_seen_on_time_cat2 >= 0.70 then 'At Risk'
            else 'Below Benchmark'
        end as scorecard_overall_rating,
        round(
            (total_ed_presentations
                - lag(total_ed_presentations) over (partition by hospital_name order by financial_year))
            * 100.0
            / nullif(lag(total_ed_presentations) over (partition by hospital_name order by financial_year), 0)
        , 1) as yoy_ed_presentations_growth_pct,
        median_ed_wait_all_triage
            - lag(median_ed_wait_all_triage) over (partition by hospital_name order by financial_year)
            as yoy_median_wait_change_minutes
    from agg

)

select
    hospital_name,
    lhn_name,
    peer_group,
    state_name,
    state_code,
    financial_year,
    total_ed_presentations,
    median_ed_wait_all_triage,
    pct_ed_seen_on_time_cat2,
    pct_ed_seen_on_time_cat3,
    four_hour_rule_pct,
    scorecard_overall_rating,
    yoy_ed_presentations_growth_pct,
    yoy_median_wait_change_minutes,
    latitude,
    longitude
from scored
