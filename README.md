# legal-judgment
NYU Tandon Machine Learning Final Project

# Team 11 — NY case annotation package

Start with **[the teammate README](annotation/README.md)**. This is the data-mining and annotation phase for 506 provisional New York slip/trip-and-fall opinions.

## Where we are

As of October 18, Becca's calibration files are on `main`, and Yinkui's 12-case assistant draft and comparison are in [PR #3](https://github.com/rweng18/legal-judgment/pull/3). Both structured submissions are LLM drafts. They agree on all 12 appellate outcomes, but on include/exclude/review for only 7/12 cases. Hyun Sang's calibration was not found during the latest check. No shared rule freeze or completed human adjudication is claimed.

**If you have not finished your independent calibration, save your own answers before opening anyone else's submission or the comparison report.**

## What we can do next

1. **Finish the independent set.** Hyun Sang can submit the same 12 cases when ready. Yinkui still needs actual human review; the assistant's notes are not human annotations.
2. **Discuss the disagreements together.** After saving independent answers, read the [comparison report](https://github.com/rweng18/legal-judgment/blob/annotations/yinkui-calibration/annotation/submissions/yinkui/comparison/REPORT.md). The main questions are what evidence establishes private premises, how to handle step-off falls, and how to count appealed orders. Review the documented validation/provenance fixes too.
3. **Agree on a shared rule version.** Record actual decisions in [DECISIONS.md](annotation/docs/DECISIONS.md), preserve original drafts, and validate revised copies. Once all three submissions are available and valid, run the three-way comparison.
4. **Try five pilot cases each.** With the rules agreed, use your batch's `SUNDAY_PILOT.md` and cross-review A → B, B → C, C → A. The filename is just a label; this can happen after Monday's discussion. Then decide whether the workflow is ready for the remaining batches.

Monday can focus on these questions and a manageable pace for the remaining work. There is no need to finish every pending item before the meeting.

## Packages and instructions

- [Batch A download](annotation/downloads/batch_A.zip): 169 primary cases.
- [Batch B download](annotation/downloads/batch_B.zip): 169 primary cases.
- [Batch C download](annotation/downloads/batch_C.zip): 168 primary cases.
- [Detailed codebook](annotation/docs/CODEBOOK.md)
- [Weekend timeline](annotation/docs/TIMELINE.md): suggested Saturday/Sunday preparation for our Monday discussion.

The packages contain source texts, assignments, instructions, schemas, and offline validation tools. Teammate calibration answers and previous automated outcome labels are omitted from the batch inputs. Human-reviewed labels and classifier results are still pending.

