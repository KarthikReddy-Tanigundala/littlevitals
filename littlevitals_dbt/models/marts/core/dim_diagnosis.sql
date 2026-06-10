/*
    dim_diagnosis — ICD-10-AM diagnosis lookup (paediatric-focused), plus Unknown.
*/

with dx as (
    select * from {{ ref('seed_icd10_paediatric') }}
),

diagnoses as (
    select
        {{ dbt_utils.generate_surrogate_key(['condition_code']) }} as diagnosis_key,
        condition_code,
        condition_description,
        body_system,
        is_paediatric_common
    from dx
),

unknown_member as (
    select
        '-1'        as diagnosis_key,
        'UNKNOWN'   as condition_code,
        'Unknown'   as condition_description,
        'Unknown'   as body_system,
        'N'         as is_paediatric_common
),

combined as (
    select * from diagnoses
    union all
    select * from unknown_member
),

final as (
    select
        cast(diagnosis_key as varchar)          as diagnosis_key,
        cast(condition_code as varchar)         as condition_code,
        cast(condition_description as varchar)  as condition_description,
        cast(body_system as varchar)            as body_system,
        cast(is_paediatric_common as varchar)   as is_paediatric_common
    from combined
)

select * from final
