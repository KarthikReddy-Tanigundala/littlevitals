-- Singular test: validates the australian_financial_year macro at FY boundaries.
-- 1 Jul 2024 -> "2024-25"; 30 Jun 2024 -> "2023-24"; 15 Jan 2025 -> "2024-25".
-- Returns rows only if the macro mislabels any boundary date.

select full_date, aus_financial_year
from {{ ref('dim_date') }}
where (full_date = cast('2024-07-01' as date) and aus_financial_year <> '2024-25')
   or (full_date = cast('2024-06-30' as date) and aus_financial_year <> '2023-24')
   or (full_date = cast('2025-01-15' as date) and aus_financial_year <> '2024-25')
