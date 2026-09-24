# TypeSafe docs digest (agent report, 2026-09-24)

> Synthesized from the 111-page archive in `typesafe-docs/`. Sections: A use cases, B every example question, C cookbook datasets, D question-design guidance, E facts beyond the basics.

## TypeSafe docs archive: report

**Archive location:** `/Users/junzhang/Projects/askjev/resources/references/typesafe-docs/`

I downloaded all 111 pages listed in `llms.txt` with curl (`<path>.md`). Every download returned HTTP 200 and is saved byte-for-byte, with the folder layout matching the site's URL paths. I also saved `llms.txt` and `llms-full.txt` (910 KB, the site's all-pages dump). `README.md` has the fetch date (2026-09-24), a one-line description of every file, and groups them by section. I checked every internal link inside the pages, and each one points to a file in the archive. The legal page's only outbound links are to typesafe.ai/legal/*, which is the marketing site, so I did not archive those. Nothing was written outside the folder; the stripped reading copies are in the scratchpad.

I read every non-reference page in full, and skimmed the SDK reference pages for limits and defaults.

---

## A. Use cases, industries and decision shapes

**Five category cards on `concepts/use-case-map.md`:**
- AI Automation Software: "run it a million times in the background without a human co-pilot. Code owns control flow (not markdown files)".
- Real-time applications: "150ms", "faster than human perception… play games or embedded into a UI".
- AI Map Reduce over Big Data: "100x cheaper… classify giant agent traces".
- Universal Verification: check the input prompt, extractions, reasoning traces, tool calls, or other AIs' inputs; catch jailbreaks, citation errors and hallucinations.
- Harness Engineering: model routing, semantic context retrieval, LLM error detection and guardrails, reasoning-trace classification.

**Industries and bullets** (the list you gave is complete). Sub-items worth noting:
- Search/retrieval: "Rerank results with **pairwise comparisons**", "Cross-encode queries and candidates", replace or supplement embeddings.
- Scientific discovery: systematic-review inclusion/exclusion screening, thematic coding of interviews and surveys, citation-supports-claim checks, flagging missing methods details, knowledge graphs across papers.
- Model routing: difficulty and risk estimation, escalating to a more expensive model.
- Guardrails: jailbreak and prompt-injection detection, policy violations, sensitive-data exposure, tool-call errors, logging check probabilities.
- Semantic code linting: team conventions and writing guidelines, run in CI.
- Feature extraction: probabilistic features plus structured data, autoresearch.
- Recruiting: resumes and interview feedback against job criteria, competency evidence, matching, routing, escalation.
- Lead gen: ICP match, industry fit and company maturity, buyer relevance, pain points, purchase intent.
- Support: call-transcript commitments and follow-ups, churn risk, refund requests, checking responses against policy.
- Insurance claims: first-notice-of-loss (FNOL) reports and adjuster notes, complexity, missing info, fraud indicators, straight-through processing vs specialist.
- Financial crime: transaction narratives, KYC, alert histories, entity matching across inconsistent names.
- Legal/compliance: contracts, policies, filings, marketing claims, missing clauses, prohibited claims.
- E-commerce: listing normalization, attribute extraction, prohibited or counterfeit listings, review abuse.
- Moderation/T&S: company-specific criteria, SDR workflows, opt-out requests, unsafe advice, "combine severity and confidence to allow, warn, review, or block".
- Advertising: brand safety, audience suitability, prohibited claims, ad-to-landing-page alignment.
- Gaming: player reports, chat, reviews, frustration and engagement, churn.
- Risk: incident reports and vendor assessments turned into probabilistic risk indicators for underwriting.
- Demand forecasting: purchase intent, supply concerns, competitive pressure, fed to time-series models.
- Knowledge graphs: relationship and entity-type classification, contradiction detection, "probabilistic traversal".

**Decision-shape table:** exactly the 10 you listed, each with "reach for it when" text and examples.

**Other use cases that appear elsewhere in the docs:**
- Refund-request adjudication: message plus transactions plus policy.
- Voice banking commands (confidence routing).
- Resume screening with composite IC-vs-manager weights.
- Resume de-duplication against candidate database records.
- Customer-service intent routing to deterministic code, specialist LLMs or humans.
- Smart-home command parsing (category, room, device, action), plus an "is this compound?" Noul that triggers an LLM splitter and an LLM fallback for chit-chat.
- Startup-pitch evaluation (decomposition example).
- Phishing/spam decomposition.
- Tool-call trace verification.
- Invoice field verification.
- PR-description scope scoring.
- Regulatory checklist over a document (GDPR).
- Legal passage re-ranking (CLERC).
- Line-level semantic search inside a document (GitHub ToS).
- Markdown structure recovery.
- Natural-language to typed function calls (trading).
- Agent skill suggestion (Hermes, 182 skills).
- Knowledge-graph entity alignment (beer catalogues).
- RAG passage gating: relevance, evidence, premise contradiction, injection.
- Citation verification (RFC 7519).
- LLM input/output guardrails.
- Structured-data-extraction verification, cascading to a reasoning model.
- Date extraction.
- Regex-candidate span selection (email, phone, money).
- Hierarchical classification over CPC patents, Shopify products, MeSH, and a codebase file tree.
- Wine-review score prediction with CatBoost features.
- SEC 10-K SIC industry classification with confidence fallback to the division.
- Insurance-claim triage rubric.
- Content-moderation rubric.
- The agent-skill page suggests finding places where "intelligent judgement… stand[s] in for complex parsing or other fragile code".

---

## B. Every concrete example question, grouped by use case
Format: id, type: instructions → criteria | state.

**Customer support triage** (quickstart, primitives, fan-out, SDK pages)
- `urgency` Noul: "Does this message express urgency?" | Stripe-integration-failing ticket.
- `department` Choice: "Which team should handle this" → billing "Payment or subscription issues" / technical "Bugs or integration problems" / sales "Pricing or account questions".
- `frustration` Score: "How frustrated the customer appears" → ["Calm, just stating facts", "Frustrated but civil", "Very angry, strong language"].
- `is_urgent` Noul: "The message conveys urgency or time-sensitivity". The same trio also runs on "Our API integration started returning 500 errors… can't process any customer orders".
- API page: `is_urgent` "Does this convey urgency?" with criteria true "Explicitly time-sensitive" / false "No urgency expressed". `department` → billing "Payments, invoicing, refunds" / technical "Bugs, outages, integrations" / sales "Pricing, upgrades, new accounts". `frustration` → ["Calm","Frustrated","Very angry"]. State: "Help! My payouts have been failing for 3 days."
- system-one.md: Choice "Which team should handle this ticket?" (billing/technical/account). Score "How frustrated is this customer?" (calm/frustrated/very frustrated). Noul "Does this message request a refund?"
- State: "My card was charged twice." `refund_requested` Noul "Does the customer request a refund?"
- Structured state (ticket.messages / order.charges / refund_policy):
  - "Does `ticket.messages[0].text` request a refund?"
  - "Does `refund_policy` support the refund requested in `ticket.messages[0].text`, given `order.charges`?"
