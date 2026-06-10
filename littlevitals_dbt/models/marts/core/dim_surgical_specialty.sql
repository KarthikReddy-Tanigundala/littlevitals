/*
    dim_surgical_specialty — surgical specialty (SRG) reference, plus Unknown.
*/

with specialty as (
    select * from {{ ref('seed_surgical_specialties') }}
),

specialties as (
    select
        {{ dbt_utils.generate_surrogate_key(['specialty_code']) }} as specialty_key,
        specialty_code,
        specialty_name,
        srg_group
    from specialty
),

unknown_member as (
    select
        '-1'       as specialty_key,
        'UNK'      as specialty_code,
        'Unknown'  as specialty_name,
        'Unknown'  as srg_group
),

combined as (
    select * from specialties
    union all
    select * from unknown_member
),

final as (
    select
        cast(specialty_key as varchar)  as specialty_key,
        cast(specialty_code as varchar) as specialty_code,
        cast(specialty_name as varchar) as specialty_name,
        cast(srg_group as varchar)      as srg_group
    from combined
)

select * from final
