/*
    dim_patient_demographics — demographic "junk" dimension: distinct combinations
    of age band, sex, SEIFA-IRSD quintile and Indigenous status, plus an Unknown
    member. SYNTHETIC (Synthea-derived).
*/

with encounters as (
    select * from {{ ref('int_encounters__enriched') }}
),

distinct_combos as (
    select distinct age_band, sex, seifa_irsd_quintile, indigenous_flag
    from encounters
),

demographics as (
    select
        {{ dbt_utils.generate_surrogate_key(['age_band', 'sex', 'seifa_irsd_quintile', 'indigenous_flag']) }} as patient_demo_key,
        age_band,
        sex,
        seifa_irsd_quintile,
        indigenous_flag,
        case when age_band <> 'Adult (18+y)' then true else false end as is_paediatric
    from distinct_combos
),

unknown_member as (
    select
        '-1'                  as patient_demo_key,
        'Unknown'             as age_band,
        'U'                   as sex,
        cast(null as integer) as seifa_irsd_quintile,
        'U'                   as indigenous_flag,
        false                 as is_paediatric
),

combined as (
    select * from demographics
    union all
    select * from unknown_member
),

final as (
    select
        cast(patient_demo_key as varchar)    as patient_demo_key,
        cast(age_band as varchar)            as age_band,
        cast(sex as varchar)                 as sex,
        cast(seifa_irsd_quintile as integer) as seifa_irsd_quintile,
        cast(indigenous_flag as varchar)     as indigenous_flag,
        cast(is_paediatric as boolean)       as is_paediatric
    from combined
)

select * from final