- Flight state {ticket_message: "My flight was cancelled. Can I get a refund?", refund_policy: "Cancelled flights are eligible for a full refund."}:
  - Noul "Does `ticket_message` request a refund?"
  - Choice "What is the main request in `ticket_message`?" → refund "The customer wants money returned." / rebooking "The customer wants a replacement flight." / information "The customer is asking for information only."
  - Score "How frustrated does the customer appear in `ticket_message`?" → ["Calm and neutral.", "Concerned but civil.", "Very angry or using strong language."]
  - Noul "Does the refund policy support the refund requested in the ticket?"
- Nested state:
  - "Do `support.tickets[0].message` and `commerce.orders[0].charges` indicate a duplicate charge?"
  - "Can `account.security.password_reset` resolve the request in `support.tickets[1].message`?"
- Shoe store, state "My running shoes arrived in the wrong size…": `department` "Which team should handle this?" → returns "Exchanges, wrong or damaged items" / shipping "Delivery status, delays, lost packages" / billing "Charges, invoices, payment problems".
- Five-Choice triage, state "Shoes arrived two weeks late and in the wrong size. Also I see two charges of $120…":
  - `department` as above.
  - `return_reason` "If the customer wants to return something, why?" → wrong_size "The item doesn't fit" / wrong_item "A different product was delivered" / damaged "The item arrived broken or faulty" / changed_mind "The item is fine, the customer no longer wants it" / other "A return reason that fits none of the above".
  - `shipping_issue` "If this is a shipping problem, which kind is it?" → not_delivered "The package never arrived" / delayed "The package is late but still on its way" / wrong_address "The package went to the wrong place" / damaged_in_transit "The package arrived damaged" / other.
  - `requested_resolution` "What does the customer want to happen?" → exchange "Swap the item for a different one" / refund "Money back" / replacement "The same item sent again" / information "Just an answer, no action needed".
  - `tone` "What is the customer's tone?" → calm/frustrated/angry (null descriptions).
  - Results: department returns 0.61 / billing 0.35, confidence 0.42; resolution confidence 0.20.
- Contrastive criteria, state "I sent the shoes back a week ago. When do I get my money?": `return_topic` instructions {question "Which returns topic is the customer asking about?", focus "Classify the information the customer wants."}
  - return_policy {what "Whether and how an item can be returned", not_for "Progress of a return already sent", examples ["Can I return shoes I've worn once?","How long do I have to return an order?"]}
  - return_status {what "Progress of a return already sent", not_for "Whether and how…", examples ["Has my return arrived yet?","When will my refund be paid?"]}
  - Result: return_status at 1.0.
- `department` (advanced.md and how-to-build), state "I ordered the standing desk two weeks ago and tracking still says label created. Was I even charged?": {question "Which team should handle this message?", focus "Classify the customer's primary request, not every topic mentioned."}
  - billing {what "Charges, invoices, refunds, or subscriptions", not_for "Order tracking or account access", examples ["I was charged twice","Where is my refund?"]}
  - orders {what "Order status, delivery, cancellation, or returns", not_for "Charges or account access", examples ["Where is my package?","Cancel my order"]}
  - account {what "Login, password, profile, or security", not_for "Charges or delivery", examples ["I can't log in","Change my email"]}
- `card_help_topic`, state "How many disposable virtual cards can I make per day?":
  - get_disposable_virtual_card {what "Purpose, eligibility, or setup", not_for "Quantity, transaction, or merchant restrictions", examples […]}
  - disposable_card_limits {inverse, examples ["How many disposable cards can I make per day?","Where can I use a disposable card?"]}
- Human escalation (Noul page), state "I have asked three times now. Can I please just talk to a real person?":
  - `is_human_escalation` "Is the customer asking for a human agent?" → 0.99.
  - `is_repeat_contact` "Has the customer contacted support about this before?" true "Mentions a prior attempt, ticket, or that they have asked before" / false "No sign of any previous contact" → 0.93.
  - Recorded `is_human_escalation` values: "Thanks, that fixed it!" 0.02; "How do I reset my password?" 0.07; "I need this sorted today, whatever it takes." 0.26; "Are you a bot?" 0.40; "Is there any way to speak to someone about my invoice?" 0.84.
- Fan-out, state "Hi, I placed an order (#98423) last Thursday and was charged twice. I also can't log in… adding Apple Pay would be really helpful…":
  - `category` "Determine the broad category of this support ticket" → bug_report "The user is reporting something that is broken or producing errors" / billing "Charges, invoices, refunds, subscriptions" / feature_request "The user is requesting new functionality" / account "Login, permissions, profile, security".
  - `bug_severity` "How severe is the reported issue" → ["Cosmetic; no impact to functionality","Broken or degraded feature; workaround exists","Blocking issue; no workaround exists"].
  - `has_reproducible_steps` "The user describes specific steps to reproduce the issue".
  - `refund_requested` "The user is explicitly asking for a refund or credit".
  - `frustration` → ["Calm, matter-of-fact","Frustrated but civil","Very angry"].
- Intent routing:
  - `intent` "The primary intent of this customer message" → order_status "Asking about an existing order" / product_question "Asking about a product before buying" / return_exchange "Wants to return or exchange something" / complaint "Unhappy with experience, wants resolution".
  - `complexity` Score "How complex is this request to resolve" → ["Simple lookup or standard procedure","Requires some judgment or multi-step process","Unusual situation, edge case, or escalation needed"].
- SDK examples:
  - "Is this ticket about billing?" / "Is this about billing?" / "About billing?"
  - Choice "What is the customer's tone?" → calm/frustrated/angry.
  - Score "How urgent is this ticket?" → ["can wait","this week","today"] and "How urgent is this?" → ["low","medium","high"].
  - JS: choice("What is this ticket about?", {billing, technical, other}).
- Full triage workflow (how-to-build `triage_ticket.py`):
  - `topic` (contrastive billing/orders/account).
  - `requests_credentials` {question "Does the message request a sensitive credential?", compare [`ticket.message`,`policy.sensitive_credentials`], focus "Look for a request to disclose the credential itself."}; true {what "Asks the recipient to disclose a listed credential", examples ["Reply with your password","Send us your API key"]}; false {what…, not_for "A legitimate instruction to reset a credential", examples ["Use this link to reset your password"]}.
  - `sender_identity_mismatch` "Does the claimed sender identity conflict with its domain?" (examples "Acme Payroll sent from claim-bonus.example" vs "…acme.example").
  - `unexpected_reward` "Does the message announce an unexpected reward?" (not_for "A customer asking about a known refund or payroll deposit").
  - `refund_requested` "Does the customer explicitly request a refund or credit?" (focus "Require a requested remedy, not a billing complaint alone"; false example "Why was I charged twice?").
  - `mentions_open_order` "Does the message refer to a supplied open order?"
  - `frustration` Score {question "How frustrated does the customer appear?", focus "Judge expressed frustration, not issue severity."}, levels with `signals`.
  - Code weights: spam_risk = 0.45·creds + 0.30·mismatch + 0.25·reward.
