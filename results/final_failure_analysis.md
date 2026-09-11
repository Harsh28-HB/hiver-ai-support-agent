# Final AmazonHelp Failure Analysis

## Scope and evidence

The final evaluation used 196 labelled examples from the 200-row Golden file. Four examples were skipped and excluded. No Golden examples were used for training or retrieval.

- Duplicate conversation IDs: `0`
- Split leakage: `0`
- LLM judge: unavailable because `OPENAI_API_KEY` was not configured
- Balanced agent accuracy: `0.096939`
- Balanced agent macro F1: `0.121689`
- Balanced agent escalation accuracy: `0.392857`

The five patterns below combine the final balanced confusion matrix with real Golden messages and saved Knowledge-only retrieval evidence. Where a message comes from the saved per-example response artifact, it is identified as such; no new inference was run.

## 1. Residual collapse into `other_or_unclear`

The balanced confusion matrix still sends many concrete intents to `other_or_unclear`:

- Refund/return/cancellation: `38`
- Prime membership/benefits: `19`
- Account/email/login: `19`
- Delivery tracking: `12`
- Payment/card: `10`

This explains the very low `other_or_unclear` F1 of `0.034483` and shows that balancing did not solve coverage or label-boundary problems.

Real Golden examples from the saved per-example evaluation evidence:

1. Conversation `105219`, gold `delivery_tracking`: “@AmazonHelp They keep sending me the same auto email. On the phone they say they'll get back to me, auto email. Been round and round for days. Just want a real update on the situation. Can you help?”
2. Conversation `1065652`, gold `refund_return_or_cancellation`: “@AmazonHelp I have checked the info and contacted customer care many times but no help is being provided.”

**Diagnosis:** short, indirect, and escalation-oriented messages have weak lexical anchors for the nine-way taxonomy.

## 2. Delivery language dominates unrelated operational issues

The balanced confusion matrix predicts `delivery_delay` for many other intents:

- Refund/return/cancellation -> delivery delay: `9`
- Account/email/login -> delivery delay: `7`
- Prime membership/benefits -> delivery delay: `5`
- Payment/card -> delivery delay: `5`
- Delivery tracking -> delivery delay: `4`

Real Golden examples:

1. Conversation `1843523`, gold `delivery_delay`: “@AmazonHelp I was issued a refund on 17th for a lost trade in and then it dissapered from my account and no one can tell me why and they stopped replying to me misse all black friday deals and ill miss cyber monday as well”
2. Conversation `390784`, gold `refund_return_or_cancellation` in the saved per-example artifact: “@AmazonHelp Yes, and it's a 3 day delivery instead of 2 days. I am a prime member and expect prime shipping.”

**Diagnosis:** order and delivery vocabulary is common across returns, refunds, Prime, and payment complaints, so TF-IDF similarity overweights shared commerce terms.

## 3. Account/email/login remains completely unrecognized

The balanced classifier's account/email/login F1 is `0.0`. Its confusion row contains only false predictions, including `7` delivery-delay predictions, `2` tracking predictions, `3` refund predictions, and `19` other/unclear predictions.

Real Golden examples:

1. Conversation `1719215`, gold `delivery_tracking` in the saved per-example artifact: “@AmazonHelp It’s been over 48 hours my account has been on hold. Still no email from your team!! How patient do you want me to be.”
2. Conversation `2269126`, gold `account_email_or_login` in the saved per-example artifact: “@AmazonHelp Other than the dispatch confirmation and delivery which had mysteriously changed - no”

**Diagnosis:** account issues are often expressed through missing emails, holds, or order context rather than explicit “login” or “account” language. The taxonomy label is semantically valid but not lexically separable with the existing model.

## 4. Retrieval can select generic or unrelated evidence

The saved response-evaluation evidence shows raw TF-IDF retrieval returning weak matches even when three results are available.

Real Golden examples:

1. Conversation `718348`: “@AmazonHelp I was looking at the deals page and clicked on an item. Once I saw I liked it, I clicked the one-click order button. Then saw I was charged $20 more than the page said. I went back to the page and took a screen shot of correct price ($20 less than I was charged). 50 mins on chat.” The top retrieved customer message was “@AmazonHelp Not really, lost my voice otherwise that would be an option.” with similarity `0.1675`.
2. Conversation `656083`: “@AmazonHelp Thx for reaching out. I didnt, but started the refund process. It's a hassle to bring this heavy #persil to ups. Timing isnt gonna work out now, I'll reorder after holidays...” The top retrieved customer message was “@AmazonHelp Thx” with similarity `0.1894`.

**Diagnosis:** lexical cosine similarity is not sufficient for issue-level relevance; generic short messages can become retrieval neighbors.

## 5. Escalation remains poorly calibrated and replies inherit retrieval errors

Balanced agent escalation accuracy is only `0.392857`. The final evaluation does not include a newly generated response-quality score because the LLM judge was unavailable. The saved response evidence nevertheless shows that the current reply path directly returns the top historical response for auto-handled cases, so a bad retrieval can produce an irrelevant answer.

Real Golden examples:

1. Conversation `111811`: “@AmazonHelp The order was placed on the wrong card. Initially I just wanted to change the card... I tried to cancel the order... forced to pay $31.00 and have my bank stop payment.” The saved response was an expedited-shipping answer: “I'm sorry for any troubles with this order! Not all items are eligible for expedited shipping...”
2. Conversation `1016385`: “@AmazonHelp Phoned amazon &amp; ive been refunded, parcel is 3 days late, promised next day with prime...” The saved agent decision escalated because similarity was `0.1522`, despite the intent being predicted correctly in that saved artifact.

**Diagnosis:** fixed confidence/similarity gates and direct top-response copying do not distinguish “low evidence but understandable request” from “unsafe to answer.”

## Headline metric warning

Accuracy should not be interpreted alone:

- Majority accuracy: `0.015306`; macro F1: `0.003350`.
- Original TF-IDF accuracy: `0.081633`; macro F1: `0.105836`.
- Balanced agent accuracy: `0.096939`; macro F1: `0.121689`.

The balanced agent's accuracy is only about `9.7%`, and macro F1 is only `0.122`. The gap between accuracy and macro F1 reflects uneven intent behavior. Most importantly, account/email/login has F1 `0.0`, while minority and ambiguous classes remain weak. A single accuracy number can obscure complete failure on an intent and the large residual confusion into `other_or_unclear`.

Escalation is also a separate safety outcome: `0.392857` accuracy means the intent improvement did not translate into reliable handling decisions. Response quality has no LLM-judge score and must be treated as unmeasured, not as successful.

## Conclusion

The balanced classifier is better than the original TF-IDF baseline on the measured intent metrics, but it is not a reliable support agent yet. The main remaining risks are semantic coverage of indirect messages, delivery-vocabulary dominance, generic retrieval neighbors, and escalation calibration. No model, taxonomy, Golden labels, or agent code was modified during this diagnosis.
