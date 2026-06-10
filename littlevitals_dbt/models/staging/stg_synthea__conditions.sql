/*
    Staging: Synthea synthetic conditions/diagnoses (SYNTHETIC). Rename + cast.
*/

with source as (

    {% if target.type == 'snowflake' %}
    select * from {{ source('synthea', 'raw_synthea_conditions') }}
    {% else %}
    select * from {{ ref('raw_synthea_conditions') }}
    {% endif %}

),

renamed as (

    select
        cast(patient_id as varchar)            as patient_id,
        cast(encounter_id as varchar)          as encounter_id,
        cast(condition_code as varchar)        as condition_code,
        cast(condition_description as varchar) as condition_description,
        cast(onset_date as date)               as onset_date
    from source

)

select * from renamed