- Weighted-quality snippet (Nouls named in code only): `answers_request`, `citations_are_supported`, `contradicts_context`.

**Bug/engineering triage** (Score page)
- `bug_severity` "How severe is the reported issue?" → ["Cosmetic; no impact to functionality","Broken or degraded feature, but workaround exists","Blocking issue; no workaround exists"]. Recorded states and scores:
  - misaligned button: 0.0
  - PDF export dead with a CSV workaround: 1.0
  - spinner, mixed CSV reports: 1.11 / confidence 0.84
  - Safari crash: 1.43 / 0.35
  - "Nobody… can log in… 500": 2.0
- Anti-example: "Rate severity from 0 to 2, where 2 is worst" with criteria ["0","1","2"] → 0.55 / confidence 0.33.
- Priority triage: `severity` (as above), `frustration` "How frustrated is the customer?" → [...,"Very angry, strong language or threatening to leave"], `report_quality` "How much does the report give an engineer to work with?" → ["No detail; just says something is broken","Names the feature but no steps or environment","Steps to reproduce or environment, but not both","Steps to reproduce and environment"]. Priority = 0.6·sev + 0.3·frus + 0.1·quality = 0.664.
- Structured levels with {what, examples}: typo/misaligned icon; "export fails in one browser but works in another"; cannot log in/data loss. Result 1.09/0.87. The Safari report went from 1.43/0.35 to 1.03/0.96 with a matching example; an unrelated example ("search fails, but browsing categories still works") left it at 1.43/0.35.
- `pr_scope` Score {question "How focused is this pull request description on a single change?", note "Judge the number of independent changes, not the size of any one change."} → [{summary "One change, clearly stated", signals […]}, {summary "One main change plus a small related tweak"}, {summary "Several independent changes bundled together"}] | state "Fixed the null check in the payment handler. Also refactored the retry loop…"

**Choice page one-liners:**
- "What programming language is this code written in" → python/javascript/typescript/go/rust/other
- "What type of meeting is this based on the title and description" → standup/planning/retrospective/one on one/brainstorm/none of the above
- "Which product category does this item belong to" → electronics/clothing/home garden/food and beverage

**Recruiting/HR**
- Noul "Is the candidate strong in Python?" compared with Score "How much Python experience does the candidate have?" (no experience / some familiarity / regular use in a job / deep expertise). Four candidates: 0.03/0.0, 0.14/1.0, 0.81/2.05, 0.92/2.89.
- Also: "Does the resume state that the candidate has used Python at work?", "Does this candidate have any Python experience?", "does the resume mention distributed systems".
- Duplicate detection: `same_as_record_{id}` Noul, instructions {potential_duplicate: {name, location, last_employer}, question: "Is the resume for the same person as `potential_duplicate`?"} | resume John Smith, Oakland, Google/Microsoft. Jon Smith/Oakland/Google 0.74; John Smith/Austin/Lone Star Freight 0.09; John Smithers/Oakland/Bay Health 0.08. Threshold 0.7.
- Composite scoring, 5-level Scores:
  - `python_depth` "How much depth of python experience does this candidate have, based on the supplied resume?" → No Python experience mentioned / Mentioned but no detail / Used in projects, some specifics / Primary language, multiple projects / Deep expertise: architecture, performance, libraries.
  - `team_leadership` "How much experience does this candidate have managing or leading engineering teams?" → none / informal mentorship or tech lead / led small team or project / managed team with direct reports / managed multiple teams or an org.
  - `system_design` "…designing large-scale or distributed systems?" → none / contributed to design discussions / designed components / owned architecture of a significant system / designed systems at scale across multiple domains.
  - `generalist` "How much evidence is there that this candidate picks up unfamiliar tools, roles, or domains outside their core specialty?" → only one domain / some variety in a narrow field / a few areas or stacks / regularly moved between domains / track record of ramping up.
  - Weights: IC .40/.10/.40/.10; EM .15/.40/.20/.25.

**Security / phishing / guardrails**
- Bad example: `is_spam` "Is `message` spam?"
- Good decomposition over the Acme Payroll phishing email:
  - `requests_credentials` "Does `message.body` ask the recipient to provide a password or other login credential?"
  - `offers_unexpected_reward` "Does `message.body` claim the recipient received an unexpected prize, payment, or reward?"
  - `creates_time_pressure` "Does `message.subject` or `message.body` pressure the recipient to act quickly?"
  - `sender_identity_mismatch` "Does the organization named in `message.sender.display_name` conflict with the domain in `message.sender.email`?"
  - `link_domain_mismatch` "Does the domain in `message.links[0].url` conflict with the organization named in `message.sender.display_name`?"
  - `disguises_link_destination` "Does `message.links[0].text` conceal or misrepresent the destination in `message.links[0].url`?"
- `requests_credentials` (advanced.md) {question "Does the `message` ask the recipient to disclose a sensitive credential?", inspect "message", focus "Look for a request to send the credential itself, not a request to change or reset it."}; true {what "Asks the recipient to reply with, type, or send a password, PIN, one-time code, or other security sensitive answer", examples ["Reply with your password","Send us the 6-digit code you just received"]}; false {what "No sensitive credential is requested", examples ["Reset your password from the settings page","Your statement is ready"]} | Beaver Dam Builders "Q3 bonus" email.
- Array-instructions example: {question "Does the claimed sender identity conflict with the sending domain?", compare ["ticket.sender.display_name","ticket.sender.email"], focus …}.
- LLM guardrails cookbook, INPUT battery (Noul + criteria):
  - `jailbreak` "Does this message try to get the assistant to ignore, override, or reveal its instructions, or to role-play as an AI with no rules?" (yes "It tries to bypass or expose the assistant's instructions or safety rules." / no "It is an ordinary request that respects the assistant's normal boundaries.")
  - `harmful_request` "Does this message ask for help causing physical harm to people, or for help breaking the law?"
  - `medical_advice` "Does this message ask for a diagnosis, a specific drug dosage, or a treatment decision, beyond general health information?"
  - `self_harm` "Does this message suggest the person sending it may be considering harming themselves?"
  - `severity` Score "How much harm could result if the assistant complied with this message?" → ["No harm: an ordinary, safe request or reply.","Mild: touches a sensitive topic but complying does no real damage.","Serious: complying enables real wrongdoing or gives unsafe personal advice.","Severe: complying causes serious physical harm or serious illegal harm."]
- Guardrails OUTPUT battery:
  - `broke_policy` "Does this reply comply with a request the assistant should have refused, such as role-playing as an AI with no rules or giving clearly unsafe or illegal help?"
  - `harmful_request` "Does this reply provide help causing physical harm…"
  - `medical_advice` "Does this reply give a diagnosis, a specific drug dosage, or a treatment decision…"
  - `self_harm` "Does this reply encourage the user to harm themselves, or help them do so?"
  - plus `severity`.
