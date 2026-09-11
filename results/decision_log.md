# Engineering Decision Log

This log records decisions made in the foundation phase. Dataset-dependent decisions remain provisional until the raw export is inspected.

1. Use the Customer Support on Twitter export as the only primary dataset; Banking77 is out of scope.
2. Keep raw data untouched and ignore raw/generated records by default in version control.
3. Derive paths from the repository root so commands do not depend on a developer's machine.
4. Inspect headers and sampled values before assigning semantic roles to columns.
5. Use chunked reads for row counts, missingness, and duplicate counts to reduce memory pressure.
6. Treat absent or ambiguous brand fields as a blocked selection, not an invitation to hard-code a brand.
7. Rank brands with an explicit weighted score that rewards volume, customer coverage, linkage, thread evidence, and issue diversity.
8. Make brand analysis report its measurement basis when calculated from a bounded sample.
9. Reconstruct conversations only when stable relationship, text, and identity fields are available.
10. Require evidence for both customer and brand speakers before calling a thread usable.
11. Preserve chronological order when timestamps are parseable and retain unknown timestamps rather than inventing order.
12. Store message sequences as JSON inside the processed table so later evaluation can prevent future-response leakage.
13. Use deterministic configuration defaults, including random seed 42 for future sampling.
14. Defer intents, retrieval, generation, escalation, golden labels, baselines, and LLM judging until data quality is measured.
15. Report unavailable values explicitly and never fabricate schema, brand, or performance statistics.
16. Discover the draft intent taxonomy from the knowledge split only; golden conversations are reserved for independent human evaluation.
17. Use strongest-evidence thematic assignment for exploratory frequencies because delivery, tracking, returns, and support-escalation language overlaps.
18. Keep `other_or_unclear` and multi-intent queues visible rather than forcing multilingual, noisy, or underspecified messages into a false intent.
19. Treat TF-IDF terms and response regex signals as review aids, not as a production classifier or final label source.
20. Recommend golden sampling by observable structure and blind annotation, without automatically applying the exploratory taxonomy to golden messages.
21. The original TF-IDF baseline was evaluated on 196 labelled Golden examples: accuracy 0.081633 and macro F1 0.105836.
22. A deterministic balanced Knowledge artifact capped dominant classes at 6,000 examples, retained 26,781 Knowledge rows across all nine intents, and had zero Golden conversation overlap.
23. The balanced classifier improved measured accuracy to 0.096939 and macro F1 to 0.121689, but account/email/login remained at F1 0.0 and escalation accuracy was 0.392857.
24. Final evaluation excluded four skipped Golden rows; metrics were not presented as 200-example metrics.
25. Final retrieval/response quality was not scored by an LLM judge because `OPENAI_API_KEY` was unavailable; this remains unmeasured rather than assumed successful.
26. The headline accuracy is insufficient for acceptance because macro F1, per-intent F1, confusion matrices, and escalation accuracy expose severe minority-intent and decision-quality failures.
