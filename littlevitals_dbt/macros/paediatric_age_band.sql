{#
    paediatric_age_band(age_years)
    ------------------------------
    Map an age in (fractional) years to a paediatric age band. Bands match the
    Power BI DAX labels in CLAUDE.md §5.3 so the semantics are identical across
    the dbt model and the BI layer.

        Neonate (0–28d) | Infant (1–12m) | Toddler (1–3y) |
        Child (4–12y)   | Adolescent (13–17y) | Adult (18+y)
#}
{% macro paediatric_age_band(age_years) -%}
    case
        when {{ age_years }} < (28.0 / 365.25) then 'Neonate (0–28d)'
        when {{ age_years }} < 1  then 'Infant (1–12m)'
        when {{ age_years }} < 4  then 'Toddler (1–3y)'
        when {{ age_years }} < 13 then 'Child (4–12y)'
        when {{ age_years }} < 18 then 'Adolescent (13–17y)'
        else 'Adult (18+y)'
    end
{%- endmacro %}
