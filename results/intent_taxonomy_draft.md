# Draft AmazonHelp Intent Taxonomy

This exploratory taxonomy was derived only from conversations in the `knowledge` split. The golden split was counted for planning but never read for terms, examples, or taxonomy decisions.

Knowledge conversations analyzed: 37,719
Knowledge customer messages analyzed: 85,315

## Intents
### delivery_late_or_missing
- Definition: The order or package is late, missing, not received, or has an unresolved delivery date.
- Approximate frequency: 11,515 customer messages (13.50% of knowledge customer messages)
- Closest/confusing intent: `order_tracking_or_status`
- Representative examples:
  - @AmazonHelp It had been said that the package would be delivered by Nov 9th. Then the package got delayed and it was said to be delivered by Nov 11th 8 pm. Now that it's late it says the package is «Out for delivery  On its way to CHICAGO, IL, US». Has been like that since 9 am.
  - @AmazonHelp Latest update on furniture is delivery date pushed out again and no indication of when it will be delivered.   Other item to be delivered today &amp; delayed, now told they need other instructions to complete delivery which is funny bc I've had three other things delivered today.
  - @AmazonHelp Hi. I had notification of shipment for 2 packages on Tuesday. Later that day one was shown as delivered, it wasn't. Then received updates of "out for delivery" or "delayed" and various combinations thereof for both packages on both Wednesday, and Thursday. Today, another "on way"

### order_tracking_or_status
- Definition: The customer asks where an order is, whether it shipped, or how to track its current status.
- Approximate frequency: 4,632 customer messages (5.43% of knowledge customer messages)
- Closest/confusing intent: `delivery_late_or_missing`
- Representative examples:
  - @AmazonHelp I can't even imagine how brainless Bimbo you guys are if they are shipped as per delivery date how the hell was the order whose delivery date is farther than the previous Order got dispatched earlier but the previous Order is not dispatched yet
  - @AmazonHelp Preordered #FIFA18. Order wasn't delivered . Ordered it again and it got delivered before the pre order was even dispatched! https://t.co/QjLUzAfYeo
  - @AmazonHelp So far I have been told issue is solved and order ready to dispatch, that my order has been cancelled (at my request) and lastly via email that order is on way and there will be no further delay..... app still shows order in red and needing payment details again!

### refund_return_or_cancellation
- Definition: The customer requests a refund, return, cancellation, reimbursement, or money-back action.
- Approximate frequency: 5,382 customer messages (6.31% of knowledge customer messages)
- Closest/confusing intent: `item_wrong_damaged_or_missing`
- Representative examples:
  - @AmazonHelp how much more i have to wait refund my money and you guys carry on your investigation and even do complaint with the authorities but please refund my money today, i dont have any smartphone of my own so i have to buy a phone so please refund my money.
  - @AmazonHelp ORDER # 408-7866006-8411522 was cancelled by Amazon immediately after registering it. It was informed to me repeatedly by SMS. I was assured that my money will be refunded. Today, I received this SMS that it is under despatch. I do not need it. Please refund my money. https://t.co/JhES7zBUlA
  - @AmazonHelp I am missing 2 refunds out of 6 items I returned, I used the other 4 refunds on other items already and waiting for the last 2 to be refunded. he stated I already used the last 2 when it obviously has not been refunded, I have all transactions on my account still and saved

### prime_membership_or_benefits
- Definition: The message concerns Prime membership, Prime delivery benefits, trials, renewal, or membership charges.
- Approximate frequency: 2,867 customer messages (3.36% of knowledge customer messages)
- Closest/confusing intent: `payment_or_card_charge`
- Representative examples:
  - @AmazonHelp It's OK, I've found the way to cancel the Prime free trial on the Amazon.de, seems the Prime yearly membership on Amazon.fr is still OK. Could be nice to have only 1 Prime membership for all Europe and not one by country :(
  - @AmazonHelp OnePlus 5t is available only for prime customers. It also has an offer on prime video (INR 250 Amazon Pay balance). However this offer is available only on signing up for prime via the prime video app. But I'm already a prime subscriber. So how does it work for me?
  - @AmazonHelp My prime membership is due for renewal on Nov 3rd.. also the prime membership charge is just 499... Then why 719 has been charged...

### account_email_or_login
- Definition: The customer cannot access, update, verify, or receive messages for an Amazon account or email.
- Approximate frequency: 3,012 customer messages (3.53% of knowledge customer messages)
- Closest/confusing intent: `website_app_or_technical_issue`
- Representative examples:
  - @AmazonHelp I know how it happened, someone used the wrong email for their account &amp; because Amazon does NOT have any email verification process, this person inadvertently gave me access to their account. Not email provider's fault, AMAZON's fault. This wouldn't happen w/email verification. https://t.co/4EOurezBTE
  - @AmazonHelp I have palced order from account where login id is my mobile no.  Though i have seperate account having my emaild as login. Still you can use the email to communicate but not to current order details. To check my current order use phone no as Login I'd. Thanks
  - @AmazonHelp Got an email stating that the email associated with the account has been changed, even though I did not change it and now I no longer have access to that account. I called three different service reps, one said my account was safe and the others said they would just email a form

### payment_or_card_charge
- Definition: The message concerns a payment, charge, credit/debit card, billing, or an unexpected transaction.
- Approximate frequency: 1,371 customer messages (1.61% of knowledge customer messages)
- Closest/confusing intent: `prime_membership_or_benefits`
- Representative examples:
  - @AmazonHelp well I more meant an actual card. Not a credit card or gift card from amazon themselves. Like if I live in UK with a uk debit card or something can I purchase stuff off the US amazon store.
  - @AmazonHelp Thanks for repling, I recently looked at my credit card bills and I have been seen that there is a charge on there that I was not aware of. I would like to have charges back to that credit card. Please.
  - @AmazonHelp Instead of automatically charging someone's card, setup a system that text's that person's card and/or bank (so the bank can send the card holder a text in Amazon's stead) to ask permission to CHARGE the card - instead of the surprise hit.

