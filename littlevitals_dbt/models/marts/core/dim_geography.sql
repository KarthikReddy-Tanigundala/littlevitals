/*
    dim_geography — Victorian postcode → suburb / SA2 / PHN / SEIFA / remoteness,
    plus an Unknown member. Powers equity analysis.
*/

with geo as (
    select * from {{ ref('seed_vic_geography') }}
),

geography as (
    select
        {{ dbt_utils.generate_surrogate_key(['postcode']) }} as geography_key,
        postcode,
        suburb,
        sa2_name,
        phn_name,
        seifa_irsd_quintile,
        remoteness_area
    from geo
),

unknown_member as (
    select
        '-1'                  as geography_key,
        'UNKNOWN'             as postcode,
        'Unknown'             as suburb,
        'Unknown'             as sa2_name,
        'Unknown'             as phn_name,
        cast(null as integer) as seifa_irsd_quintile,
        'Unknown'             as remoteness_area
),

combined as (
    select * from geography
    union all
    select * from unknown_member
),

final as (
    select
        cast(geography_key as varchar)       as geography_key,
        cast(postcode as varchar)            as postcode,
        cast(suburb as varchar)              as suburb,
        cast(sa2_name as varchar)            as sa2_name,
        cast(phn_name as varchar)            as phn_name,
        cast(seifa_irsd_quintile as integer) as seifa_irsd_quintile,
        cast(remoteness_area as varchar)     as remoteness_area
    from combined
)

select * from final