- Guardrails states: banana_bread, https_explainer, prescription_info (lisinopril), melatonin_dose, dosage_request, novelist_poison, lockpick_burglary, self_harm, dan, neurosemantical (inputs); banana_bread, prescription_info, good_refusal, dosage_request, jailbroken (replies).

**Tool calls / agents**
- Tool-trace verification, bad example: "Is `trace.tool_calls` correct for `request` and `available_tools`?" Good decomposition, 9 Nouls:
  - "Is `trace.tool_calls[0].name` an appropriate tool for resolving `request.location`?"
  - "Does `trace.tool_calls[0].arguments.city` match `request.location`?"
  - "Does `trace.tool_calls[0].arguments` conform to `available_tools.geocode_city.parameters`?"
  - "Does `trace.tool_results[0].tool_call_id` match `trace.tool_calls[0].id`?"
  - "Is `trace.tool_calls[1].name` an appropriate tool for answering `request.text`?"
  - "Does `trace.tool_calls[1].arguments` conform to `available_tools.get_weather.parameters`?"
  - "Do the coordinates in `trace.tool_calls[1].arguments` match those in `trace.tool_results[0].output`?"
  - "Does `…arguments.date` match `request.date`?"
  - "Does `…arguments.unit` match `request.unit`?" (the planted bug is celsius vs fahrenheit)
- Function calling (trading, 10 functions, 54 questions per command):
  - `__tool__` Choice "What is the user asking the trading assistant to do?" over function descriptions.
  - Per-argument Choice, e.g. style "Does the user want a plain line or candles?" → line "a simple line through the closing prices" / candles "a candlestick or OHLC chart, showing each bar's open, high, low and close".
  - `style?` "stated" Noul "Does the user say how the chart should be drawn, such as a line, candles, or OHLC bars?"
  - moving_average "How many bars should the moving average cover - nine, twenty, or fifty?" → "a nine-bar moving average, a fast one" / "a twenty-bar moving average" / "a fifty-bar moving average, a slow one", with stated Noul "Does the user ask for a moving average or a smoothed line over the candles?"
  - Set members: "Does the user want {} in the comparison?"
  - 14 commands with results, e.g. "is amd tracking nvidia lately" → rolling_correlation(AMD, NVDA), confidence 0.82. Most of spec.json is not published.
- Skill suggestion:
  - Request 1: `which` Choice "Which of these skills, if any, is the right one to load to help with the user's latest request?" over 182 names (60-char descriptions).
  - Gate Nouls: `acts_on_user_system` "Is the assistant being asked to act on the user's files, accounts, devices, or online services, rather than only to explain or advise?"; `would_follow_documented_procedure` "Would a careful expert answering this consult a specific documented procedure or set of commands, rather than answering from general understanding?"; `prose_suffices` (inverted) "Could a knowledgeable generalist fully satisfy this request in prose, with no tools, no documentation, and no access to the user's files or accounts?"
  - Request 2: `which` "Exactly one of these skills is the right one to load for the user's latest request. Which one? Read what each actually does, not just its name." plus `fits::{name}` "Does the skill '{name}' do the specific thing the user's request asks for? It is described as: …"
  - State {request, recent_context}.
- Smart home, paraphrased: "What category of request is this?", "What domain is this request targeting?", "What type of device…?", "What action should be taken on the lights?", plus a Noul asking whether the request contains more than one action.

**Banking / voice**
- Confidence page `action`: "What is the user trying to do?" → check_balance "View account balance" / approve_transfer "Approve the pending withdrawal request" / support "Get help with an issue".
- Confidence-routing pattern `intent`: "What action is the user requesting?" → check_balance "Check the balance of an account" / approve_transfer "Approve the pending transfer request" / other "Something else".

**Extraction / verification**
- Invoice (advanced.md), state "Invoice #4471 issued March 3, 2026 to Beaver Dam Logistics for $12,840.00, net 30.":
  - `invoice_number_is_correct` Noul {field {name,type,description "The identifier printed on the invoice."}, extracted_value "4471", question "Does `extracted_value` match the `field` as it appears in `source_text`?"}
  - `customer_name` Choice {field…, question "Which option is the value of `field` in `source_text`?"} → Beaver Logistics / Dam Logistics / Beaver Dam Logistics / Beaver / Dam.
  - `amount_due` Score "How large is the `field` value in `source_text`?" → Under $1,000 / $1,000 to $10,000 / $10,000 to $100,000 / $100,000 to $1,000,000 / Over $1,000,000.
  - `payment_terms` Score "How many days does the `field` in `source_text` allow for payment?" → Due on receipt / Net 10 / Net 30 / Net 60 / Net 90.
- SDE cascade (Noul batch per field; instructions {field_spec, extracted_field, main_question}):
  - name_desc_mismatch "Does the `extracted_field` fail to match the field at `path` or the `description` in the `field_spec`? If the `description` is empty, judge against the `path` alone."
  - type_mismatch "Does the `extracted_field` violate the `type` declared in the `field_spec`?"
  - unreasonable "Is the `extracted_field` one that a reasonable person would not have extracted for this `field_spec`?"
  - hallucinated "Is the `extracted_field` unsupported by, or absent from, the source text?"
  - off_target "Does the source text fail to genuinely report the thing the `field_spec` describes, so the value was pulled from incidental text?"
  - incomplete "Does the `extracted_field` fail to capture a value the source supports (note whether the `field_spec` is `required`)?"
  - format_violation "…violate the format or constraints implied by the `description`, the schema `type`, and the extraction instructions (e.g. date format, units, enum membership)?"
  - absence_wrong "The `extracted_field` is empty, null, or an empty collection. Does the source text contain the information the `field_spec` describes, making the empty result wrong?" (true "a value was wrongly omitted")
  - `__overall__::judge` "Is this extracted record an incorrect extraction … so it should be escalated to a smarter model?"
  - Each has explicit true/false criteria. State {system_message, instruction, source_text, schema, extraction}. Results: hallucinated 0.95, off_target 0.85, judge 0.56.
- Date extraction, 7 Choices per role such as "the deadline to return the form":
  - `mode` "How is {role} written? 'absolute' = … 'relative' = … 'none' = the document does not state this date." → absolute/relative/none
  - `month` "If {role} is an absolute calendar date, which month is it in?" → 12 months plus none
  - `day` "…which day of the month (1-31)?" → 1–31 plus none
  - `year` "…which year? Pick 'none' if the document states no year (code infers it), or 'out_of_range' if a year is stated but not in the list." → 1900–2050 plus out_of_range plus none (153 options)
  - `day_anchor` → today/tomorrow/day_after/weekday/none
  - `weekday` "If {role} names a day of the week, which one?"
  - `week_offset` → current/next/none
  - The "none" description throughout: "The document does not state this, or it is not this kind of date."
  - States: the contract, form, survey and review sentences. 6/6 correct; the missing kickoff date came back at confidence 0.46 and went to review.
