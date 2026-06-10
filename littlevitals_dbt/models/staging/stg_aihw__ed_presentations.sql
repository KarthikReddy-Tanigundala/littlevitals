/*
    Staging: AIHW ED presentations (1:1 with source — rename + type-cast only).

    Reads the live Snowflake landing table in prod, or the committed fixture seed
    on DuckDB (dev/CI), so the model graph is identical across environments.
*/

with source as (

    {% if target.type == 'snowflake' %}
    select * from {{ source('aihw', 'raw_aihw_ed_presentations') }}
    {% else %}
    select * from {{ ref('raw_aihw_ed_presentations') }}
    {% endif %}

),

renamed as (

    select
        cast(hospital_code as varchar)          as hospital_code,
        cast(hospital_name as varchar)          as hospital_name,
        upper(cast(state as varchar))           as state_code,
        cast(financial_year as varchar)         as financial_year,
        cast(triage_category as integer)        as triage_code,
        cast(total_presentations as integer)    as total_presentations,
        cast(median_wait_minutes as integer)    as median_wait_minutes,
        cast(pct_seen_on_time as double)        as pct_seen_on_time,
        cast(four_hour_rule_pct as double)      as four_hour_rule_pct
    from source

)

select * from renamed
