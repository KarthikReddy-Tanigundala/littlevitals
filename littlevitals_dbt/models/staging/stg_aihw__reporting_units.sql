/*
    Staging: AIHW hospital master (reporting units). Rename + type-cast only.
*/

with source as (

    {% if target.type == 'snowflake' %}
    select * from {{ source('aihw', 'raw_aihw_reporting_units') }}
    {% else %}
    select * from {{ ref('raw_aihw_reporting_units') }}
    {% endif %}

),

renamed as (

    select
        cast(hospital_code as varchar)  as hospital_code,
        cast(hospital_name as varchar)  as hospital_name,
        upper(cast(state as varchar))   as state_code,
        cast(lhn_name as varchar)       as lhn_name,
        cast(peer_group as varchar)     as peer_group,
        cast(latitude as double)        as latitude,
        cast(longitude as double)       as longitude
    from source

)

select * from renamed
