/*
    mart_paediatric_summary — paediatric encounters summarised by diagnosis.
    One row per ICD-10-AM code (paediatric encounters only): volume, distinct
    patients, average length of stay, and 30-day readmission rate. Feeds the
    paediatric dashboard page. SYNTHETIC.
*/

with enc as (
    select * from {{ ref('fct_patient_encounters') }}
    where is_paediatric
),

dx as (
    select * from {{ ref('dim_diagnosis') }}
),

joined as (
    select
        dx.condition_code,
        dx.condition_description,
        dx.body_system,
        enc.patient_id,
        enc.los_hours,
        enc.is_readmission_30d
    from enc
    inner join dx on enc.diagnosis_key = dx.diagnosis_key
)

select
    condition_code,
    condition_description,
    body_system,
    count(*)                                                  as encounters,
    count(distinct patient_id)                                as distinct_patients,
    cast(round(avg(los_hours), 1) as double)                  as avg_los_hours,
    cast(round(avg(case when is_readmission_30d then 1.0 else 0.0 end), 3) as double)
                                                              as readmission_rate_30d
from joined
group by condition_code, condition_description, body_system
order by encounters desc