- Pre-parsed values:
  - `pick` Choice over regex spans plus none "None of these is the requested value.": "Which email address does the sender want their receipt sent to?" (0.98), "Which email address did this message come from (the From line)?", "Which of these is the direct mobile / cell number?", "Which amount is the total the customer must pay?", "Which amount is the courtesy credit that was applied?"
  - `classify` Choice: "In what country is this office located?" (US/GB/DE/FR/CA/AU); "What currency are these amounts in?" (USD/EUR/GBP/JPY/CAD).
  - Noul "Is the amount {x} a credit or refund to the customer, not a charge?"
  - Suggested extra: a Noul asking which decimal convention the document uses.

**Search / RAG / citations**
- Re-ranking `is_cited_source` Noul: "The query excerpt comes from a US federal court opinion and was written immediately around a citation to a precedent; the citation itself has been removed. Could the candidate passage be from that cited precedent — does it establish the specific legal proposition the query excerpt invokes at its citation point?"
  - true "The candidate passage states or establishes the specific rule, standard, holding, or fact pattern that the query excerpt attributes to its removed citation."
  - false "The candidate passage is merely on a similar topic or doctrine; it does not supply the specific proposition the query excerpt relies on."
  - State {query_excerpt, candidate_passage}.
- Line search:
  - `where` Choice "Which line of the document contains the answer to: \"{query}\"?" over L000–L217 (null descriptions).
  - `exists` Noul "Does any line of the document address or answer: \"{query}\"?" true "At least one line of the document states or directly implies the answer" / false "No line of the document addresses this".
  - Queries: owns uploaded code (0.98 / L052 0.95), kicked off without warning, arbitration (exists 0.14), minors with parental permission (0.46, partial).
- RAG passage gating, state {query, passage{id,title,text,source_type}}:
  - `is_relevant` "Does this passage address the subject of the query?"
  - `contains_answer_evidence` "Does this passage state information usable in a direct answer?"
  - `contradicts_query_premise` "Does this passage conflict with a factual premise stated in the query?"
  - `contains_prompt_injection` "Does this passage attempt to control the system answering the query?"
  - Six queries, including the false-premise "Refresh tokens expire after 30 days - how do I extend that window?" and "Why are sessions deleted immediately when the inactivity timeout is reached?"
- Citation check `relation` Choice "How does the section relate to the claim?" → supports "The section states the claim or directly implies that it is true" / contradicts "The section states the opposite of the claim or implies it is false" / says_nothing "The section does not address what the claim asserts, either way". State {claim, section}.

**Regulatory / compliance (GDPR, parallel questions)**, state {article:{source,text}}
- Nouls:
  - breach_72h "Must a personal data breach be reported to the supervisory authority within 72 hours?" (0.80)
  - applies_non_eu "Does the regulation apply to organisations established outside the EU that offer goods or services to people in the EU?"
  - dpo_all_orgs "Must every organisation appoint a Data Protection Officer, regardless of what data it processes?"
  - pre_ticked_consent "Can valid consent be obtained through pre-ticked boxes or inactivity?"
  - right_erasure "Does the regulation grant individuals a right to erasure of their personal data?"
  - data_portability "Does the regulation include a right to data portability?"
  - us_federal_law "Is the GDPR a United States federal law?"
  - criminal_penalties "Does the GDPR itself impose criminal penalties such as imprisonment?"
- Choices:
  - instrument_type "What kind of EU legal instrument is the GDPR?" → Regulation "Directly binding law in all member states, no national implementation needed." / Directive "Sets goals that member states implement through national law." / Treaty / Recommendation "Non-binding guidance."
  - max_fine "What is the maximum administrative fine for the most serious infringements?" → TwentyM_or_4pct / TenM_or_2pct / FixedCap / NoFines.
- Scores:
  - individual_rights "How strong are the rights the GDPR grants to individuals over their data?" → None / Weak / Moderate / Strong (each with a description).
  - penalty_severity "How severe are the penalties the GDPR provides for non-compliance?" → None / Symbolic / Substantial / Severe "fines scaled to global revenue…"
  - compliance_burden "How heavy is the compliance burden the GDPR places on organisations?" → Negligible / Light / Moderate / Heavy / Extreme (0.75 normalized).

**Insurance** (Noul self-consistency, state `{uid, claim: CLAIM}`: policy AP-77413, track-day parking-lot rear-end, $3,250 including a $300 rental, auto-triage "Approved")
- covered "Is the loss covered under the policy's collision coverage?" (0.43–0.53)
- exclusion "Does a policy exclusion apply to this loss?"
- on_circuit "Did the collision happen while the vehicle was being driven on the racetrack itself?"
- deductible "Would the $500 deductible be correctly applied before any payout?"
- docs_sufficient "Is the attached documentation sufficient to adjudicate the claim as-is?"
- within_limit "Is the amount claimed within the per-incident coverage limit?"
- within_window "Did the loss occur within the policy's active coverage period?"
- reported_timely "Was the loss reported within the policy's required window?"
- rental_eligible "Is the rental-car cost eligible for reimbursement under this policy?"
- fraud_flag "Are there indicators that warrant a fraud review?"
- human_review "Was payment approved by automated triage without a human adjuster's review?"
- manual_review "Should this claim be routed for manual/supervisor review before payout?"
- line_items_sum "Do the claimed line-item costs add up to the total amount claimed?"
- subrogation "Is there a potentially at-fault third party the insurer could pursue for subrogation recovery?"

**Moderation** (Choice self-consistency, state `{uid, post}`: r/gamedebates reply "Are you seriously this dense?… you need to be dealt with… invite's right here… I'll end your whole channel.", discord.gg link, 1 strike, 4 reports)
- category "What is the single most applicable content-policy category for this post?" → None/Harass/Hate/Violence/Spam/Sexual (each described, e.g. Harass "Insults or demeans a person, with no threat of harm and no protected-class attack.")
- primary_risk "What is the primary moderation risk that should drive triage for this post?" → Harassment/Violence/LinkAbuse/AccountHistory/LowRisk
- target "Who or what is the content primarily directed at?" → None/Person/Group/Platform
- action "What enforcement action should be taken on this post?" → Allow/Warn/Remove/Strike/Escalate
- queue "Which single moderation queue should own this post?" → Auto/General/Threat/Spam/TSLead
- link_handling "How should any external link or off-platform invite in the post be handled?" → Allow/RmLink/Brigade/Escalate
- review_path "Who should make the final call on this post?" → Auto/Human/Senior/Legal
- severity "What is the overall severity of this post?" → None/Low/Medium/High

