{#
    Override dbt's default schema-naming behaviour.

    Default dbt concatenates: <target_schema>_<custom_schema>. That produces
    GOLD_BRONZE etc. For a medallion warehouse we want the custom schema to be
    used VERBATIM, so models land in BRONZE / SILVER / GOLD / RAW / SEED exactly
    as configured via `+schema:` in dbt_project.yml. This behaves identically on
    DuckDB (local/CI) and Snowflake (prod).

    Falls back to target.schema when a model has no custom schema configured.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- set default_schema = target.schema -%}
    {%- if custom_schema_name is none -%}
        {{ default_schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
