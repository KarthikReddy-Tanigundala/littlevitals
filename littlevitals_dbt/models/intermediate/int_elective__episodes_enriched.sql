/*
    Intermediate (Silver): enrich elective episodes with urgency + specialty
    reference data, derive the Australian financial year, overdue flag and the
    admitted (event) flag for survival analysis. Grain: one waitlist episode.
*/

with episodes as (
    select * from {{ ref('stg_elective__episodes') }}
),

urgency as (
    select * from {{ ref('seed_urgency_categories') }}
),

specialty as (
    select * from {{ ref('seed_surgical_specialties') }}
),

joined as (

    select
        episodes.episode_id,
        episodes.hospital_code,
        episodes.urgency_category,
        episodes.specialty,
        episodes.added_date,
        episodes.wait_days,
        episodes.removal_reason,
        episodes.admitted_flag,
        urgency.urgency_name,
        urgency.recommended_max_wait_days,
        specialty.specialty_code,
        specialty.srg_group,
        {{ australian_financial_year('episodes.added_date') }} as financial_year,
        case when episodes.wait_days > urgency.recommended_max_wait_days
             then true else false end as is_overdue,
        case when episodes.admitted_flag = 1 then true else false end as is_admitted
    from episodes
    left join urgency   on episodes.urgency_category = urgency.urgency_code
    left join specialty on episodes.specialty        = specialty.specialty_name

)

select * from joined
