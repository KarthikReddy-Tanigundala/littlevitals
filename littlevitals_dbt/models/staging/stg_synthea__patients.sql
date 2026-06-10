/*
    Staging: Synthea synthetic patients (SYNTHETIC). Rename + type-cast only.
*/

with source as (

    {% if target.type == 'snowflake' %}
    select * from {{ source('synthea', 'raw_synthea_patients') }}
    {% else %}
    select * from {{ ref('raw_synthea_patients') }}
    {% endif %}

),

renamed as (

    select
        cast(patient_id as varchar)      as patient_id,
        cast(birthdate as date)          as birthdate,
        upper(cast(sex as varchar))      as sex,
        cast(postcode as varchar)        as postcode,
        upper(cast(indigenous_flag as varchar)) as indigenous_flag
    from source

)

select * from renamed
