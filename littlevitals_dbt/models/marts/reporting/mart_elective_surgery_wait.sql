/*
    mart_elective_surgery_wait — elective waiting times by hospital x FY x urgency.
    Wait-time statistics are computed over ADMITTED episodes (completed waits);
    overdue counts use all episodes. SYNTHETIC.
*/

with fct as (
    select * from {{ ref('fct_elective_surgery') }}
),

hosp as (
    select * from {{ ref('dim_hospital') }}
),

urgency as (
    select * from {{ ref('dim_urgency_category') }}
),

joined as (
    select
        fct.financial_year,
        fct.wait_days,
        fct.is_admitted,
        fct.is_overdue,
        hosp.hospital_name,
        hosp.state_code,
        urgency.urgency_code,
        urgency.urgency_name,
        urgency.recommended_max_wait_days
    from fct
    inner join hosp    on fct.hospital_key = hosp.hospital_key
    inner join urgency on fct.urgency_key  = urgency.urgency_key
)

select
    hospital_name,
    state_code,
    financial_year,
    urgency_code,
    urgency_name,
    count(*)                                                    as episodes,
    sum(case when is_admitted then 1 else 0 end)                as admitted_episodes,
    cast(round(median(case when is_admitted then wait_days end)) as integer)
                                                                as median_wait_days,
    cast(round(quantile_cont(
        case when is_admitted then wait_days end, 0.9)) as integer)
                                                                as p90_wait_days,
    cast(round(
        sum(case when is_admitted and wait_days <= recommended_max_wait_days then 1.0 else 0.0 end)
        / nullif(sum(case when is_admitted then 1.0 else 0.0 end), 0), 3) as double)
                                                                as pct_on_time,
    sum(case when is_overdue then 1 else 0 end)                 as overdue_count
from joined
group by hospital_name, state_code, financial_year, urgency_code, urgency_name
