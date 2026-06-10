/*
    fct_patient_encounters — Gold fact at encounter grain (SYNTHETIC / Synthea).
    Surrogate PK: encounter_key.
    FKs: hospital_key -> dim_hospital, date_key -> dim_date,
         patient_demo_key -> dim_patient_demographics,
         diagnosis_key -> dim_diagnosis, geography_key -> dim_geography.
*/

with enriched as (
    select * from {{ ref('int_encounters__enriched') }}
),

final as (

    select
        {{ dbt_utils.generate_surrogate_key(['encounter_id']) }}      as encounter_key,
        cast(patient_id as varchar)                                  as patient_id,
        coalesce({{ dbt_utils.generate_surrogate_key(['hospital_code']) }}, '-1') as hospital_key,
        cast(extract(year from start_date) * 10000
             + extract(month from start_date) * 100
             + extract(day from start_date) as integer)              as date_key,
        coalesce({{ dbt_utils.generate_surrogate_key(['age_band', 'sex', 'seifa_irsd_quintile', 'indigenous_flag']) }}, '-1') as patient_demo_key,
        coalesce({{ dbt_utils.generate_surrogate_key(['primary_diagnosis_code']) }}, '-1') as diagnosis_key,
        coalesce({{ dbt_utils.generate_surrogate_key(['postcode']) }}, '-1') as geography_key,
        cast(encounter_class as varchar)         as encounter_class,
        cast(age_years as double)                as age_years,
        cast(age_band as varchar)                as age_band,
        cast(is_paediatric as boolean)           as is_paediatric,
        cast(los_hours as double)                as los_hours,
        cast(total_cost as double)               as total_cost,
        cast(is_readmission_30d as boolean)      as is_readmission_30d,
        cast(had_readmission_30d as boolean)     as had_readmission_30d
    from enriched

)

select * from final
