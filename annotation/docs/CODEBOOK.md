# Annotation codebook — initial version 1.0.0

## Purpose and source boundary

Annotate New York Appellate Division opinions dated 2010–2024 involving private-property slip/trip-and-fall negligence. Eligibility is being checked again; inclusion in these packets is not a positive label. Use only the supplied controlling opinion and metadata. Ignore substantive conclusions in titles of files or earlier research. Preserve the original source text.

The annotation unit is one appellate decision. The principal outcome concerns the **whole current appellate disposition**, not a citation, trial judgment, or whether the plaintiff ultimately wins damages. Capture granular order outcomes so a future project can revisit the binary boundary without rereading everything.

Passages P001, P002, etc. are artificial divisions of the exact normalized opinion. They are not original paragraphs. A canonical `start`/`end` pair locates each passage; the validator computes quotation offsets. Read across a passage boundary when a sentence or legal discussion continues.

## Eligibility: two separate decisions

`eligibility.scope` describes subject relevance:

- `in_scope`: the injured person slipped/tripped and fell on text-supported private premises and this appeal substantively addresses the negligence claim.
- `out_of_scope`: clear public property, nonfall injury, unrelated dispute, procedural-only decision, or third-party-only issue.
- `uncertain`: insufficient or conflicting facts about those requirements.

`eligibility.binary_task` determines admission to the primary dataset:

- `include`: in scope, enough controlling text, and an unambiguous whole disposition of affirmed/reversed/vacated. Supply evidence for property, incident, merits and outcome. `reasons=[]`; `quality.needs_review=false`.
- `exclude`: a definite scope or disposition exclusion. Supply one or more reason codes; binary label is null. Still annotate facts and outcomes that are stated.
- `review`: unresolved eligibility, text, or outcome issue. Supply reasons and quality flags; binary label is null and `needs_review=true`.

An in-scope case can have a mixed disposition and therefore be excluded from the binary task. This distinction supports a future multiclass extension. Do not force borderline cases into a class to preserve 506 observations.

### Property

Use `private`, `public`, or `unclear`. Describe the basis as `owned`, `leased`, `controlled`, `insufficient`, or `other`, and cite the exact supporting words.

- A defendant-owned house, business interior, private apartment complex, or private parking lot can qualify.
- Private nonprofit and religious premises can qualify; public access to a store or church does not itself mean public ownership.
- A contractor, private operator, or corporate defendant alone does not prove private property. In particular, operating a public facility is not enough.
- A sidewalk adjacent to private property is not automatically private. Public/private boundary uncertainty goes to review. A clearly described private inter-building walkway can qualify when the text supports ownership/control of the accident area.
- A private defendant sued over an expressly municipal site remains outside scope.
- Institutions, loading docks, construction sites, and ambiguous shared spaces require careful reading. Include only when the required private-premises slip/trip negligence claim is established; otherwise review or exclude with a reason.

### Incident and merits

`fall_type`: slip, trip, slip_or_trip, other_fall, nonfall, unclear. Stairs and a trip over an obstruction can qualify. A turkey, ceiling, or door falling onto a person is not a personal slip/trip fall. A ladder/roof fall, bicycle crash, or unrelated workplace accident is not automatically in scope merely because premises liability is mentioned.

`merits`: substantive, procedural_only, third_party_only, mixed_unclear. Summary judgment, substantive dismissal, and a substantive trial/verdict appeal can qualify. Exclude discovery/default/service/venue-only disputes and disputes solely about indemnification between defendants.

An ancillary evidentiary or procedural argument does not automatically exclude an appeal that actually decides the negligence merits. An appeal after **granted reargument** can qualify if it substantively reviews the resulting merits ruling. A decision only refusing permission to reargue does not. If the substantive/procedural boundary cannot be resolved, use review.

The plaintiff need not establish a dangerous condition or negligence for a case to qualify. An affirmed defense judgment for inability to identify the cause of a fall remains a relevant negligence case.

## Outcome and orders

`appellate_disposition` uses: affirmed, reversed, vacated, modified, mixed, appeal_dismissed, remand_only, other, unclear.

| Current whole disposition | Binary label for an included case |
|---|---:|
| Fully affirmed | 0 |
| Fully reversed | 1 |
| Fully vacated | 1 |
| Any other category or unresolved eligibility | null |

