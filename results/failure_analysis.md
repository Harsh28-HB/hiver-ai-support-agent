# AmazonHelp Agent Failure Analysis

## Evaluation scope

Analysis uses the saved per-example results for 196 human-labelled golden examples. The four skipped golden rows were excluded. The agent trained and retrieved only from Knowledge data.

- Duplicate golden conversation IDs: 0
- Conversation split leakage: 0
- Agent intent accuracy: 0.081633
- Agent intent macro F1: 0.105836
- Agent escalation accuracy: 0.408163
- LLM judge: unavailable because `OPENAI_API_KEY` is not configured

The agent's intent metrics exactly match the TF-IDF baseline because the agent reuses the same Knowledge-trained classifier. The agent's additional behavior is retrieval, reply selection, and escalation.

## Per-intent evidence

Agent per-intent F1:

| Intent | F1 |
|---|---:|
| delivery_delay | 0.102564 |
| delivery_tracking | 0.125000 |
| refund_return_or_cancellation | 0.089552 |
| prime_membership_or_benefits | 0.157895 |
| account_email_or_login | 0.000000 |
| payment_or_card_charge | 0.153846 |
| gift_card_or_promotion | 0.125000 |
| website_app_or_technical_issue | 0.166667 |
| other_or_unclear | 0.032000 |

The confusion matrix shows the dominant error direction: 122 of 196 examples were predicted as `other_or_unclear`, while only 3 golden examples had that intent. The largest individual confusions were:

- `refund_return_or_cancellation` -> `other_or_unclear`: 38
- `prime_membership_or_benefits` -> `other_or_unclear`: 22
- `account_email_or_login` -> `other_or_unclear`: 19
- `delivery_tracking` -> `other_or_unclear`: 16
- `payment_or_card_charge` -> `other_or_unclear`: 12

## Top five failure patterns

### 1. Weak Knowledge labels collapse the classifier into `other_or_unclear`

The Knowledge training file contains 85,315 weak-rule labels. `other_or_unclear` accounts for 55,700 rows, or 65.30%. The trained classifier therefore learns a severe class prior that is inconsistent with the golden distribution: 122/196 predictions were `other_or_unclear`, versus 3/196 golden labels.

Real examples:

1. **Conversation 105219**
   - Gold: `delivery_tracking`
   - Predicted: `other_or_unclear`
   - Customer: “@AmazonHelp They keep sending me the same auto email. On the phone they say they'll get back to me, auto email. Been round and round for days. Just want a real update on the situation. Can you help?”

2. **Conversation 1065652**
   - Gold: `refund_return_or_cancellation`
   - Predicted: `other_or_unclear`
   - Customer: “@AmazonHelp I have checked the info and contacted customer care many times but no help is being provided.”

**One concrete fix:** Replace broad weak-rule labels with a manually reviewed, stratified Knowledge training subset, especially for `other_or_unclear` and minority intents, before retraining.

### 2. Overlapping operational intents are not separated reliably

Delivery delay, tracking, refund, payment, and account messages share words such as “order,” “delivery,” “email,” “charge,” and “cancel.” The current single-label TF-IDF model has no explicit hierarchy or multi-intent handling. This produces errors such as refund/payment and delivery/tracking swaps.

Real examples:

1. **Conversation 111811**
   - Gold: `refund_return_or_cancellation`
   - Predicted: `payment_or_card_charge`
   - Customer: “@AmazonHelp The order was placed on the wrong card. Initially I just wanted to change the card. When I was told that was impossible I tried to cancel the order. When that was impossible I was forced to pay $31.00 and have my bank stop payment.”

2. **Conversation 1843523**
   - Gold: `delivery_delay`
   - Predicted: `refund_return_or_cancellation`
   - Customer: “@AmazonHelp I was issued a refund on 17th for a lost trade in and then it dissapered from my account and no one can tell me why and they stopped replying to me misse all black friday deals and ill miss cyber monday as well”

**One concrete fix:** Add a manually reviewed multi-intent/primary-intent training layer with explicit precedence rules for operational entities, rather than relying on unigram/bigram TF-IDF alone.

### 3. Retrieval returns semantically unrelated Knowledge conversations

The retrieval index uses one TF-IDF document per Knowledge conversation and returns the top lexical cosine matches without intent-conditioned reranking. This can produce low-overlap or generic matches even when the similarity score appears usable.

Real examples:

1. **Conversation 718348**
   - Gold: `delivery_tracking`
   - Predicted: `website_app_or_technical_issue`
   - Similarity: `0.1675`
   - Customer: “@AmazonHelp I was looking at the deals page and clicked on an item. Once I saw I liked it, I clicked the one-click order button. Then saw I was charged $20 more than the page said. I went back to the page and took a screen shot of correct price ($20 less than I was charged). 50 mins on chat.”
   - Top retrieved customer message: “@AmazonHelp Not really, lost my voice otherwise that would be an option.”

