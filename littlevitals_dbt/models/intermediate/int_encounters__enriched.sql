/*
    Intermediate (Silver): enrich Synthea encounters with patient demographics,
    geography (SA2 / SEIFA), and diagnosis attributes; derive age at encounter,
    paediatric age band, and a 30-day readmission flag (window function).
    Grain: one row per encounter. SYNTHETIC.
*/

with enc as (
    select * from {{ ref('stg_synthea__encounters') }}
),

pat as (
    select * from {{ ref('stg_synthea__patients') }}
),

geo as (
    select * from {{ ref('seed_vic_geography') }}
),

dx as (
    select * from {{ ref('seed_icd10_paediatric') }}
),

joined as (
    select
        enc.encounter_id,
        enc.patient_id,
        enc.hospital_code,
        enc.start_date,
        enc.encounter_class,
        enc.los_hours,
        enc.total_cost,
        enc.primary_diagnosis_code,
        pat.birthdate,
        pat.sex,
        pat.postcode,
        pat.indigenous_flag,
        geo.suburb,
        geo.sa2_name,
        geo.phn_name,
        geo.seifa_irsd_quintile,
        geo.remoteness_area,
        dx.condition_description,
        dx.body_system,
        datediff('day', pat.birthdate, enc.start_date) / 365.25 as age_years
    from enc
    left join pat on enc.patient_id = pat.patient_id
    left join geo on pat.postcode = geo.postcode
    left join dx on enc.primary_diagnosis_code = dx.condition_code
),

banded as (
    select
        joined.*,
        {{ paediatric_age_band('age_years') }} as age_band,
        lag(start_date) over (
            partition by patient_id order by start_date, encounter_id
        ) as prev_start_date
    from joined
),

final as (
    select
        *,
        case when age_band <> 'Adult (18+y)' then true else false end as is_paediatric,
        case
            when prev_start_date is not null
                 and datediff('day', prev_start_date, start_date) <= 30
            then true else false
        end as is_readmission_30d
    from banded
)

select * from final