- “Affirmed insofar as appealed from” may be 0 when everything actually appealed is affirmed. A reversal of the entire appealed portion may be 1. Do not confuse a limited appeal with a mixed appellate outcome.
- Costs directions do not create a mixed outcome. Consequential remand after full reversal can remain 1.
- A substantive modification, partial affirmance/reversal, or conflicting results among appealed orders is outside the primary binary task.
- Dismissal of the **complaint** may follow affirmation or reversal. Dismissal of the **appeal** is a different outcome.
- One reversed order plus one dismissed appeal in the same decision is mixed for this task.
- Do not use “we would reverse” from a dissent or an outcome in a cited case.
- If a short/fragmentary opinion lacks a usable current disposition, use review instead of inferring from legal reasoning.

List each independently appealed order/judgment under `outcome.orders`. State its appellant role, trial-court action and appellate result, with evidence. Do not count historical orders not independently before the court. If the number is unclear, keep one uncertainty entry, set review, and explain it. `multiple_orders` equals whether the list has more than one entry.

`outcome.favors` records the practical direction **at this appellate stage**, not final liability: plaintiff, defendant, both, unclear, not_applicable. For example, reversal granting defense summary judgment favors defendant; reversal denying defense summary judgment favors plaintiff. This field is an outcome-derived descriptor, never a normal predictive feature.

## Facts and possible extension features

Populate every field in `facts`; use the enums in the schema. Give a short, neutral factual summary (roughly 1–3 sentences) with no invented facts and no appellate outcome. Preserve allegation language where disputed. Every factual group needs supporting evidence references.

| Field | Meaning / rule |
|---|---|
| premises_type | residential, retail, restaurant, office, industrial, religious_nonprofit, recreation, institutional, parking_only, other, unclear. A supermarket parking lot is retail with parking_lot location. |
| location | indoor_floor, stairs, entrance, walkway, parking_lot, sidewalk, road, loading_dock, other, unclear |
| hazards | One or more stated categories: snow_ice, water, grease, debris, uneven_surface, hole, obstruction, wheel_stop, stairs_handrail, lighting, other, unclear |
| injured_role | customer, tenant, employee, contractor, guest, visitor, other, unclear. Do not infer a role solely from the setting. |
| defendant_roles | owner, tenant, manager, contractor, municipality, other, unclear; multiple values allowed |
| accident_date | ISO date only if fully stated; otherwise null. If only month/year is stated, retain that wording in the summary/evidence rather than inventing a day. |
| factual_summary | What happened, where, and what allegedly caused the fall; keep separate from the outcome and legal findings |
| evidence_ids | Exact source support for these values, not citations copied from another opinion |

Do not collect irrelevant personal details or infer demographics. Names already present in public case metadata remain source identifiers, not modeling features. Do not infer injury severity, damages, or socioeconomic status when unstated.

## Legal issues: all 19 topics must be assessed

For each topic below, provide exactly one object in `legal_issues`:

`duty`, `creation_of_hazard`, `actual_notice`, `constructive_notice`, `recurring_condition`, `open_and_obvious`, `trivial_defect`, `storm_in_progress`, `causation_identification`, `assumption_of_risk`, `comparative_fault`, `out_of_possession_landlord`, `contractor_duty`, `code_violation`, `expert_evidence`, `spoliation`, `procedural_issue`, `labor_law`, `other`.

`discussion` is one of:

- `not_discussed`: no substantive discussion in this opinion after reading it fully. Set `finding=""` and `evidence_ids=[]`. A cited case's title or a bare citation does not count.
- `raised_only`: a party raises the issue, but the appellate court does not resolve it. State who argued what.
- `court_addressed`: the court analyzes the issue. State its actual conclusion or that it found a triable issue; do not equate “triable issue” with a final finding of liability.
- `unclear`: the passage does not support a reliable classification. Explain uncertainty and provide evidence if available.

Use a concise finding, not a chain of thought. For constructive notice, distinguish “defendant failed to show lack of notice” from “court conclusively found notice.” Do not convert a burden-of-proof failure into a proven factual finding. Mere discussion is not a positive factual finding. These issue annotations describe post-decision reasoning and can leak outcomes.

