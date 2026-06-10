-- Singular test: ED median wait must be non-negative and within 24 hours.
-- A wait outside [0, 1440] minutes signals a data or transformation error.
-- Returns offending rows (build fails if any are returned).

select
    ed_presentation_key,
    median_wait_minutes
from {{ ref('fct_ed_presentations') }}
where median_wait_minutes < 0
   or median_wait_minutes > 1440
