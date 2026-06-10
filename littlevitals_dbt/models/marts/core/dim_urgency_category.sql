/*
    dim_urgency_category — elective surgery urgency categories 1-3 with clinically
    recommended maximum wait (days), plus an Unknown member.
*/

with urgency as (
    select * from {{ ref('seed_urgency_categories') }}
),

categories as (
    select
        {{ dbt_utils.generate_surrogate_key(['urgency_code']) }} as urgency_key,
        urgency_code,
        urgency_name,
        recommended_max_wait_days,
        description
    from urgency
),

unknown_member as (
    select
        '-1'                  as urgency_key,
        -1                    as urgency_code,
        'Unknown'             as urgency_name,
        cast(null as integer) as recommended_max_wait_days,
        'Unknown urgency category' as description
),

combined as (
    select * from categories
    union all
    select * from unknown_member
),

final as (
    select
        cast(urgency_key as varchar)               as urgency_key,
        cast(urgency_code as integer)              as urgency_code,
        cast(urgency_name as varchar)              as urgency_name,
        cast(recommended_max_wait_days as integer) as recommended_max_wait_days,
        cast(description as varchar)               as description
    from combined
)

select * from final
