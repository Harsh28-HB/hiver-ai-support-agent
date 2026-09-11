# Golden Evaluation Sampling Plan

The golden split contains 4,761 conversations in the current processed artifact. It was not used to discover, tune, or name intents.

Sample approximately 200 complete conversations for human annotation:

- Draw 160 conversations with a deterministic seed from the golden split, stratified only by observable structure: conversation length (2, 3, 4, and 5+ messages), whether the first customer message has a linked brand reply, and customer-message length bands.
- Reserve 40 additional conversations for coverage of rare/ambiguous cases identified by annotators during the first pass. Selection must be blind to any automatically inferred intent.
- Keep every message in a selected conversation together. Annotators should label the first customer request using the approved taxonomy, mark multi-intent and ambiguous cases, and record the first historically appropriate brand response separately.
- Deduplicate near-identical customer text within the golden sample using normalized exact text before annotation; replace excluded rows with another deterministic draw.
- Store labels and annotator notes under `data/golden/`; do not feed those labels back into taxonomy discovery.

This plan creates a human-reviewed evaluation set without allowing golden examples to shape the taxonomy.
