/*
    fct_elective_surgery — Gold fact at waitlist-episode grain (SYNTHETIC).
    Surrogate PK: elective_episode_key. is_admitted is the survival event;
    non-admitted episodes are right-censored.
    FKs: hospital_key -> dim_hospital, urgency_key -> dim_urgency_category,
         specialty_key -> dim_surgical_specialty, date_key -> dim_date (added date).
*/

with enriched as (
    select * from {{ ref('int_elective__episodes_enriched') }}
),

final as (

    select
        {{ dbt_utils.generate_surrogate_key(['episode_id']) }}                 as elective_episode_key,
        coalesce({{ dbt_utils.generate_surrogate_key(['hospital_code']) }}, '-1')     as hospital_key,
        coalesce({{ dbt_utils.generate_surrogate_key(['urgency_category']) }}, '-1')  as urgency_key,
        coalesce({{ dbt_utils.generate_surrogate_key(['specialty_code']) }}, '-1')    as specialty_key,
        cast(extract(year from added_date) * 10000
             + extract(month from added_date) * 100
             + extract(day from added_date) as integer)        as date_key,
        cast(financial_year as varchar)              as financial_year,
        cast(wait_days as integer)                   as wait_days,
        cast(recommended_max_wait_days as integer)   as recommended_max_wait_days,
        cast(is_overdue as boolean)                  as is_overdue,
        cast(is_admitted as boolean)                 as is_admitted,
        cast(removal_reason as varchar)              as removal_reason
    from enriched

)

select * from final