### gift_card_or_promotion
- Definition: The customer reports a gift card, promotional code, voucher, balance, or redemption problem.
- Approximate frequency: 596 customer messages (0.70% of knowledge customer messages)
- Closest/confusing intent: `payment_or_card_charge`
- Representative examples:
  - @AmazonHelp Product page had promotion details but promotion would not apply to purchase.
  - @AmazonHelp We are unable to validate the Gift card / Voucher code you have entered. Please recheck the Gift card / Voucher code before trying to add it
  - @AmazonHelp "We are unable to validate the Gift card / Voucher code you have entered. Please recheck the Gift card / Voucher code before trying to add it again in your account."  By the way, this happened to my four different codes. What can be the problem

### item_wrong_damaged_or_missing
- Definition: The delivered item is wrong, damaged, defective, incomplete, or materially different from the order.
- Approximate frequency: 621 customer messages (0.73% of knowledge customer messages)
- Closest/confusing intent: `delivery_late_or_missing`
- Representative examples:
  - @AmazonHelp Same mechanical approach. Absolutely bizzare! Order placed on 18 Nov. with next day delivery charge, received defective product on 19Nov, defective product picked up on 20 Nov, defective product reached your warehouse on 23 Nov. Expected delivery on 30 Nov. Brilliant!
  - @AmazonHelp Oh so you are saying unless the order is defective or damaged what about your technican report who confirmed it is defective
  - @AmazonHelp Finally received the defected and broken product with totally broken outer box. Refund requested. Mail already sent.

### customer_service_contact_or_escalation
- Definition: The customer reports poor support, requests a human/contact route, or asks why support has not resolved the issue.
- Approximate frequency: 9,962 customer messages (11.68% of knowledge customer messages)
- Closest/confusing intent: `all operational intents`
- Representative examples:
  - @AmazonHelp I have already contacted ur customer support many times in past 3 days, still my order is not delivered yet, neither courier service is contacting me nor I can contact them, everytime I get the same mail from customer service that they have contacted courier, but still not (1/2)
  - @AmazonHelp I am providing order details n DM not twitter page. Are you new to twitter.When Amazon having social customer support handle i.e Twitter. Why customer need to contact customer support. It is very bad service as compared to flipkart. Now Amazon day by day service quality is bad.
  - @AmazonHelp In app I go 2-&gt;Customer Service-&gt;Contact us-&gt;Call Customer Service-&gt;Return &amp; Refunds-&gt;Call us now Then on a call it says unable 2 find order

### website_app_or_technical_issue
- Definition: The customer reports an Amazon site, app, link, checkout, or other technical failure.
- Approximate frequency: 7,071 customer messages (8.29% of knowledge customer messages)
- Closest/confusing intent: `account_email_or_login`
- Representative examples:
  - @AmazonHelp Okay I understand. But who won #motoG5Splus #MotoAppQuiz #AppDanceQuiz #MicromaxAppQuiz #GalaxyNote8AppQuiz  #Iphone8AppQuiz 🙏
  - @AmazonHelp Ur system is sucking. I pressed add to cart button at 12, it didn't happen then again add to cart option appeared when 32% was booked, again it didn't happened then again add to cart appeared when booking was 78% and again I pressed that but it didn't happen. Pathetic. Disgusting
  - @AmazonHelp During checkout, the app automatically assigns 2-day shipping. Any attempt to alter shipping by opening the shipping box (when you know you get free shipping) causes the app to go back two pages. There is no way to escape the loop.

## Ambiguity
Messages matching two or more exploratory themes: 13,302
Messages matching no exploratory theme: 38,286
These are review queues, not automatically assigned labels.

## TF-IDF signals
amazon (17110.6), order (14124.6), que (13933.8), delivery (13889.9), now (12663.2), email (11109.9), time (10427.4), prime (10171.4), customer (10146.9), today (10036.3), it's (9798.3), service (9578.1), delivered (9307.9), day (8918.6), already (8704.5), call (8483.8), days (8318.5), had (8123.4), yes (8050.6), any (7998.4), refund (7967.9), account (7738.3), got (7616.0), don't (7580.3), product (7549.9), again (7539.8), back (7502.2), same (7346.7), said (7286.8), says (7258.7), want (7236.1), issue (7189.4), i'm (7063.5), amp (7053.4), know (7028.3), item (6885.5), need (6781.7), did (6701.4), received (6649.5), only (6616.1)

The themes are lightweight, evidence-based grouping anchors for manual review, not a classifier or final label set.