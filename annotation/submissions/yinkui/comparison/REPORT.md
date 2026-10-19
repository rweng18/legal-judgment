# Calibration comparison for Monday discussion

Prepared October 18, 2026. This compares Yinkui's assistant draft with Becca's submitted LLM outputs and separately discusses Becca's submitted notes. It does not claim that Yinkui personally annotated or reviewed the cases.

## What was completed

- All 12 complete opinions were read and annotated under the initial 1.0.0 codebook, including all 19 legal-issue topics, factual fields, order outcomes, quotations, passage classifications and outcome cues.
- Yinkui's independent draft was committed as `b94ae3c` **before** fetching teammate submissions. The frozen draft, source/codebook hashes and original chunk outputs remain unchanged. See [independent_freeze.json](../independent_freeze.json).
- Fetched GitHub and merged remote `main` at `20fee87`, which includes Becca's work from PR #2. The fetched branches were `main`, `bw-working` and `data/ny-506-annotation`; the open-PR search returned no additional submissions. No Hyun Sang calibration submission was found at the time of this check.
- Yinkui's 12 records pass structural, source-hash, exact quotation and coverage checks. Becca's first two chunks pass; the third has one binary-label consistency error described below. These checks do not prove semantic correctness.

## Results

| Quantity | Yinkui LLM draft | Becca LLM draft |
|---|---:|---:|
| Cases annotated | 12 | 12 |
| Include / exclude / review | 7 / 1 / 4 | 8 / 1 / 3 |
| Affirmed / reversed across all opinions | 9 / 3 | 9 / 3 |
| Included label 0 / label 1 | 4 / 3 | 6 / 2 |
| Fully human-reviewed records claimed | 0 | 0 |

| Compared field | Agreement | Cohen's kappa |
|---|---:|---:|
| Current appellate disposition | 12/12 (100%) | 1.00 |
| Include / exclude / review | 7/12 (58.3%) | 0.20 |
| Subject scope | 7/12 (58.3%) | 0.20 |
| Property status | 8/12 (66.7%) | 0.25 |
| Raw binary field, including null and the invalid peer value | 8/12 (66.7%) | 0.495 |

Six cases are included by both drafts; their binary labels agree in all six (four affirmed, two reversed). This subset omits the difficult inclusion decisions and is not an accuracy estimate. Excluding Becca's entire invalid Verges record leaves binary-field agreement of 8/11; that is a separately reported denominator, not a silent repair.

The central problem in this calibration is **eligibility consistency**, rather than reading affirmed/reversed. Null in these comparisons means outside/pending admission to the binary dataset, not a third classification target. Accuracy, balanced accuracy, macro F1 and a classifier confusion matrix cannot be estimated from two LLM drafts without an independently reviewed reference set. The JSON report contains cross-tabulations with reviewer axes, explicitly not ground-truth/prediction axes.

See [the complete case table](case_table.md), [machine-readable comparison](calibration_comparison.json), and [proposed corrections](proposed_corrections.json). Raw inputs and original drafts were not changed to improve agreement.

## Cases to discuss

| Case | Yinkui | Becca LLM | Evidence and proposed next step |
|---|---|---|---|
| Rodriguez, NY-5992200 | Review | Exclude | P001 establishes ownership of the **building**; P002 discusses a pedestrian ramp outside section 7-210's abutting-owner sidewalk rule. Both drafts withhold a binary label. Decide whether that context is sufficient to label the ramp public or whether its status should remain unclear. Do not include merely because the abutting owner is private. |
| Richardson, NY-2993705 | Exclude | Review | P002 says her foot went off an unguarded walkway edge into a trench, without describing a slip or trip. Both drafts withhold a binary label. Agree whether this is a definite `other_fall` exclusion under the narrow scope, or a review case. Becca's separate notes say include, so also reconcile those notes with her LLM draft. |
| Maldonado, NY-3193933 | Review | Include | P001 says a drain in front of the condominium near its entrance; P002 describes a removed planter and construction. Agree how much location/control evidence establishes a private approach rather than an adjoining public area. Yinkui may be overly conservative; document the rule rather than automatically accepting either draft. |
| Troina, NY-4551400 | Include | Review | P002 expressly links the restaurant parking lot to alleged defendant ownership/operation/maintenance. Yinkui accepts the allegation as source-supported setting information; Becca requires stronger establishment. Clarify whether uncontradicted property allegations suffice for scope, while keeping their allegation status. |
| Gartenberg, NY-4840329 | Review | Include | P001 says a restaurant operated by Driton; no title or lease is stated. Agree whether an ordinary commercial interior is enough to establish private premises. Apply the same rule consistently to Germain and similar cases; avoid requiring documentary title in one interior case but not another without a reason. |
| Verges, NY-4795834 | Review; null | Review; **0** | Both LLM drafts flag unclear ownership of the homeless shelter (P001). Becca's label 0 contradicts review eligibility: proposed mechanical correction is **null**, preserving affirmed disposition. Her separate notes say include and also need reconciliation. |

