# GTM Agent

A general-purpose content agent prototype that turns audience questions or a user-selected topic into source-grounded content. Supplied documents support explanations; LangGraph coordinates drafting, source-support checks, bounded revision and human review. Business, audience, goal, tone and documents are campaign inputs; Nexus Vision is the first example.

**Current stage:** Local Streamlit prototype with hybrid retrieval, topic-scope review, automated draft-support checks and per-format campaign packages. A live standalone blog completed automatic revision and review. The later package is incomplete: LinkedIn passed, while blog and Google Business Profile reviews hit Gemini HTTP 429. A diagnostic confirmed daily quota exhaustion. Human and clinical approval remain required.

**Last progress update:** 5 October 2026.

[Inspect the 5 October automatic review and campaign-package evidence](https://gtm-campaign-sample.netlify.app/progress-oct5). Includes passing and blocked outcomes, original drafts, revisions and quota diagnosis. The page displays saved results, not a live AI service.

[Try the interactive saved sample](https://gtm-campaign-sample.netlify.app/). No installation or API keys needed. This browser sample lets visitors inspect saved research, review drafts and download test notes; it does not run fresh AI generation or the Python application.

[View the 2 October Streamlit PDF, screenshots and sample draft](https://gtm-content-progress-20261002.netlify.app/) · [View the 1 October audience evidence](https://gtm-audience-evidence-20261001.netlify.app/)

These public pages contain saved development evidence, not a live interactive app. The medical example remains a draft awaiting clinical review, not approved campaign content.

## Working workflow

```text
Audience research OR a user-selected topic
          |
Campaign brief + source documents
          |
Hybrid or keyword retrieval + evidence review
          |
Source-grounded topic + scope check
          |
Human reviews topic and selected statements
          |
One draft OR LinkedIn / blog / Google Business Profile package
          |
Source-support checks -> at most two revisions -> recheck
          |
Pass: pause for individual human review | Fail: block and retain audit
          |
Display and export; no automatic publication
```

Comments help identify questions worth addressing. Uploaded documents supply explanatory material. Titles and descriptions support positioning analysis; spoken-content analysis requires available captions. Speaker claims are attributed research context, not automatically verified facts.

The prototype supports LinkedIn posts, blogs and Google Business Profile posts, individually or as a campaign package. Each format has its own review, acceptance and retry; previous failed runs are retained. Package Markdown excludes blocked/rejected drafts, while JSON preserves the audit. All three formats were generated separately in the October 4 demonstration with manual editorial review. A complete three-format live pass through the new automated package workflow remains pending quota availability. Video generation, scheduling, publishing and conversion tracking are future work.

## Campaign inputs

| Input | Purpose |
| --- | --- |
| Business, audience and goal | Define whom the campaign serves and the intended action |
| Reference documents | Supply product, service, subject or research evidence |
| Formats, language, tone and CTA | Guide the output |
| Source review status | Keep draft material distinct from approved business material |
| Editorial direction | Refine scope and wording; it supplies no new factual evidence |

The first example is keratoconus education for Nexus Vision Speciality Eye Care, aimed at patients and encouraging a clinic appointment. The chosen language is English, tone warm and reassuring, and CTA **Call +91 8247710054 to book an appointment**. Generated prose must not use em dashes. Campaign timing and advertising service area remain undecided.

The six medical starter summaries and three later lens-replacement summaries were prepared by the assistant with citations, not supplied or clinically approved by the user. The user supplied the clinic website and campaign decisions. Sources and clinic details still require appropriate review; they do not substantiate invented prices, guarantees or procedure availability.

## Implementation status

| Component | Current status |
| --- | --- |
| YouTube collection and SQLite history | Working bounded prototype |
| English, Hindi and Hinglish comment interpretation | Working Gemini analysis; one live topic evaluated |
| Free caption retrieval and video research | Implemented with explicit unavailable-caption handling |
| Campaign inputs and document upload | Implemented for UTF-8 Markdown/plain text |
| Source-grounded topic briefs | Implemented with exact-excerpt and evidence-ID checks |
| Guided topic review and content writer | Implemented; all three formats generated in the live example |
| JSON, text and campaign Markdown exports | Implemented; per-format statuses and audit history retained |
| Factual guardrails | Exact-reference checks plus model-assisted support review; human review still required |
| Indexed document RAG | Default BM25 plus optional experimental local semantic + keyword retrieval |
| Local embeddings | Optional FastEmbed all-MiniLM-L6-v2; no hosted vector store |
| LangGraph | Integrated for retrieval/planning and bounded draft/review/revision workflows |
| Deep Agents | Not integrated |
| Direct-topic entry and campaign packages | Implemented locally; new package live validation incomplete |
| Automated draft review | Separate Gemini support-check call; not an autonomous subagent |
| Publishing and performance monitoring | Not implemented |

## Retrieval and grounding

Uploaded documents are split into overlapping passages and indexed locally with BM25. An editable audience question or user-selected topic retrieves up to six candidate passages. The reviewer inspects them before the planner receives those passages, comments and the campaign brief. The writer receives selected statements and their cited evidence. Exports retain passage IDs, document names, offsets, links and source review status.

The default is lexical RAG. Optional experimental hybrid search adds local English all-MiniLM-L6-v2 embeddings and reciprocal rank fusion. It adds no embedding API or hosted vector database. It can miss synonyms and cross-language matches; an English interpretation can seed a search of English documents. No matches block generation. Partial matches do not prove the question is answered: the planner and reviewer must identify missing support. Changing the question or documents invalidates old outputs.

RAG selects evidence; it does not verify whether a source is correct or whether a draft follows it faithfully. The first live RAG draft still added an unsupported generic introduction, which was caught in review and removed through regeneration. A separate model scope check now reviews the proposed topic before acceptance. A separate draft-support check now examines the headline and body sentences, requests up to two revisions and blocks incomplete or failed reviews. Broader retrieval and factual-support evaluation remain necessary.

## Evidence and limits

[Shared factual guardrails](guidelines/factual_guardrails.md) cover supplied facts, missing evidence, unsupported claims and human approval. Runtime checks reject unknown IDs, invented excerpts, missing paragraph references, changed CTAs and em dashes in generated prose. Original source quotations retain their punctuation.

Exact-reference checks establish traceability. The model-assisted reviewer additionally assesses source support, but can miss errors or overflag wording; it does not establish independent truth. Human review remains necessary. The live test exposed overly broad comparison framing and video findings whose brief excerpts did not support every implication. A comparison topic was narrowed before drafting. The 3 October example adds replacement evidence and narrows the scope to that question. Pricing, insurance, daily wear and treatment comparisons remain outside this completed sample.

The collection is a small snapshot of recent top-level comments, not exhaustive social listening. Engagement totals and repeated saved runs do not yet establish trends, market demand, audience geography, medical facts or bookings. Cross-industry accuracy and commercial readiness have not been demonstrated.

## Repository contents

| Location | Contents |
| --- | --- |
| [social_listening/](social_listening/) | Streamlit app, collector, analyzers, planner, writer, tests and setup |
| [docs/progress/2026-10-05/](docs/progress/2026-10-05/) | Automatic review, campaign package, audits, screenshots and quota diagnosis |
| [docs/progress/2026-10-04/](docs/progress/2026-10-04/) | Retrieval evaluation, live RAG evidence and review record |
| [docs/progress/2026-10-02/](docs/progress/2026-10-02/) | Earlier PDF, screenshots, drafts and source catalog |
| [guidelines/factual_guardrails.md](guidelines/factual_guardrails.md) | Reusable content and research rules |
| [data/raw/products/](data/raw/products/) | Cited keratoconus and lens-replacement summaries, plus clinic profile |
| [Campaign brief](data/raw/campaigns/keratoconus_campaign_brief.md) | First example's campaign decisions |
| [Editorial guidance](data/raw/campaigns/keratoconus_editorial_guidance.md) | First example's wording, tone and factual constraints |

## Daily progress

### 6 October 2026: Saved campaigns and successful review resumption

**Platform-policy correction (6 October):** The scleral-lens Google Business Profile draft is withheld pending platform-policy review, based on our conservative interpretation of [Google’s regulated-products guidance](https://support.google.com/business/answer/7342169?hl=en). This is not a Google rejection. Passing source-support checks does not establish platform suitability. The app blocks acceptance and omits this draft from campaign-copy Markdown while preserving the audit. LinkedIn and Blog remain drafts awaiting human review and clinical approval. This is a narrow English scleral-lens check, not comprehensive platform compliance. 96 automated tests pass.

Added local campaign saving and reopening with documents, inputs, drafts, prior runs and per-format decisions. API key fields and executable graph objects are excluded from snapshots. Interrupted claim checks can resume on an existing draft; already checked drafts can resume human approval without another model request.

**Live verified:** Reopened Nexus Vision and resumed the Blog and Google Business Profile checks using Gemini. Both passed with unchanged draft text and unchanged attempt counts (2 and 1 respectively). Blog reviewed 9 units; Google Business Profile reviewed 7. LinkedIn had already passed. All three await human review and medical content still needs clinical approval. Earlier failures remain in the audit.

**Validation:** 93 automated tests pass, including fresh-session reopening, credential exclusion, session-key retention, stale-save protection and review resumption. Automated model responses are mocked. The two resumed checks above were live Gemini calls.

[Public evidence and saved drafts](https://gtm-campaign-sample.netlify.app/progress-oct6) · [Audit and screenshots](docs/progress/2026-10-06/)

Next: test a new non-medical business with its own source documents, audience and campaign goal, then independent user testing. Campaign storage is local, not cloud sync. Public pages display saved outputs, not hosted generation.

### 5 October 2026: Automatic support review and campaign packages

**Implemented:** LangGraph retrieval/planning and draft/review/revision workflows, with at most two revisions and a pause for human review. Added direct-topic entry without audience analysis, multi-format campaign generation, separate approvals and retries, campaign exports, detailed validation failures and Gemini quota diagnostics. Session checkpoints remain in memory, not durable across restarts.

**Verified:** All 88 automated tests pass using mocked model responses and UI checks. A live standalone blog had an unsupported introduction rejected, was automatically rewritten, passed a second review and paused for user review, without manual text corrections. One other reviewer flag was overly strict; model checks remain fallible.

**Incomplete live test:** The direct-topic campaign generated a LinkedIn draft that passed review. The blog was automatically rewritten after an uncited introduction but its subsequent review hit HTTP 429. Google Business Profile review also hit HTTP 429. A small diagnostic request confirmed daily quota exhaustion for the configured model. Neither blocked format is shown as ready. The exact test outcomes and earlier attempts are retained in the audit.

**Limits:** The checker covers draft content, not every research interpretation or topic rationale. Clinical approval, durable campaign storage, independent user tests and broader nonmedical evaluation remain pending. No automatic publication or Deep Agents integration was added.

[Inspect the public progress page](https://gtm-campaign-sample.netlify.app/progress-oct5) · [Audits and test evidence](docs/progress/2026-10-05/)

### 4 October 2026: Passage retrieval connected to generation

**Full workflow verified:** A new live hybrid run passed the topic-scope check and generated LinkedIn, a short blog and Google Business Profile drafts through Streamlit. Codex editorial review corrected unsupported wording and added explicit source attribution; original outputs and the correction log are preserved. Reviewed drafts contain 143, 167 and 144 words. The [public sample](https://gtm-campaign-sample.netlify.app/) now displays these 4 October drafts and retrieved passages. [Inspect the full-run evidence](docs/progress/2026-10-04/hybrid-campaign/). Clinical approval remains pending.

**Follow-up:** Added optional local hybrid retrieval and a visible “Results updated for” message. Hybrid found the expected document for 9/9 original answerable questions versus BM25's 7/9, and 6/6 additional questions versus 5/6. These small hand-labelled tests include synthetic software data. Added a single-question planner and a separate Gemini scope check; 57 automated tests pass. [Comparison and live scope-review findings](docs/progress/2026-10-04/HYBRID.md).

- Added local BM25 indexing and retrieval over uploaded documents, with exact offsets, stable passage IDs, original source links and review metadata.
- Added question selection, editable search, retrieved-evidence inspection and JSON export in Streamlit. Topic planning now receives retrieved passages instead of whole documents.
- Added no-match blocking and invalidation when questions or documents change. Partial matches still require human assessment.
- All 48 automated tests passed. API responses in automated tests are mocked; tests cover retrieval isolation, provenance, absent evidence and the planner-to-writer path.
- Live-tested nine existing summaries, indexed into eleven passages. The replacement query retrieved six candidates and Gemini generated a topic linked to the original audience comment, followed by a LinkedIn draft. Review excluded one inferred statement and corrected an unsupported introductory generalization through regeneration.
- This is one lexical retrieval example, not a broad accuracy benchmark. Clinical review remains pending. The public browser sample was subsequently updated with the reviewed 4 October hybrid outputs.

[Review the retrieval evaluation and live evidence](docs/progress/2026-10-04/).

Next: broaden independent retrieval and scope evaluations, test real nonmedical campaign documents and improve factual review. Hybrid remains experimental; BM25 is still the default.

### 3 October 2026: An audience replacement question connected to supported drafts

**Completed**

- Added three cited reference summaries from Moorfields, Cleveland Clinic and a professional Contact Lens Spectrum article to address scleral lens replacement.
- Reanalyzed the existing 35-comment collection in Streamlit. Gemini proposed a replacement topic linked to the original audience comment.
- Reviewed the proposed statements, excluded one consequence not established by its selected excerpt, and generated LinkedIn, short blog and Google Business Profile drafts through the actual Gemini writer.
- Replaced the public sample's incomplete main example with this focused question, explanatory statements, original-source links and the three saved outputs.
- Retained the scope review gate and downloadable drafts, briefs and feedback notes. Changed selections cannot silently reuse a saved draft.

**Verification and limits**

- Checked exact excerpts, paragraph references, the phone CTA and the no-em-dashes rule. Drafts contain 175, 177 and 118 words respectively; the blog remains a short explanation rather than a long-form article.
- Reviewed the prose against the supplied summaries and the original source guidance. This review does not certify clinical accuracy or approve publication.
- The browser sample serves saved outputs, not live AI generation. Whole-document input and selected excerpts were used; indexed RAG remains unimplemented.
- Clinical approval, independent user testing, cross-industry evaluation and business outcomes remain pending.

**Evidence**

- [Try the focused sample](https://gtm-campaign-sample.netlify.app/)
- [Topic brief, actual generated outputs and review record](docs/progress/2026-10-03/lens-replacement/)

**Next work**

- Obtain clinical review for this medical example and independent feedback on the workflow.
- Implement and evaluate retrieval, then test a nonmedical campaign.

### 2 October 2026: Research connected to source-grounded drafting

**Completed**

- Added free caption retrieval and video research with numbered source passages and explicit transcript availability.
- Added document uploads, campaign settings, topic proposals, cited statements and missing-evidence questions.
- Added guided topic review and a writer for one selected LinkedIn, blog or Google Business Profile format.
- Added paragraph references, exact CTA checks, no-em-dash validation and TXT/JSON downloads.
- Saved the Streamlit PDF and a sample draft with source references as public development evidence.

**Validation and findings**

- All 35 automated tests passed on 2 October; mocked transport and UI checks complement the live sample.
- Reanalyzed the existing 35-comment, five-video collection: 18 relevant, 14 irrelevant and three uncertain. These model classifications are not an accuracy benchmark.
- Video research returned five analyses and three opportunities. A free auto-generated Hindi caption retrieval succeeded.
- Uploaded six assistant-prepared source summaries with clinical review pending. Narrowed an unsupported comparison topic and generated one LinkedIn draft from four selected statements.
- The draft retained the exact appointment CTA and paragraph references. Blog and Google Business Profile drafts were subsequently generated from the same four statements, exported and checked for valid references and the exact CTA. The blog introduction contains an extra management claim not established by its citation; it is flagged for removal during review. No campaign content was published.
- Exact excerpts do not guarantee semantic support. Ambiguous numbers, topic framing and source sufficiency still need review.

**Next work**

1. Implement and evaluate indexed RAG retrieval with source metadata.
2. Evaluate quality across all three formats and test a nonmedical campaign.
3. Improve semantic support checks and topic-to-evidence fit; retain human review.

### 1 October 2026: Social listening prototype implemented and tested

**Completed**

- Built a local Streamlit interface with YouTube collection, SQLite run history and JSON download.
- Integrated Gemini structured output to interpret English, Hindi and Hinglish comments inside the app.
- Added relevance classification, original comment evidence, content suggestions and missing-evidence requirements.
- Added validation that rejects unknown or missing comment IDs and derives theme counts from source records.
- Published a [saved evidence page](https://gtm-audience-evidence-20261001.netlify.app/) with the Streamlit PDF and AI JSON report.

**Validation and findings**

- Ten automated tests passed, including mocked API errors, duplicate handling, evidence validation and Streamlit UI flows.
- Live run collected 35 comments across five videos. The final Gemini run classified 18 as relevant and 17 as irrelevant, producing four themes.
- Captured questions the keyword baseline missed: per-eye pricing, wearing hours, exercise, bubbles and replacement.
- Verified the exported AI report and its supporting IDs and counts. Themes can overlap; counts are not unique people.
- One-sample validation is not an accuracy benchmark. The model inferred that “45” meant “45,000” and excluded a contact request that may be commercially relevant. Human review remains necessary.

**Next work**

- Improve ambiguous-number handling and relevance classification.
- Test more topics and larger, more varied samples before claiming cross-industry accuracy.
- Evaluate additional sources subject to data access and platform permissions.

### 29 September 2026: Factual guardrails defined

**Completed**

- Saved [reusable content and research guardrails](guidelines/factual_guardrails.md) for all industries and formats.
- Defined how to flag missing details and evidence, ask focused questions, and resolve or remove unsupported claims before publication.
- Added rules against invented metrics and customer claims, and separated factual claims from suggestions.
- Required evidence for trend and performance claims, original content, source traceability, campaign alignment, privacy, and human approval.

**Validation and next work**

- Checked that the note explicitly covers missing evidence and includes all 12 agreed rules.
- Documentation only: these rules are not yet enforced by a working agent. Niche research and performance analysis are not implemented.
- Next: include the shared guardrails in drafting and review instructions when implementing the agent.

### 28 September 2026: General-purpose scope clarified

**Completed**

- Updated the project description and problem statement to cover content across industries and topics.
- Documented the separation between the reusable agent, campaign inputs, brand guidance, and domain-specific review rules.
- Kept Nexus Vision as the first example and clarified the three initial formats and future video exploration.
- Generalized the planned evaluation criteria and retained example-specific checks.

**Validation and next work**

- Documentation-only update. This does not add working agent capabilities or establish performance on other domains.
- Next: implement reusable campaign configuration and document ingestion, then test retrieval before adding drafting and review.


### 27 September 2026: Scope and knowledge-base preparation

**Completed**

- Created the public repository and defined the first patient campaign.
- Prepared six medical topic files, each with its source citation.
- Added the clinic profile, campaign brief, and separate editorial guidance.
- Confirmed English, a warm and reassuring tone, the phone CTA, and the no-em-dashes rule.
- Selected LinkedIn posts, blog articles, and Google Business Profile posts as the initial output formats.

**Validation and findings**

- Inspected the reference application's loader and chunker. Its recursive character splitter uses a 1,000-character limit and 150-character overlap, without special handling for Markdown citations.
- Found that the initial combined document separated an eye-rubbing passage from its citation.
- Reorganized the material into short files. Local checks with the same splitter settings confirmed that each current ingestion document stays in one chunk, with medical citations attached.
- No embedding, Pinecone ingestion, retrieval, or agent-generation run has been completed. The chunking check is not an end-to-end application test.

**Next work**

1. Create the Python application structure and configuration.
2. Implement document loading and preserve source attribution through chunking.
3. Add embeddings and retrieval, then inspect returned evidence before connecting the agent.

**Open decisions**

- Select campaign timing and advertising service area.
- Choose the model/provider and configure the development environment and Pinecone namespace.

Future daily entries should record the work completed, verification results, remaining issues, and next actions under the actual date. Preserve earlier entries; record planned work as planned rather than completed.

## Running the prototype

From a local checkout, with Python 3.9+:

```sh
cd social_listening
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.address 127.0.0.1
```

Choose “I already have a topic” to begin with documents and a question, or use the labelled synthetic demo or a YouTube Data API key for public comment collection. A separate Gemini key runs analysis and generation. Account quota and pricing apply; no paid transcript fallback is used. See [setup, workflow and limits](social_listening/README.md).

```sh
python -m unittest discover -s . -p 'test_*.py'
```

Keep API keys, `.env`, local SQLite databases and private reports out of Git. The dated proof folder contains explicitly selected demonstration exports, not credentials or a local database.

## Evaluation still needed

- Whether retrieved passages support each full claim, including qualifications.
- Draft quality and factual alignment in all three formats.
- A second, nonmedical campaign without changing core logic or mixing campaign sources.
- Human review and clinical approval for the medical example before publication.