2. **Conversation 656083**
   - Gold: `account_email_or_login`
   - Predicted: `refund_return_or_cancellation`
   - Similarity: `0.1894`
   - Customer: “@AmazonHelp Thx for reaching out. I didnt, but started the refund process. It's a hassle to bring this heavy #persil to ups. Timing isnt gonna work out now, I'll reorder after holidays (hope prices won't change). Hopefully your team wont ask me how come there is only one item in the package”
   - Top retrieved customer message: “@AmazonHelp Thx”

**One concrete fix:** Rerank candidate conversations with an intent-conditioned relevance model and reject evidence below a calibrated similarity/relevance threshold instead of treating the raw top-3 TF-IDF results as equally useful.

### 4. Escalation thresholds produce massive false escalations

Escalation accuracy is 0.408163. The error matrix is:

- Gold `AUTO-HANDLE`, predicted `ESCALATE`: 108
- Gold `AUTO-HANDLE`, predicted `AUTO-HANDLE`: 34
- Gold `ESCALATE`, predicted `ESCALATE`: 46
- Gold `ESCALATE`, predicted `AUTO-HANDLE`: 8

Thus the current policy is conservative in the wrong way: it escalates 108 cases that annotators considered auto-handleable. There were 32/196 cases with best retrieval similarity below 0.20; the fixed threshold rejects many otherwise correct intent predictions.

Real examples:

1. **Conversation 1016385**
   - Gold decision: `AUTO-HANDLE`
   - Predicted: `ESCALATE`
   - Intent was correct: `delivery_delay`
   - Confidence: `0.6156`; best similarity: `0.1522`
   - Customer: “@AmazonHelp Phoned amazon &amp; ive been refunded, parcel is 3 days late, promised next day with prime. Very stressful, been told might be here tomorrow.”

2. **Conversation 2910317**
   - Gold decision: `AUTO-HANDLE`
   - Predicted: `ESCALATE`
   - Intent was correct: `refund_return_or_cancellation`
   - Confidence: `0.9989`; best similarity: `0.1494`
   - Customer: “@AmazonHelp I bought a product off you and then cancelled as found cheaper. You still delivered and tried to charge me returns. Your advisor said they would advance refund so I could return and still buy product elsewhere. Refund never came and now I’m out of pocket as deal elsewhere has end”

**One concrete fix:** Calibrate the escalation thresholds on a separately human-labelled validation set, using intent confidence and evidence quality jointly instead of the fixed 0.60/0.20 gates.

### 5. Reply generation copies the top response without checking answer compatibility

The local agent does not generate a new grounded answer or compare the response against the input. For auto-handled cases it directly cleans and returns the top retrieved historical response. When retrieval is wrong, the reply can answer a different issue while still sounding plausible.

Real examples:

1. **Conversation 111811**
   - Gold intent: `refund_return_or_cancellation`
   - Predicted intent: `payment_or_card_charge`
   - Decision: `AUTO-HANDLE` despite gold `ESCALATE`
   - Customer asks about a wrong card, cancellation, and forced payment.
   - Returned reply: “I'm sorry for any troubles with this order! Not all items are eligible for expedited shipping. You will see the availability through check out. Also, just to clarify, have you received an e-mail regarding this order? ^AL”
   - This response is about expedited shipping and email, not the customer's payment/cancellation problem.

2. **Conversation 718348**
   - Gold intent: `delivery_tracking`
   - Predicted intent: `website_app_or_technical_issue`
   - Customer reports a $20 price discrepancy after one-click ordering.
   - Top retrieved message: “@AmazonHelp Not really, lost my voice otherwise that would be an option.”
   - Returned reply: “I’m sorry, but I need a support specialist to review this request.”
   - The reply is generic escalation and contains no useful response grounded in the price discrepancy.

**One concrete fix:** Generate or select replies only after a response-specific entailment/relevance check confirms that the historical response addresses the predicted intent and customer issue; otherwise escalate with the mismatch reason.

## Overall diagnosis

The agent is not outperforming TF-IDF because its intent component is exactly the same TF-IDF Logistic Regression model, trained on noisy weak labels. Retrieval is an independent TF-IDF index with no intent-aware reranking, and reply generation is direct copying of the top historical response. The most important root cause is training-label quality: the weak-label process assigns 65.30% of Knowledge messages to `other_or_unclear`, which explains the collapse in the confusion matrix and the low per-intent F1.

No fixes were implemented in this diagnosis.