The five include/exclude/review disagreements are Rodriguez, Richardson, Maldonado, Troina and Gartenberg. Verges is an additional invalid-label problem, not an eligibility disagreement between the structured drafts.

## One clear clarification from Becca's notes

Becca's notes question Freiser (NY-5960096) because the accident happened in 2007. The codebook's 2010–2024 window refers to **appellate opinion dates**, not incident dates. Freiser was decided May 31, 2011, so the 2007 accident does not exclude it. Both LLM drafts already include it and record the 2007 accident date separately. The actual source opinion date also places it within calibration's 2010–2020 training period.

Becca's submitted notes and her LLM eligibility differ for **four** cases: Freiser, Richardson, Troina and Verges. Keep the notes as a separate source of review evidence; do not overwrite the JSON from the notes without adjudication.

## Extra-feature issues worth resolving

The machine-readable comparison lists categorical differences beyond the five primary fields; they occur in 11 of 12 cases. Different wording or local evidence IDs alone is not counted as a categorical disagreement.

- **Orders versus motions (Jewett, P001–P002):** the opinion describes one July 2, 2010 order resolving several motions, with appeals and a cross-appeal. Yinkui records one order; Becca records three motion-level entries and `multiple_orders=true`. The current codebook unit is the independently appealed order/judgment, so one order with a detailed description is the recommended interpretation. Multiple motions are not automatically multiple orders. Both drafts correctly record a whole affirmance and practical benefit to both sides.
- **Issue discussion versus proven liability:** a court finding a triable issue still counts as `court_addressed`. In Verges P003, employee-created residue is part of the court's alternate triable-issue analysis, rather than only an unaddressed allegation. The finding text must still avoid saying creation was conclusively proved.
- **Procedural issue tags:** Becca frequently tags an ordinary summary-judgment ruling as `procedural_issue`; Yinkui reserves that tag for a separately analyzed procedural/evidentiary dispute (for example, feigned affidavits or late-disclosed witnesses). The codebook needs an explicit boundary. Avoid turning every summary-judgment opinion into an identical procedural feature.
- **Role inference:** being at one's parents' complex does not alone prove guest status (Maldonado). Visiting a bodega bathroom does not establish a customer relationship (Nieves). Operating a restaurant does not establish a tenancy (Gartenberg). Use unclear/other as appropriate, or explicitly agree how broad the visitor category is. Likewise, “defendants' home” supports a residential connection but does not necessarily prove legal ownership (Ackerman).
- **Evidence medium:** Jewett explicitly discusses a lease and rider; these can be captured as `other` documentary evidence. Troina and Gartenberg say no last-inspection **evidence**, which need not mean an inspection **record** existed or was specifically requested. Avoid inventing a documentary medium from a general evidentiary gap.
- **Quoted precedent applied to the present case:** Germain P003 uses a quoted formulation about examining a photograph, with a bracketed substitution for carpeting. Yinkui interprets it as the current court applying that assessment to this case; Becca treats it solely as precedent and omits photographs. Review the current-opinion context together; a citation does not automatically make surrounding language external case facts.
- **Hazard mechanism:** water freezing into ice may justify snow/ice alone or both water and snow/ice; choose a consistent convention. A planter that was removed is not necessarily the object plaintiff tripped over, and an unguarded trench is not necessarily an obstruction. Keep hazard coding tied to the alleged cause.
- **Appellant role in Gartenberg:** the caption shows respondent-appellant and appellant-respondent, while the opening order focuses on defendant's motion. Yinkui records both based on the caption; Becca records defendant. Check whether the schema's role should follow all appeals or only the described motion. There is still one order and a clear affirmance.
- **Neutral factual summaries:** review both submissions for reasoning or later court findings embedded in factual summaries. Keep those findings in legal issues, especially if summaries might later be used for exploratory modeling.

## Provenance and technical cleanup

All Becca records have `prompt_version="unspecified_by_team"` and `annotator_id="GPT-6"`. The model fields also say GPT-6. Confirm the actual prompt/version and distinguish teammate identity from model identity; do not retrospectively assert a version without evidence. Some narrative fields contain the Unicode replacement character. Their evidence quotations pass exact matching, but the narrative encoding should be repaired in a reviewed derivative, preserving the original files.

The supplied three-person comparison script requires exactly three valid inputs. It was not given a duplicated or invented third submission. Instead, [compare_available.py](compare_available.py) performs a transparent two-submission audit and retains validation errors. Run it with Python from any directory to reproduce the JSON and case table. The prose findings in this report are authored interpretations and are not regenerated by that script.

## Suggested next step

At Monday's discussion, agree on the private-property evidence rule, the step-off/trench boundary and the order-versus-motion unit; then correct the mechanical null-label error and record actual team decisions. Request Hyun Sang's independent submission before a three-way comparison. Preserve all original drafts, record any changes in a separate reviewed version, and only mark human review after a person actually checks the evidence. No team consensus or codebook freeze is claimed here.