**Knowledge graph**
- `link_state` Score "How do the two entity descriptions relate as products?" → ["They describe two different products.", "They describe closely related products that may or may not be the same one: a variant, a special edition, or a name that could plausibly refer to either.", "They describe one and the same product."]
- Nouls: `same_name` "Do the two entities state the same beer name?", `same_brewery` "Are the two entities from the same brewery?", `same_style` "Do the two entities describe the same beer style?"
- State {entity_a, entity_b}. ABV is deliberately not asked ("comparing two numbers is arithmetic").

**Documents / structure recovery**
- Pass 1 `join` Noul: "Does line {Lk} pick up mid-sentence, continuing a sentence left unfinished at the end of line {Lk-1}?" true "The line starts in the middle of a sentence that began on the previous line - the line break tore the sentence apart" / false "The line begins a new sentence, item, heading, or thought of its own". The failed alternative was "Are lines X and Y part of the same paragraph?"
- Pass 2:
  - `type_B` "What kind of content is block {B}?" → heading "A short label or title that names the document or the section that follows it - not a full sentence of content" / paragraph "Running prose: one or more complete sentences…" / list_item "One entry in a list of parallel items…" / quote "Words attributed to a person or source…" / code "Computer code, a shell command, terminal output, or a config snippet meant to be read verbatim" / callout "A warning, tip, or important note that interrupts the flow…"
  - `hlevel` "As a heading, what level would block {B} occupy in this document's structure?" → title/section/subsection
  - `step` Noul "Is block {B} an instruction in a sequence where the order of the items matters?" (true "It is one step of a procedure…" / false "Order is irrelevant…")
  - `callout` "What kind of aside is block {B}?" → note/tip/warning

**Classification / taxonomies**
- Taxonomy walk (advanced.md): "Which top-level department does this product belong to?" with nested subtrees as criteria values | "32oz plastic bottle with a flip straw lid. Fits most bike cages."
- Hierarchical cookbook, each node: "Which direct child category best matches this document?" with keys c0…cN mapped to child labels. Documents:
  - "Patent abstract: a freestanding structural wooden perch for poultry or pet birds…" → A01K31/12
  - "Furniture listing: a wall-mounted window shelf bed… for one cat." → Cat Window Beds & Perches
  - "Clinical abstract: Crohn disease with transmural ileocolonic inflammation…" → C06.405.469.432.500
  - "Developer search: find the experimental Python module under x/eugene that implements BM25, dense, and fused retrievers for legal RAG." → retrievers.py
- SEC: `group` Choice "Which broad industry does this company operate in? Judge the company's own operations as this filing describes them." over 75 SIC major groups, each described as "umbrella — includes: up to 8 industries".

**Feature extraction (wine)**
- Fixed intensity levels: "Not present in this note at all" / "Barely present - mentioned once, in passing" / "Present at a moderate level" / "Present strongly - the note dwells on it" / "Dominant - the note is largely about this".
- Presence criteria: true "The note states this or clearly implies it" / false "The note gives no indication of this".
- Direct Score "Judging only by what this tasting note says, how good is the wine?" over 10 bands, from "Faulty or unpleasant - the note is mostly criticism" to "Profound - the note treats it as exceptional".
- Only one discovered question's text is printed: note_overall_tone_positivity "Setting aside specific descriptors, how positive is the overall emotional tone and word choice of the note taken as a whole (warm, admiring language throughout vs. flat, neutral, or lukewarm phrasing)?" (17.4% importance). The other 37 appear by name only (complexity, finish_quality, aging_potential, single_vineyard_or_prestige_signal, hedged_qualified_praise, …).

**Invariance probes** (jaggedness page)
- "Is the customer asking for a refund?" as Noul vs yes/no Choice on "I'm not happy with the fit. What are my options here?": 0.22 vs yes 0.01.
- Noul "refund" vs "Is the customer asking for something other than a refund?" on "I was charged twice… Can someone look into this?": 0.72 + 0.47 = 1.19.
- Counting example: "Is `items[i]` the name of a fruit?"

---

## C. Datasets used in cookbooks

