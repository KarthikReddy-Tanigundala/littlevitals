-- Singular reconciliation test (CLAUDE.md 27.4): total VIC ED presentations in
-- the Gold fact must equal the cleaned staging total within tolerance. This is
-- the test that proves the transformation neither dropped nor duplicated rows.
-- Returns a row only when the totals diverge beyond var('recon_tolerance').

with gold as (
    select sum(f.total_presentations) as total_presentations
    from {{ ref('fct_ed_presentations') }} f
    inner join {{ ref('dim_hospital') }} h on f.hospital_key = h.hospital_key
    where h.state_code = 'VIC'
),

staged as (
    select sum(total_presentations) as total_presentations
    from {{ ref('stg_aihw__ed_presentations') }}
    where state_code = 'VIC'
)

select
    gold.total_presentations  as gold_total,
    staged.total_presentations as staged_total
from gold
cross join staged
where abs(gold.total_presentations - staged.total_presentations)
      > ({{ var('recon_tolerance') }} * staged.total_presentations)
