# TypeSafe AI documentation archive (Jev / System One)

Verbatim raw-Markdown mirror of https://docs.typesafe.ai, fetched **2026-09-24** with `curl` by appending `.md` to each page path listed in the official index `llms.txt`. Directory layout mirrors the site's URL paths. Content is unmodified (each file keeps the site's own 3-line "Documentation Index" preamble). At fetch time the docs describe `jev-1.13.0` (jaggedness page last reviewed 2026-09-17); most cookbooks were rendered on `jev-1.12`.

- `llms.txt` — the official page index (111 pages), saved verbatim.
- `llms-full.txt` — the site's single-file full-text dump (~910 KB) of all pages, saved verbatim as a cross-check.
- 111 page files below, all fetched with HTTP 200. Internal links in the pages were checked: every linked docs page is present here.

Legal page links out to typesafe.ai/legal/{data-processing,mca,privacy-policy}; those are on the marketing site, not the docs, and are not archived here.

## Getting started & concepts

- `introduction.md` — **Introduction**: Jev is TypeSafe's flagship model and the first System One model. Send state and typed questions; get structured answers your code can use directly.
- `introduction/quickstart.md` — **Quick start**: Prefer to just dive in? Here's everything you need to get started immediately.
- `introduction/coding-agents.md` — **Jev with coding agents**: What Jev is (and isn't) when you're using a coding agent.
- `concepts/use-case-map.md` — **Example use cases**: Explore TypeSafe use cases by industry and turn promising ideas into software workflows.
- `concepts/system-one.md` — **System One**: System One models make fast, structured decisions for software. Jev is TypeSafe's flagship model and the first System One model.
- `concepts/state.md` — **State**: What state is, how to structure it, and how to give a System One model the context it needs.
- `concepts/how-to-build-with-system-one.md` — **How to build with TypeSafe**: Design AI-powered software by keeping code in control and giving System One narrow, structured decisions.
- `introduction/machine-learning-primer.md` — **AI primer**: Why TypeSafe trains decision models with calibrated probabilities instead of optimizing for generated text.

## Primitives & confidence

- `primitives.md` — **Primitives (Questions)**: The three TypeSafe question types (Choice, Score, Noul), the typed answers they return, how to choose between them, and how to ask several at once.
- `primitives/choice.md` — **Choice**: A Choice is a System One question type for selecting one option from a defined set. The answer includes the selected option, a probability for each option, and confidence.
- `primitives/score.md` — **Score**: A Score is a System One question type for rating content against ordered, descriptive levels. The answer includes a score, a probability for each level, and confidence.
- `primitives/noul.md` — **Noul**: A Noul question asks the TypeSafe model to evaluate a yes/no question and return the probability that the answer is yes.
- `primitives/advanced.md` — **Advanced: structure**: Instructions, Choice options, Score levels, and Noul criteria all accept JSON structure.
- `confidence.md` — **Confidence**: How TypeSafe reports certainty, how it differs from probability, and how to use it to control system behavior.

## Patterns

- `patterns.md` — **Patterns**: Architectural patterns for building systems with TypeSafe.
- `patterns/fan-out.md` — **Speculative fan-out**: Send many questions in a single call, including speculative ones, and let your code decide what's relevant.
- `patterns/confidence-routing.md` — **Confidence-gated routing**: Use confidence as a second axis. The answer tells you what; confidence tells you whether to act.
- `patterns/composite-scoring.md` — **Composite scoring**: Break a complex judgment into atomic scores, combine with weights you control in code.
- `patterns/intent-routing.md` — **Intent routing**: Classify incoming requests and route each to the optimal handler: deterministic logic, a specialist LLM, or a human.

## Cookbooks

- `cookbooks.md` — **Cookbooks**: End-to-end recipes that show TypeSafe in real problems, from a few questions to full pipelines.
- `cookbooks/consistency_noul_cookbook.md` — **Self-consistency: nouls**: Route uncertain probabilities to human review while keeping the underlying noul values visible.
- `cookbooks/consistency_choice_cookbook.md` — **Self-consistency: choices**: Add an uncertain outcome to moderation decisions and compare label agreement with the share of automatic actions.
- `cookbooks/parallel_questions.md` — **Parallel questions**: Runs a 13-question regulatory briefing over the GDPR Wikipedia article, showing that batching every question into one TypeSafe call is 12.2x cheaper and 10.0x faster with no change in answers.
- `cookbooks/rerank_typesafe.md` — **Re-ranking**: Builds 30-passage BM25 shortlists for 40 CLERC legal queries, then uses one TypeSafe question per query-candidate pair to raise top-1 accuracy from 5% to 18% and top-10 accuracy from 38% to 62%.
- `cookbooks/semantic_find.md` — **Line-by-line search**: Build semantic search for GitHub's Terms of Service. In one request, score 218 line ids against a plain-language query with a Choice question, and use a Noul question to check whether the document contains an answer.
- `cookbooks/autoformat.md` — **Structure recovery**: Reconstructs Markdown from plain text that lost its formatting in two requests: one stitches hard-wrapped lines back together, one classifies every block (heading, list, code, callout).
- `cookbooks/function_calling.md` — **Function calling**: Turns natural-language trading requests into calls to ordinary typed functions by mapping function names and closed-set arguments to confidence-aware TypeSafe questions.
- `cookbooks/skill_suggestion.md` — **Skill suggestion**: Picks at most one skill for an agent turn out of the 182 in Nous Research's Hermes catalog, using two TypeSafe requests to rank and re-check the top candidates.
- `cookbooks/entity_alignment.md` — **Knowledge graph entity alignment**: Decides which of 450 candidate pairs from two beer catalogues describe the same product using one Score question plus three companion Nouls that surface which fields disagree.
- `cookbooks/classifying_rag_passages.md` — **Classifying RAG passages**: Score each retrieved passage with one TypeSafe request, then decide in code which ones reach the answering model.
- `cookbooks/citation_check.md` — **Double-checking citations**: Catch wrong or hallucinated citations by checking against the source document. One Choice question decides whether the quote's context supports the claim.
- `cookbooks/llm_guardrails.md` — **Guardrails for LLMs**: Screen every message going into and out of an LLM app with one TypeSafe request, thresholding hazard probabilities and severity to pass, review, block, or route.
- `cookbooks/sde_cascade.md` — **SDE cascade**: Uses a 2-stage structured-data-extraction cascade (mini → verify → reasoning) to get most of the quality of a big reasoning model at a fraction of the cost.
- `cookbooks/date_extraction_cookbook.md` — **Date extraction**: Extracts absolute and relative dates by asking TypeSafe for the parts named in a document, then resolving and validating them in code with confidence-based review.
- `cookbooks/pre_parsed_value_extraction_cookbook.md` — **Pre-parsed value extraction**: Uses regexes to find candidate emails, phone numbers, and amounts, then has TypeSafe select the requested span so code can normalize a verbatim value.
- `cookbooks/hierarchical_classification.md` — **Hierarchical classification**: Classifies documents through deep patent, retail product, biomedical, and source-code hierarchies using parallel beam search over TypeSafe Choice probabilities.
- `cookbooks/autoresearch_feature_discovery.md` — **Autoresearch feature discovery**: Runs an autoresearch loop that proposes TypeSafe questions, converts free text into numeric features, and uses model errors to improve a supervised CatBoost regressor.
- `cookbooks/classification_using_confidence.md` — **Classification using confidence**: Classify SEC annual reports into 75 industry groups with one Choice each, then read the answer's own confidence to decide whether to report that group or the broader division above it.

## Demos

- `demos.md` — **Demos**: Interactive examples showing what's possible with TypeSafe.
- `demos/smart-home.md` — **Smart home assistant demo**: Demo code: a smart home assistant that uses TypeSafe to evaluate user requests.

## Models, API, jaggedness, legal, agent skill

- `models.md` — **Models**: Current models (jev-1.13.0), price $0.042/Mtok input (output free), 250k tok/s + 1,200 req/min, 64k/32k context, aliases jev-latest/jev-preview, language support, GET /v1/models.
- `api.md` — **API reference**: Full HTTP API reference for the TypeSafe evaluation endpoint.
- `agent-skill.md` — **Agent skill**: Drop-in skill for Claude Code, Codex, and other agent environments.
- `legal.md` — **Legal**: Legal documents and policies for TypeSafe.
- `model-jaggedness/jev-1.13.md` — **Jev 1.13 jaggedness**: Jev isn't perfect. Here are some jagged edges we are aware of with jev-1.13. Many of these will be fixed in later versions.

## Python SDK

- `sdk.md` — **Client SDKs**: Install a TypeSafe client SDK and use typed questions and answers in your application.
- `sdk/python.md` — **TypeSafe Python SDK**: Install the TypeSafe Python SDK and get started with asynchronous or synchronous API calls.
- `sdk/python/usage.md` — **Usage**: Guides and patterns for working with the TypeSafe Python SDK.
- `sdk/python/changelog.md` — **Changelog**: Python clients for the TypeSafe AI API
- `sdk/python/api.md` — **API reference**: Python clients for the TypeSafe AI API
- `sdk/python/api/clients/async.md` — **Asynchronous client**: Use AsyncTypeSafeClient to ask questions, list models, and configure asynchronous TypeSafe API requests.
- `sdk/python/api/clients/sync.md` — **Synchronous client**: Use TypeSafeClient to ask questions, list models, and configure synchronous TypeSafe API requests.
- `sdk/python/api/types/questions.md` — **Questions**: Provide state and ask yes/no, choice, and score questions using objects or dictionaries.
- `sdk/python/api/types/responses.md` — **Answers and responses**: Read answers, confidence scores, token usage, and available models returned by the TypeSafe API.
- `sdk/python/api/retries.md` — **Retries**: Configure retries with RetryPolicy — attempt count, retryable statuses, backoff, and retry headers handling.
- `sdk/python/api/types/common.md` — **Common types**: Common types for TypeSafe API SDK.
- `sdk/python/api/exceptions.md` — **Exceptions**: Handle TypeSafe API errors, rate limits, connection failures, and timeouts.
- `sdk/python/api/constants.md` — **Constants**: Default settings and environment variable names for the TypeSafe Python SDK.

## JavaScript SDK

- `sdk/javascript.md` — **JavaScript SDK**: JavaScript/TypeScript SDK (@typesafe-ai/sdk, Node 20+) quickstart.
- `sdk/javascript/changelog.md` — **Changelog**: JS SDK changelog (v0.5.7 initial release 2026-09-11; v0.6.0 Score.criteria as ordered sequence).
- `sdk/javascript/api.md` — **API reference**: Index of the JS SDK generated API reference (classes, interfaces, type aliases, variables, functions).
- `sdk/javascript/api/classes/APIConnectionError.md` — **Class: APIConnectionError**: JS SDK reference: Class: APIConnectionError.
- `sdk/javascript/api/classes/APIError.md` — **Class: APIError**: JS SDK reference: Class: APIError.
- `sdk/javascript/api/classes/APIPromise.md` — **Class: APIPromise<T>**: JS SDK reference: Class: APIPromise<T>.
- `sdk/javascript/api/classes/APITimeoutError.md` — **Class: APITimeoutError**: JS SDK reference: Class: APITimeoutError.
- `sdk/javascript/api/classes/APIUserAbortError.md` — **Class: APIUserAbortError**: JS SDK reference: Class: APIUserAbortError.
- `sdk/javascript/api/classes/AuthenticationError.md` — **Class: AuthenticationError**: JS SDK reference: Class: AuthenticationError.
- `sdk/javascript/api/classes/BadRequestError.md` — **Class: BadRequestError**: JS SDK reference: Class: BadRequestError.
- `sdk/javascript/api/classes/InternalServerError.md` — **Class: InternalServerError**: JS SDK reference: Class: InternalServerError.
- `sdk/javascript/api/classes/NotFoundError.md` — **Class: NotFoundError**: JS SDK reference: Class: NotFoundError.
- `sdk/javascript/api/classes/PermissionDeniedError.md` — **Class: PermissionDeniedError**: JS SDK reference: Class: PermissionDeniedError.
- `sdk/javascript/api/classes/RateLimitError.md` — **Class: RateLimitError**: JS SDK reference: Class: RateLimitError.
- `sdk/javascript/api/classes/TypeSafeClient.md` — **Class: TypeSafeClient**: JS SDK reference: Class: TypeSafeClient.
- `sdk/javascript/api/classes/TypeSafeError.md` — **Class: TypeSafeError**: JS SDK reference: Class: TypeSafeError.
- `sdk/javascript/api/classes/UnprocessableEntityError.md` — **Class: UnprocessableEntityError**: JS SDK reference: Class: UnprocessableEntityError.
- `sdk/javascript/api/interfaces/ChoiceQuestion.md` — **Interface: ChoiceQuestion<T>**: JS SDK reference: Interface: ChoiceQuestion<T>.
- `sdk/javascript/api/interfaces/ChoiceResponse.md` — **Interface: ChoiceResponse<T>**: JS SDK reference: Interface: ChoiceResponse<T>.
- `sdk/javascript/api/interfaces/Logger.md` — **Interface: Logger**: JS SDK reference: Interface: Logger.
- `sdk/javascript/api/interfaces/ModelCard.md` — **Interface: ModelCard**: JS SDK reference: Interface: ModelCard.
- `sdk/javascript/api/interfaces/Models.md` — **Interface: Models**: JS SDK reference: Interface: Models.
- `sdk/javascript/api/interfaces/NoulQuestion.md` — **Interface: NoulQuestion**: JS SDK reference: Interface: NoulQuestion.
- `sdk/javascript/api/interfaces/NoulResponse.md` — **Interface: NoulResponse**: JS SDK reference: Interface: NoulResponse.
- `sdk/javascript/api/interfaces/Questions.md` — **Interface: Questions**: JS SDK reference: Interface: Questions.
- `sdk/javascript/api/interfaces/RequestOptions.md` — **Interface: RequestOptions**: JS SDK reference: Interface: RequestOptions.
- `sdk/javascript/api/interfaces/RetryPolicy.md` — **Interface: RetryPolicy**: JS SDK reference: Interface: RetryPolicy.
- `sdk/javascript/api/interfaces/ScoreQuestion.md` — **Interface: ScoreQuestion<T>**: JS SDK reference: Interface: ScoreQuestion<T>.
- `sdk/javascript/api/interfaces/ScoreResponse.md` — **Interface: ScoreResponse<T>**: JS SDK reference: Interface: ScoreResponse<T>.
- `sdk/javascript/api/interfaces/SystemOneRequest.md` — **Interface: SystemOneRequest<Q>**: JS SDK reference: Interface: SystemOneRequest<Q>.
- `sdk/javascript/api/interfaces/SystemOneRequestPayload.md` — **Interface: SystemOneRequestPayload**: JS SDK reference: Interface: SystemOneRequestPayload.
- `sdk/javascript/api/interfaces/SystemOneResult.md` — **Interface: SystemOneResult<Q>**: JS SDK reference: Interface: SystemOneResult<Q>.
- `sdk/javascript/api/interfaces/TypeSafeClientConfig.md` — **Interface: TypeSafeClientConfig**: JS SDK reference: Interface: TypeSafeClientConfig.
- `sdk/javascript/api/interfaces/Usage.md` — **Interface: Usage**: JS SDK reference: Interface: Usage.
- `sdk/javascript/api/interfaces/WithResponse.md` — **Interface: WithResponse<T>**: JS SDK reference: Interface: WithResponse<T>.
- `sdk/javascript/api/type-aliases/ChoiceCriteria.md` — **Type Alias: ChoiceCriteria**: JS SDK reference: Type Alias: ChoiceCriteria.
- `sdk/javascript/api/type-aliases/Description.md` — **Type Alias: Description**: JS SDK reference: Type Alias: Description.
- `sdk/javascript/api/type-aliases/EntryType.md` — **Type Alias: EntryType**: JS SDK reference: Type Alias: EntryType.
- `sdk/javascript/api/type-aliases/EnvVar.md` — **Type Alias: EnvVar**: JS SDK reference: Type Alias: EnvVar.
- `sdk/javascript/api/type-aliases/Fetch.md` — **Type Alias: Fetch**: JS SDK reference: Type Alias: Fetch.
- `sdk/javascript/api/type-aliases/JsonValue.md` — **Type Alias: JsonValue**: JS SDK reference: Type Alias: JsonValue.
- `sdk/javascript/api/type-aliases/LogLevel.md` — **Type Alias: LogLevel**: JS SDK reference: Type Alias: LogLevel.
- `sdk/javascript/api/type-aliases/Question.md` — **Type Alias: Question**: JS SDK reference: Type Alias: Question.
- `sdk/javascript/api/type-aliases/ResultFor.md` — **Type Alias: ResultFor<T>**: JS SDK reference: Type Alias: ResultFor<T>.
- `sdk/javascript/api/type-aliases/ScoreCriteria.md` — **Type Alias: ScoreCriteria**: JS SDK reference: Type Alias: ScoreCriteria.
- `sdk/javascript/api/type-aliases/ScoreLegend.md` — **Type Alias: ScoreLegend<T>**: JS SDK reference: Type Alias: ScoreLegend<T>.
- `sdk/javascript/api/type-aliases/ScoreOf.md` — **Type Alias: ScoreOf<T>**: JS SDK reference: Type Alias: ScoreOf<T>.
- `sdk/javascript/api/variables/ENV.md` — **Variable: ENV**: JS SDK reference: Variable: ENV.
- `sdk/javascript/api/variables/LOG_LEVELS.md` — **Variable: LOG_LEVELS**: JS SDK reference: Variable: LOG_LEVELS.
- `sdk/javascript/api/variables/VERSION.md` — **Variable: VERSION**: JS SDK reference: Variable: VERSION.
- `sdk/javascript/api/functions/choice.md` — **Function: choice()**: JS SDK reference: Function: choice().
- `sdk/javascript/api/functions/noul.md` — **Function: noul()**: JS SDK reference: Function: noul().
- `sdk/javascript/api/functions/score.md` — **Function: score()**: JS SDK reference: Function: score().
