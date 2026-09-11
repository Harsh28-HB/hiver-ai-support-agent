# Data Quality Report

- Raw records observed: 2,811,774
- Duplicate records observed: 0
- Input files inspected: 1
- Selected brand: AmazonHelp
- Selected-brand processed records: 276,678
- Usable conversation threads reconstructed: 47,204
- Multi-turn conversations (>2 messages): 38,374
- Customer messages in usable conversations: 106,791
- Brand messages in usable conversations: 120,668
- Average conversation length: 4.82
- Median conversation length: 3.00
- Empty text records removed: 0
- Conversation-level split counts: {'knowledge': 37719, 'golden': 4761, 'validation': 4724}
- Conversation reconstruction note: explicit tweet IDs and parent/response relationships; components require both speakers

Filtering decisions: duplicate tweet IDs are collapsed; empty text is excluded; only explicit tweet-ID parent/response components containing both customer and selected-brand messages are retained. Future messages remain in their chronological conversation, but later evaluation must truncate inputs before the target brand response. The deterministic knowledge/validation/golden assignment is at conversation level, so no conversation is split across partitions.