| Cookbook | Dataset / link | What was asked | Reported results |
|---|---|---|---|
| Parallel questions | Wikipedia "General Data Protection Regulation", revision 1363040264 (2026-07), 53,777 chars | 13 questions (8 Noul, 2 Choice, 3 Score) | Batching adds no bias or noise (std 0.0 on 11/13; 2 Nouls std ~0.005). Batched $0.000497 / 0.27s vs 13 calls $0.006090 / 2.71s, so **12.2× cheaper, 10.0× faster** (primitives.md says 11.5×/9.6×) |
| Self-consistency: nouls | Synthetic auto-insurance claim JSON | 14 Nouls ×15 runs vs claude-haiku-4-5, gpt-5.4-mini (t=0/default/yes-no), gpt-5.5, claude-opus-4-8 | TS mean per-question std **0.0102** (lowest of the probability conditions); `covered` 0.43–0.53 crosses 0.5. 111ms, $0.000043 per call vs Haiku 16× slower / 42× costlier and reasoning models ~100–125× slower / ~780–805× costlier. Uncertain band 0.30–0.70 |
| Self-consistency: choices | Synthetic Reddit-like post | 8 Choices ×15 | Raw agreement 90.8% (LLMs 87.5–100%). Mean prob std 0.0098, lower than 5 of 6 LLM conditions; Haiku t=0 was 0.0012. Flips on primary_risk (11/4) and link_handling (8/7). With top-prob ≥0.60 rule: 99.2% agreement, 25.8% uncertain, 74.2% automatic, 0 conflicts. 114ms, $0.000046 |
| Re-ranking | CLERC (jhu-clsp/CLERC on HF, aclanthology 2025.findings-naacl.441), 170 rows pooled into 3,565 passages, 40 queries, BM25 top-30 | 1 Noul per (query, candidate), 1,200 calls | Top-1 5%→18%, top-5 15%→35%, top-10 38%→62%. 1,536,002 input tokens, $0.0645 |
| Line-by-line search | GitHub Terms of Service (gist), 218 lines, 43,980 chars | Choice over line ids plus exists Noul | Thresholds FOUND 0.7 / ABSENT 0.35; 4 example queries |
| Structure recovery | Synthetic build-migration memo (gist), 28 lines | 16 join Nouls, then 62 questions over 17 blocks | 11 breaks healed; 2 round trips, 10,211 tokens, 0.8s, "$0.0015" (printed $0.0003). Paragraph wording gives 12 blocks vs 17 |
| Function calling | Trader dataset, 156,780 one-minute bars, 6 tickers, 10 functions | 54 questions per command | 14 commands, confidence 0.53–1.00 |
| Skill suggestion | NousResearch/hermes-agent roster, 182 skills in 33 categories (MIT); requests.json with 488 requests (315 covered, 171 distinct skills, written by Claude Sonnet 5; 173 uncovered) | 2-stage Choice plus Nouls; agent is claude-haiku-4-5-20251001 | Wrong loads 16.8%→**7.3%** (oracle 2.5%); needless loads 9.8%→**4.0%** (oracle 1.2%). Fixed 37, broke 7. Gate 0.30, fits 0.30 |
| Entity alignment | Magellan "Beer" benchmark, 450 candidate pairs (name, brewery, style, abv) | Score plus 3 Nouls | 40 sameAs (8.9%), 50 curator (11.1%), 360 unlinked (80%). No accuracy vs `known_same_as` reported |
| Classifying RAG passages | 80 Supabase auth-docs passages (commit 2440b06, Apache 2.0) plus 1 planted forum injection; text-embedding-3-small at 256 dims, top-12; generator claude-sonnet-5 | 4 Nouls per passage over 6 queries (72 passages) | Injection 0.99 excluded every time; premise contradiction 0.92 sent to the conflict block; relevance reshuffled passages ranked 8/9/11 into evidence |
| Citation check | RFC 7519 (JWT), 58,365 chars, 45 sections; 8 LLM-written citations (4 edited to fail) | Choice supports/contradicts/says_nothing | 4 verified at ≥0.93, 1 fabricated by string match, 1 contradicted at 0.99, 2 unsupported (0.27, 0.56) sent to review. AUTO_ACCEPT 0.8 |
| Guardrails | 10 prompts plus 5 replies; jailbreaks from TrustAIRLab/in-the-wild-jailbreak-prompts | 4 Nouls plus severity Score | All four actions appear. Strict vs permissive policy flips neurosemantical (0.74) between block and review |
| SDE cascade | scrapegraphai/scrapegraphai-100k, revision 4bb9fba…, row 516 (NYU events page) | 7-metric Noul battery per field plus absence and overall | hallucinated 0.95 / off_target 0.85 trigger escalation to gpt-5.5, which returns "". On 100 prompts (internal), the cascade Pareto frontier beats every single model; gpt-5.5 alone is ≈0.81 quality at ≈$0.10 per extraction |
| Date extraction | 4 synthetic docs, 6 roles, TODAY = 2026-07-30 | 7 Choices | 6/6 correct, 1 sent to review (0.46) |
| Pre-parsed values | 3 synthetic docs (email headers, phones, invoice) | pick/classify/Noul | All correct (e.g. +14155550177; $1,315.50 charge at P(credit) 0.01) |
| Hierarchical classification | CPC 2026.05 XML, Shopify taxonomy v2026-02, MeSH 2026 desc2026.xml, CookSafe file snapshot | Choice per node, beam K=3 | Beam 4/4, greedy 2/4 (greedy missed CPC → E99Z99/00 and Shopify → Pet Chairs) |
| Autoresearch | GroNLP/ik-nlp-22_winemag (HF, revision 90eb39f…), 2,000 notes (1,200 dev / 800 test), proposer claude-sonnet-5, CatBoost | 5 rounds, 38 questions (29 Score, 9 Noul) | Held-out RMSE: mean 3.088; word counts 2.466; direct Score 2.145 (Spearman 0.761); round 1 with 18 questions 1.869; 5 rounds 1.772 (Spearman 0.799). Rounds 2–5 gain −0.097 (CI −0.147 to −0.050) |
| Classification using confidence | SEC sic_codes.tsv (444 codes, 75 major groups, 10 divisions); 60 10-K Item 1 filings (1993–2024) | 1 Choice over 75 groups | Forced group 39/60. Confident half (≥0.9) 27/30 = 90%; unsure half 12/30 = 40%, rising to 70% at division level; 48/60 useful overall |

---

## D. Design guidance

**Question scope**
- One snap judgment per question: something "a knowledgeable person makes in a second". "Analyze … best course of action" is a sign to decompose. The how-to-build page calls decomposing into atomic questions "probably the most important concept in this guide".
- Split multi-factor judgments into separate questions and weight them in code; change the weights, not the prompt. Normalize Scores by `len(criteria)-1` before weighting.
- Keep deterministic work, arithmetic, counting, dates and control flow in code. Don't ask anything code can compute exactly.
- The model never sees the question ID, so write the full question in `instructions`. Option names and descriptions are both sent.
- Point at state parts with backticked dot-and-index paths such as `ticket.messages[0].text`.
- Keep content in the state and judgments in the questions. Send only the relevant context, because irrelevant state causes context rot and distraction. Prefer your own knowledge base over model weights.
- Structured instructions and criteria: start with strings. Add an object when guidance blurs together (question/focus/inspect/compare/what/not_for/examples/signals). Field names are free-form but visible to the model, so keep the same field names across options and levels. Put code-sourced data such as DB rows in their own fields rather than string templates.

**Choosing the type**
- Choice: unordered known set; include the full list plus `other` / `none of the above`.
- Score: a spectrum you can describe.
- Noul: a clean yes/no where the probability itself is the signal.
- If two fit, pick the one whose answer maps directly onto code paths.
- A Noul value is not a degree: 0.5 means uncertain, not medium.

**Score rules**
- Describe situations, not degrees ("Moderately severe" is bad). Levels are evaluated separately without their numbers or neighbours, so "worse than previous" and numeric labels do nothing.
- Use as many levels as you can describe distinctly (at least 2, at most 10). One dimension per Score.
- Give a rare extreme case its own level (e.g. "abusive or threatening").
- If there is no in-between, use a Choice or several Nouls.
- Different distributions can give the same score, so read `probabilities` too.
- Examples in levels help only when they resemble real inputs. Higher confidence does not mean more correct; validate on labeled data.
- Don't interpolate exact magnitudes from a score (jaggedness page).

**Noul rules**
- One condition per Noul.
- Phrase it so that high means yes; avoid "free of X".
- Statements work as well as questions; test both.
- Make the boundary unambiguous ("any").
- Add true/false criteria when the boundary is subtle, and test with and without them.
- Don't invert criteria (true → no). Treat criteria as an extension of the instruction.

**Cookbook-derived heuristics**
- "Name the narrowest fact that decides it": "picks up mid-sentence" works where "same paragraph" fails.
- Write skill-gate Nouls about whether an action is wanted, not about subject matter.
- Write function-arg questions about the idea, not the parameter name ("Which resolution?" is bad). Spell out roles when two args share an enum ("the one being measured, named first" vs "the yardstick").
- Add a "stated?" Noul per optional argument so a default isn't guessed confidently.
- Verifier signals: narrow and grounded, bad = TRUE with explicit criteria, per-field then aggregate with `max` ("any flag fires"), independent, cheap, separating.
- The agent-skill page says: "Agents aren't great at writing questions". Keep questions and thresholds in a single file for review.