## Evidence discussed by the court

`evidence_discussed` describes material discussed in the opinion, not evidence you independently inspected: party_testimony, witness_testimony, photographs, inspection_records, maintenance_records, expert_evidence, weather_records, surveillance, other. List only types actually mentioned in the current case and link supporting quotes. An empty list means none were identified, not that no evidence existed in litigation.

In each description note whether the evidence was submitted, missing, rejected, or considered insufficient when stated. “No inspection records were provided” is not “inspection records established safety.”

## Text sections and outcome cues

For every passage, record one `text_sections` item with its passage ID and one or more types: facts, procedural_history, legal_reasoning, current_outcome, quoted_precedent, metadata, separate_opinion, unclear. Passages often contain more than one type. Do not omit passages that contain headings or citations.

`outcome_cues` records exact evidence for current_disposition, repeated_outcome and indirect_reasoning. Mark direct outcome statements separately from reasoning that only suggests an outcome. These annotations support a masking audit. They **must not be used to hand-edit test documents using gold labels**. Any later masking algorithm must be developed on training text and frozen before evaluation.

Factual summaries are still reconstructed from post-decision opinions; they do not create a genuine prospective prediction dataset.

## Evidence objects and missing information

Assign local IDs E001, E002, etc. Each evidence object has:

- `evidence_id`: unique within this case.
- `passage_id`: an existing source passage.
- `quote`: exact continuous source text occurring once within that passage; use a long enough quote to avoid ambiguity. Do not fix OCR, substitute punctuation, insert ellipses or cross a passage boundary. Use two evidence objects if necessary.
- `statement_status`: allegation, party_argument, testimony_or_record, court_finding, procedural_history, current_disposition, unclear.

Reuse an evidence ID for several fields when the same quotation supports them. Quoted legal precedent cannot establish facts of this case. A quotation can be genuine but irrelevant: humans must still check its meaning. Validators compute offsets in a separate report; do not add unrecognized fields to the annotation object.

Unknown/not stated is distinct from false/not present. Use explicit unclear/null enums as appropriate. If full text could not be read, mark review/text_problem; do not mark every legal issue not_discussed from an incomplete read.

## Provenance and review status

Copy case_id/text_sha256/input_chunk_id from the input. Use schema_version 1.0.0 and the exact prompt_version agreed by the team. Record annotator ID, model name, observed version if known (otherwise null), and annotation time with timezone. A human reviewer ID is null on an LLM draft.

Only actual human review justifies human_reviewed. This status requires independent eligibility/outcome checking and checking the factual/issue evidence in the submitted record; it cannot mean merely running the validator. `adjudicated` means a human resolved a disagreement and documented why. Never promote automatically. Preserve drafts and use `supersedes` to identify an earlier filename/record version when replacing it.

Set needs_review=true for unresolved material uncertainty. Quality flags are not an eligibility decision by themselves; an included case cannot simultaneously require unresolved eligibility/outcome review. Describe minor formatting concerns as notes if they do not affect the decision.

## Feature-use boundaries

Metadata, facts, legal reasoning, outcomes and annotation provenance stay separate. For the current project, planned classifiers use the preprocessed opinion text only. Outcome, favors, court findings, evidence selected because of the outcome, and outcome-cue annotations are diagnostic/target information. Never concatenate the annotation JSON into model inputs. Extra features may support later studies only after their temporal availability and leakage risks are reviewed.

## Calibration edge examples (hypothetical, not corpus labels)

1. A customer trips on a wheel stop in an expressly private supermarket lot; summary judgment dismissal affirmed: in_scope/include/0, even though no negligence was found.
2. A private maintenance company is sued over a municipal subway fall: out_of_scope/exclude, public_property, null binary label.
3. A private apartment fall has one appealed order reversed and a separate appeal dismissed: in_scope/exclude, mixed_outcome, null binary label.
4. A box falls onto a customer's foot: nonfall/exclude, even if “premises liability” appears repeatedly.
5. A defendant operates a pool, but the property status is not established: uncertain/review/property_unclear.
6. Reargument was granted and the resulting negligence judgment is substantively affirmed: may qualify. A refusal to grant reargument alone does not.

