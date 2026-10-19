# Source snapshot and reproducibility

The source pool contains 506 provisional decisions retained after screening 4,232 New York Appellate Division search clusters for 2010–2024. The five-phrase search was:

```text
("premises liability" OR "slip and fall" OR "trip and fall" OR "slipped and fell" OR "tripped and fell")
```

CourtListener supplied candidate metadata and opinion IDs. Opinion text was retrieved through CourtListener's API or the linked official New York court source. The source links and retrieval-origin field are retained. Text has been normalized to Unicode NFKC and collapsed whitespace by the earlier retrieval pipeline. The hash identifies exactly the text being annotated, not the original HTML bytes.

The 506 were not independently human-validated. They were selected by an automated pre-screen with assistant calibration checks, so this annotation exercise measures the quality of that retained pool. It cannot estimate recall among all New York cases or validate all prior exclusions.

Previous outcome labels, eligibility decisions, screening reasons, notes and selected evidence were intentionally left out of this repository's source inputs. The frozen source contains opinion text, public case metadata, text hashes, and neutral passage offsets only. A full opinion naturally contains its outcome, which annotators need to read to assign labels.

`source/package_manifest.json` records the original local input-file hash, random seed, batch/year/word counts and lengths. `source/assignments.json` records batch membership, calibration/pilot membership and preliminary period (the original ownership terminology is historical; all reviewers now process all three batches). `source/family_hints.json` flags repeated names/docket strings for later human checking; it is not complete deduplication.

Batch seed is 20261016. The allocator balances reading load within filing years subject to exact capacities 169/169/168. It does not use previous outcome labels. Calibration samples two cases from each of six training-year bands; pilot inputs select five other training cases in each assignment. Passages are artificial text segments of roughly 1,200 characters with exact offsets and no lost source characters. The provided codebook explains this to annotators.

The package builder is included under `scripts/build_annotation_package.py` for inspection/reproduction from the original retained local JSONL snapshot. It requires that original input path as an argument; ordinary annotation does not need the original labeled snapshot. Do not upload that original snapshot into calibration chats. A release can be regenerated from the distributed blinded source with the assigned manifests without recovering old labels.

The case texts are public judicial materials. Preserve source attribution, URLs and snapshot hashes. No new blanket copyright/license claim is made over external text, and no API credentials are included. The source records are for the agreed academic research workflow.

Offline checks, from `annotation/`:

```sh
python scripts/check_package.py
python -m unittest discover -s tests -v
```

Run the full package check on the full repository, not a single-batch ZIP (which contains only a subset). Archive contents and checksums can be checked through `downloads/checksums.json`.