**Batching and speculation**
- Put every question for one state in one request, including speculative ones. Latency barely changes; you pay only the extra question tokens.
- Make a second request only when a real dependency exists (fetch new evidence, blocks that don't exist yet, or next-level options), as in skill suggestion, autoformat and hierarchical classification.
- Coding agents tend to fall into one question per call.

**Hierarchical classification**
- One Choice per level, walking the tree in code.
- advanced.md: use the children as options and each child's subtree as the option's value, so the model sees what lives below a branch; trim large subtrees to direct children plus sample leaves.
- The cookbook does something different: opaque keys c0..cN mapped to child labels, with no subtree.
- Beam search K=3 scored by geometric-mean edge probability `prod(p)^(1/decisions)`; use `exp(mean(log p))` for depth over 10.
- Separation = top/second path score; ~1× means ambiguous.
- Alternative metric: min(top/second) per node.
- Nodes with one child are not counted as decisions.
- SEC alternative: when confidence is low, report the parent level (no second call).
- The observability and testability of hierarchies are listed as benefits.

**Ranking / pairwise**
- The use-case map says "pairwise comparisons" and "cross-encode", but the only worked example is **pointwise**: one Noul per (query, candidate) in separate requests, sorted by noul.
- Choice over many candidates gives a relative ranking whose probabilities sum to 1, so something always ranks first. Pair it with an absolute existence or fits Noul, since each Noul can be low for all options.
- Past 255 options, use two passes (window then line; chunk then shortlist).
- Progressive disclosure: a cheap wide ranking, then a close look at the top 3 with full text.

**Verification patterns**
- Decompose "is X correct?" into per-component Nouls (tool calls, extraction fields).
- Do the string match in code first (fabricated quotes), then a Choice supports/contradicts/says_nothing.
- Use a separate conflict block for premise-contradicting evidence.
- Test injection first in routing order.
- The injection Noul "is a filter… Nothing here is a security boundary".

**Confidence and thresholds**
- `confidence` is derived from how peaked the distribution is; it exists only on Choice and Score. You can compute your own measure from `probabilities`.
- Use three bands (act / caution / don't act), with thresholds scaled to risk.

| Setting | Value |
|---|---|
| Confidence page floor; auto-approve transfer | 0.5; >0.9 |
| Confidence-routing pattern floor; transfer | 0.6; >0.85 |
| Intent routing | 0.5 |
| Triage department to manual | <0.3; cc a second team if its prob >0.25; ask the customer if resolution conf <0.5 |
| Noul routing | YES 0.8 / NO 0.2, middle goes to review; human escalation >0.9 |
| how-to-build | review <0.8; topic <0.75; spam band 0.4–0.6 |
| Self-consistency | Noul band 0.30–0.70; Choice top-prob ≥0.60 |
| Citation | 0.8 |
| Date | 0.60 |
| SEC | 0.9 |
| RAG | injection 0.70, contradicts 0.70, relevant 0.45, evidence 0.55 |
| Guardrails | review 0.35, action 0.70 (strict) / 0.85 (permissive), severity block 2.0 |
| SDE | 0.7 |
| Skill gates | 0.30 |
| Autoformat | join 0.2 after dangling / 0.5 after terminal punctuation; step mean ≥0.5; review type confidence <0.55 |
| Semantic find | exists 0.7 / 0.35 |
| Duplicate resume | 0.7 |

- If you only need the best option, take argmax rather than thresholding.
- Use `probabilities`, not `confidence`, for statistical algorithms.
- Don't carry a Noul threshold over to a Choice.
- Pin the model version if thresholds were tuned on it.
- Tune by plotting confidence against accuracy on your own data.

---

## E. New relative to your known list

**Pricing, limits and serving**
- $42 per Btok. Output tokens are free (billed on input only).
- Rate limit is also **250,000 tokens/sec**. Limits are "adjusting dynamically… can change without notice… upcoming large GPU deals"; higher limits on enterprise plans.
- Context: 64k is state plus all questions; **32k is state plus the single longest question**.
- Answer limits: Choice max 255 options (SEC cookbook: "works reliably up to roughly 240"). Score up to 10 levels; 11 returns a server error.
- Errors: 401, 422, 429, **529 Overloaded**.
- Cookbooks note that the public endpoint rate-limits "above roughly eight" concurrent workers.
- Latency: "most queries ~100 ms"; the use-case map says 150ms; measured 111–114ms per call.

**Models and access**
- Aliases `jev-latest` and `jev-preview`, both currently jev-1.13.0 (no preview build yet). The response `model` field reports the real version.
- `GET /v1/models` lists aliases only.
- Other model strings seen: `jev-1.13`, `jev`, OpenRouter `~typesafe/jev-latest`, Vercel AI Gateway `typesafe-ai/jev`.
- Most cookbooks were run on **jev-1.12**.
- Text only; English is the primary language, CJK and other languages are lower accuracy.
- No fine-tuning or LoRA; the same weights serve every account.
- Not trained on customer data; zero data retention (ZDR) for enterprise.

**Company framing**
- Training is RLCD ("reinforcement learning for calibrated decisions").
- Cofounder Diogo Almeida co-invented RLHF.
- "Machine Native Intelligence"; "Building prod, not God"; a 99% machine-to-machine thesis.
- Target of a ">100× intelligence-to-speed-and-cost ratio".
- Manifesto at typesafe.ai/manifesto; launch blog typesafe.ai/blog/introducing-system-one-models-and-jev.
- Discord for reporting failure modes.

**Determinism**
- There is no explicit API statement. The docs describe it as "designed to return stable answers" and "extremely consistent" (similar inputs give similar outputs).
- Observed noise is small but nonzero: a Noul crossing 0.5, Choice top-label flips, and self-consistency cookbook runs where "this policy does not make the model deterministic".
- The same answers come back batched or single.

**Jaggedness details beyond your 9 names**
- Counting is unreliable. Hex/RGB and assembly/binary are worse than English names or high-level code.
- Don't interpolate magnitudes from a score.
- Dates are read as text: extract the parts with Choice and compare them in code.
- A Noul and a yes/no Choice are not comparable, and P(noul) + P(not noul) ≠ 1.
- Adversarial content "can move the answer".
- Page last reviewed 2026-09-17.

**SDKs and agent skill**
- Python `typesafe-sdk` v0.7.1 (2026-09-21):
  - Supports `response_model`, `extra_body`, raw dict questions, `request_id`, and `.nouls/.choices/.scores`.
  - Defaults: timeout 10s; retries 2 with backoff 0.5–5s on 408/429/5xx; total retry budget 30s.
- JS `@typesafe-ai/sdk` v0.6.0 has a `dangerouslyAllowBrowser` option.
- Agent skill: `claude plugin install typesafe@typesafe-ai` or `npx skills add typesafe-ai/skills`.
- Playground share links; `cooksafe` cookbook helper package.
- The smart-home demo source is "available on GitHub at release".

**Inconsistencies in the docs worth knowing**
- Batching speedup: primitives.md says 11.5×/9.6×, the cookbook says 12.2×/10.0×.
- Noul page says the insurance rubric has "15 questions"; the cookbook has 14.
- Autoformat cost: the text says $0.0015, the printed output says $0.0003.
- Taxonomy walk: advanced.md recommends subtree values, but the hierarchical cookbook uses opaque c0..cN keys.
- "Pairwise reranking" is claimed on the use-case map but not demonstrated.
- The self-consistency cookbooks mention a leftover "speed_latest rate".
