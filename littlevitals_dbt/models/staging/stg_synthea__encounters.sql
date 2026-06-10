/*
    Staging: Synthea synthetic encounters (SYNTHETIC). Rename + type-cast only.
*/

with source as (

    {% if target.type == 'snowflake' %}
    select * from {{ source('synthea', 'raw_synthea_encounters') }}
    {% else %}
    select * from {{ ref('raw_synthea_encounters') }}
    {% endif %}

),

renamed as (

    select
        cast(encounter_id as varchar)           as encounter_id,
        cast(patient_id as varchar)             as patient_id,
        cast(start_date as date)                as start_date,
        lower(cast(encounter_class as varchar)) as encounter_class,
        cast(hospital_code as varchar)          as hospital_code,
        cast(los_hours as double)               as los_hours,
        cast(total_cost as double)              as total_cost,
        cast(primary_diagnosis_code as varchar) as primary_diagnosis_code
    from source

)

select * from renamed
