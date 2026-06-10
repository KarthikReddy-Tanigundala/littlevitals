/*
    Staging: elective surgery waitlist episodes (SYNTHETIC). Rename + type-cast.
*/

with source as (

    {% if target.type == 'snowflake' %}
    select * from {{ source('elective', 'raw_elective_surgery_episodes') }}
    {% else %}
    select * from {{ ref('raw_elective_surgery_episodes') }}
    {% endif %}

),

renamed as (

    select
        cast(episode_id as varchar)        as episode_id,
        cast(hospital_code as varchar)     as hospital_code,
        cast(urgency_category as integer)  as urgency_category,
        cast(specialty as varchar)         as specialty,
        cast(added_date as date)           as added_date,
        cast(wait_days as integer)         as wait_days,
        cast(removal_reason as varchar)    as removal_reason,
        cast(admitted_flag as integer)     as admitted_flag
    from source

)

select * from renamed
