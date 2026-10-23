# Case-family review — assistant draft

## Results

- Screened all 506 frozen source records (127,765 pairs), then reviewed all 53 candidate pairs.
- No identical full-text hashes or normalized-text hashes across different source records.
- Ten pairs are publication variants of the same opinions; they are grouped, retained, and not counted as independent disputes.
- Coreano is one additional family containing two distinct companion appeals.
- Forty-two candidates were rejected as surname or shared-legal-language false positives.
- No amended/superseding appellate-opinion pair was identified in the frozen snapshot. External publication history was not checked.
- 495 observed families cover all 506 records. All 114 MVP cases remain, in 114 distinct observed families.
- Five MVP families have another record outside the 114-case subset; no linked pair has both members inside it.
- No known linked family spans the proposed chronological periods. Missing companion dates remain unresolved.
- All 1,954 existing source passages and 506 annotation-packet case memberships have family mappings.

## Supported links

| Source case IDs | Relationship | MVP member(s) |
|---|---|---|
| NY-4303491 / NY-6228997 | same opinion publication variant | NY-4303491 |
| NY-4304286 / NY-6207931 | same opinion publication variant | None |
| NY-4304440 / NY-6207337 | same opinion publication variant | None |
| NY-4304488 / NY-6204784 | same opinion publication variant | NY-4304488 |
| NY-4304730 / NY-6199158 | same opinion publication variant | NY-6199158 |
| NY-4306330 / NY-6111859 | same opinion publication variant | None |
| NY-4306359 / NY-6112018 | same opinion publication variant | None |
| NY-4308801 / NY-6004283 | same opinion publication variant | NY-6004283 |
| NY-4387315 / NY-6235219 | same opinion publication variant | None |
| NY-4389907 / NY-6235554 | same opinion publication variant | None |
| NY-4849013 / NY-4849014 | related litigation companion appeals | NY-4849014 |

## Coreano and Sodhi

**Coreano:** NY-4849013 and NY-4849014 share Index No. 514351/15, Edwin Coreano, the same stairway accident, and the January 20, 2021 decision date. Slip opinions 00290 and 00289 address different appealed rulings; 00290 expressly cites the other as “decided herewith.” Both remain in FAM-NY-4849013, together with all their passages. Only NY-4849014 is in the MVP.

**Sodhi:** NY-4655053 discusses appeal No. 1 by Portage/Baldwin and appeal No. 2 by Tops arising from the same parking-lot accident. Only one Sodhi record/name/full-text match exists in the 506-case pool. Retain its family ID FAM-NY-4655053, but hold its final family/split decision until the companion identity/date are resolved or a documented scope decision is made. No external record or date is invented.

Rozier (NY-4552386), Hartnett (NY-4665270), and Gould (NY-4855957) also have missing-companion warnings outside the MVP. Ordinary references to appeal numbers in cited precedents do not join families.

## Calibration inheritance

Germain NY-6004283 is the publication counterpart of calibration case NY-4308801. Training-only status therefore propagates to the selected Germain record. The four currently recorded training-only MVP cases are:

- `NY-2757329`
- `NY-4546774`
- `NY-4840329`
- `NY-6004283`

The family manifest records calibration-origin IDs. Prior exposure not recorded in the supplied manifest/notes still needs confirmation.

## Uncertainty and review status

All family decisions are assistant drafts, not human adjudication. The ten publication-variant pairs retain unresolved canonical-text/publication-precedence choices; their grouping does not require deleting either record. Four companion warnings remain unresolved, one affecting MVP (Sodhi). Evidence and uncertainties are saved in the pair review log and uncertain-matches file.

Every other case receives a provisional singleton group, not a guarantee of independence. Thresholds and incomplete source metadata limit recall. Matching names or court language alone is insufficient; no external docket lookup was performed. Publication “As corrected through” boilerplate and amended trial orders/pleadings do not establish a separately amended appellate opinion.

## Reproduction and validation

Run `review_case_families.ipynb` from MVP or anywhere inside the repository. It uses `family_review/family_audit.py` and the saved evidence decisions. All six code cells executed successfully from both MVP and the repository root with identical outputs. Checks cover source/evidence hashes, exact quote offsets, candidate decision coverage, unique IDs, passage coverage, family consistency, unchanged targets/IDs, and rejection of synthetic family/calibration leakage or unknown/conflicting chunk IDs.

Existing multi-case A/B/C annotation packets are not model splitting units. The packet manifest records per-case membership; source passages and future encoder chunks inherit their parent case family. The helper provides family-level partition checks but does not create the chronological experiment split or replace target-review checks.

## Saved artifacts

- `review_case_families.ipynb`: executable review and manifest notebook.
- `family_review/`: screening implementation, saved candidate screen, token differences, and assistant review decisions.
- `data/family_v1/`: family, case, passage, packet, evidence, uncertainty, summary, and provenance artifacts.
- `data/metadata_v2_family_review/metadata.jsonl`: updated 114-case metadata with family IDs and inherited calibration flags.

Earlier metadata, original submissions, all source opinions, and the 114 selected IDs are preserved. No canonical opinion was deleted, no target label was changed, and no final split was assigned. Later family/source changes require a new dataset version and affected experiments to be rerun.
