/*
    dim_triage_category — ATS categories 1-5 with clinical targets, plus a '-1'
    Unknown member.
*/

with triage as (
    select * from {{ ref('seed_triage_categories') }}
),

categories as (

    select
        {{ dbt_utils.generate_surrogate_key(['triage_code']) }} as triage_key,
        triage_code,
        triage_name,
        max_wait_minutes,
        on_time_target_pct,
        description
    from triage

),

unknown_member as (

    select
        '-1'                    as triage_key,
        -1                      as triage_code,
        'Unknown'               as triage_name,
        cast(null as integer)   as max_wait_minutes,
        cast(null as double)    as on_time_target_pct,
        'Unknown triage category' as description

),

combined as (
    select * from categories
    union all
    select * from unknown_member
),

final as (

    select
        cast(triage_key as varchar)         as triage_key,
        cast(triage_code as integer)        as triage_code,
        cast(triage_name as varchar)        as triage_name,
        cast(max_wait_minutes as integer)   as max_wait_minutes,
        cast(on_time_target_pct as double)  as on_time_target_pct,
        cast(description as varchar)         as description
    from combined

)

select * from final
