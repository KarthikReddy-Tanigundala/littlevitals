/*
    dim_date — Australian financial-year date dimension.
    Daily spine (2010-2030) with calendar + AUS FY attributes. The FY runs
    1 Jul -> 30 Jun and is labelled "YYYY-YY" (see australian_financial_year macro).
*/

with spine as (

    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('" ~ var('date_spine_start') ~ "' as date)",
        end_date="cast('" ~ var('date_spine_end') ~ "' as date)"
    ) }}

),

calendar as (
    select cast(date_day as date) as full_date from spine
),

final as (

    select
        cast(extract(year from full_date) * 10000
             + extract(month from full_date) * 100
             + extract(day from full_date) as integer)              as date_key,
        full_date,
        cast(extract(isodow from full_date) as integer)             as day_of_week,
        case extract(isodow from full_date)
            when 1 then 'Monday'   when 2 then 'Tuesday' when 3 then 'Wednesday'
            when 4 then 'Thursday' when 5 then 'Friday'  when 6 then 'Saturday'
            else 'Sunday' end                                       as day_name,
        cast(extract(year from full_date) as integer)               as calendar_year,
        cast(extract(month from full_date) as integer)              as calendar_month,
        case extract(month from full_date)
            when 1 then 'January'  when 2 then 'February' when 3 then 'March'
            when 4 then 'April'    when 5 then 'May'      when 6 then 'June'
            when 7 then 'July'     when 8 then 'August'   when 9 then 'September'
            when 10 then 'October' when 11 then 'November' else 'December'
        end                                                         as calendar_month_name,
        cast(extract(quarter from full_date) as integer)            as calendar_quarter,
        {{ australian_financial_year('full_date') }}                as aus_financial_year,
        cast(
            cast(case when extract(month from full_date) >= 7
                      then extract(year from full_date)
                      else extract(year from full_date) - 1 end as varchar)
            || '-07-01' as date)                                    as aus_financial_year_start_date,
        cast(case when extract(month from full_date) >= 7
                  then extract(month from full_date) - 6
                  else extract(month from full_date) + 6 end as integer) as aus_fy_month,
        cast(ceil(
            (case when extract(month from full_date) >= 7
                  then extract(month from full_date) - 6
                  else extract(month from full_date) + 6 end) / 3.0) as integer) as aus_fy_quarter,
        cast(case when extract(isodow from full_date) <= 5 then true else false end as boolean) as is_weekday
    from calendar

)

select * from final
