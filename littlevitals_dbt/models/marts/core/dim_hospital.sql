/*
    dim_hospital — conformed hospital dimension (SCD Type 1).
    Includes a '-1' Unknown member so facts that fail to match still join and
    referential-integrity tests stay green (CLAUDE.md 27.2).
*/

with units as (
    select * from {{ ref('stg_aihw__reporting_units') }}
),

states as (
    select * from {{ ref('seed_state_names') }}
),

hospitals as (

    select
        {{ dbt_utils.generate_surrogate_key(['units.hospital_code']) }} as hospital_key,
        units.hospital_code,
        units.hospital_name,
        units.state_code,
        states.state_name,
        units.lhn_name,
        units.peer_group,
        units.latitude,
        units.longitude,
        case when units.peer_group = 'Children''s hospitals' then true else false end as is_paediatric
    from units
    left join states on units.state_code = states.state_code

),

unknown_member as (

    select
        '-1'               as hospital_key,
        'UNKNOWN'          as hospital_code,
        'Unknown Hospital' as hospital_name,
        'NA'               as state_code,
        'Not Applicable'   as state_name,
        'Unknown'          as lhn_name,
        'Unknown'          as peer_group,
        cast(null as double) as latitude,
        cast(null as double) as longitude,
        false              as is_paediatric

),

combined as (
    select * from hospitals
    union all
    select * from unknown_member
),

final as (

    select
        cast(hospital_key as varchar)   as hospital_key,
        cast(hospital_code as varchar)  as hospital_code,
        cast(hospital_name as varchar)  as hospital_name,
        cast(state_code as varchar)     as state_code,
        cast(state_name as varchar)     as state_name,
        cast(lhn_name as varchar)       as lhn_name,
        cast(peer_group as varchar)     as peer_group,
        cast(latitude as double)        as latitude,
        cast(longitude as double)       as longitude,
        cast(is_paediatric as boolean)  as is_paediatric
    from combined

)

select * from final
