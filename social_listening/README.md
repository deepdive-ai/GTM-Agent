# Audience Listening Lab

GTM Agent's local Streamlit prototype connects YouTube audience research to topic planning and content drafts with source references. Campaign inputs and uploaded documents can change between businesses. Nexus Vision is the first live example; cross-industry performance has not been evaluated.

## Run

Python 3.9+:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.address 127.0.0.1
```

Use **Explore synthetic demo** for invented, labelled comments. Live collection requires a YouTube Data API v3 key restricted to that API. Gemini analysis and generation require a separate Gemini key. Enter keys in masked sidebar fields; do not commit credentials. Keys stay in session memory and are excluded from reports and SQLite. Account quotas and pricing apply; no paid transcript fallback is used.

[YouTube API setup](https://developers.google.com/youtube/v3/getting-started) · [Gemini key setup](https://aistudio.google.com/apikey)

## Workflow

1. Collect a bounded YouTube sample or open a saved run.
2. Click **Analyze audience signals** to interpret English, Hindi and Hinglish comments, classify relevance, and propose themes with supporting comment IDs.
3. Optionally attempt free transcript retrieval, then analyze video content and opportunities. Titles/descriptions support positioning analysis; spoken-content findings require available captions.
4. Upload 1-10 UTF-8 Markdown or plain-text documents and enter the campaign settings. Select an audience comment or enter a research question in the documents' language. The local passage index retrieves up to six keyword matches. Inspect the passages and confirm relevance, then generate proposed topics and explanatory statements for that question.
5. Review a topic, narrow its title if needed, select supported statements, choose one output format and confirm review. Generate a draft. LangGraph checks its claims and allows up to two revisions. Inspect the passing draft and paragraph references, then accept or reject it. Download TXT, JSON or the workflow audit.

LinkedIn, blog and Google Business Profile are selectable formats. The writer generates one selected format per request. Choosing several formats in the brief does not generate a batch.

## Evidence and guardrails

Audience comments justify topic selection; uploaded documents support explanations. Video speaker claims are research context and require independent support before being used as facts. Topic statements cite exact excerpts from uploaded sources. Video research selects numbered source passages; the app attaches original text. Unknown IDs, invented excerpts and invalid references are rejected.

The writer receives selected statements, original excerpts, campaign inputs and unresolved questions. Every explanatory paragraph must reference known statements. The CTA must exactly match the brief; generated prose cannot contain em dashes. Original quotations retain their punctuation. Missing evidence is displayed explicitly, and unsupported questions must remain unanswered. A separate Gemini call checks the headline and every body sentence against its cited excerpts. Missing reviews, invented references, unsupported claims and uncertain support prevent acceptance. LangGraph requests up to two revisions and blocks the draft if problems remain. Human review is still required: model-assisted support checks can miss errors and do not establish source truth or clinical correctness.

Sources are supplied material, not automatically verified facts. Review confirmation does not certify accuracy or approve publication. Changing inputs clears stale derived outputs. Nothing is scheduled or published to campaign channels.

## Retrieval-augmented generation

The planner now receives retrieved passages instead of all uploaded document text. `retriever.py` splits documents into passages of up to 1,000 characters with roughly 180 characters of overlap, preserving exact offsets, line numbers, document names, source links and review metadata. A local in-memory inverted index ranks passages using BM25. The six highest-scoring matches are shown for review before generation.

The index is rebuilt from the current upload set, with no shared cross-campaign document cache. Retrieval requires no API key, embeddings, hosted database or new dependency. Gemini still handles audience analysis, topic statements and drafting under the user's account quota.

Generated citations must reference a retrieved passage ID and an exact excerpt within that passage. The writer exports the used passages and their provenance. Changing the research question, sources or brief invalidates existing topic and draft outputs. No matches block a generation request. Partial or irrelevant matches still require a missing-evidence assessment by the planner and a human reviewer.

Keyword (BM25) remains the default. An optional experimental Hybrid search combines BM25 with local all-MiniLM-L6-v2 embeddings through FastEmbed and reciprocal rank fusion. Install it with `python -m pip install -r requirements-hybrid.txt`, then select Hybrid in the UI. First use downloads roughly 90 MB of public model weights into `.model-cache`; document text stays local during retrieval. Only model weights are cached between requests. There is no embedding API fee or hosted vector database. Gemini generation still uses the configured account quota.

Hybrid semantic candidates require cosine similarity of at least 0.35, a provisional cutoff rather than a confidence score. The English encoder reads up to 256 tokens per passage; unusually token-dense chunks can be truncated by the encoder while full passage text remains available to BM25 and the planner. This is a small-corpus experiment, not calibrated cross-language retrieval. Missing optional dependencies or model failures are explicit errors, never silent fallback. Keyword mode remains available.

Topic planning now requests one topic scoped to the research question. A second Gemini call checks title, rationale, statements and evidence requests for scope drift. Failed, invalid or unfinished checks block acceptance. A model scope check can still miss errors and is not factual verification. Changing the search method or scope-check version invalidates prior approvals and outputs. LangGraph now coordinates retrieval and planning, plus a separate drafting graph with source-support review, bounded revision and a user-review pause. Deep Agents and automatic publication are not implemented.

## Limits and storage

- Collection: up to ten videos and 100 recent top-level comments per video; no replies or exhaustive search. Publication window filters videos. English is a search hint, not a language/location filter.
- Audience analysis: up to 100 comments and 150,000 serialized input characters. Themes can overlap; counts refer to comment IDs, not unique people.
- Source planning: up to ten documents, 100,000 document characters and 200,000 combined input characters.
- Transcript retrieval: local `youtube-transcript-api`, English/Hindi preference, bounded timeouts, up to 40,000 characters per transcript. Blocked/missing captions remain explicitly unavailable. No Apify actors, paid proxies, authentication cookies or paid transcription fallback.
- Video research: up to 200,000 serialized input characters. No silent truncation. Auto-generated captions can be wrong; short excerpts may fail to support all implications of a finding.
- SQLite stores collections locally; snapshots older than 29 days are removed on database access. AI results, transcripts, uploaded documents and drafts remain session-only and can be exported. Manage downloaded copies separately.
- Snapshots and accumulated engagement totals do not establish trends, causal performance, medical facts, geographic demand or bookings. Automatic metric-change calculations and monitoring are not implemented.

Before commercial distribution, review current platform policies for the intended integration. This is a development prototype.

## Verification on 4 October 2026

All 48 automated tests pass. New coverage includes retrieved-only planner inputs, exact source offsets, metadata preservation, unrelated queries, cross-campaign isolation, stale queries/documents, missing-evidence responses and writer provenance. Gemini responses in automated tests use a mock transport. The local nine-document retrieval evaluation is saved separately; it is not a clinical validation or broad retrieval benchmark.

The live nine-document run generated a replacement topic and LinkedIn draft using retrieved passages. Review removed one proposed inference and regenerated an unsupported introduction. The final export still needs a follow-up assurance clause removed and clinical review. See [the live evidence and review record](../docs/progress/2026-10-04/).

## Verification on 2 October 2026

```sh
python3 -m unittest discover -s . -p 'test_*.py'
```

Thirty-five tests passed, covering mocked API failures, evidence validation, missing-evidence handling, stale-input checks, CTA checks, source passage attachment and Streamlit UI flows. They are not an accuracy benchmark.

The live sample used an existing collection of 35 comments across five videos. The audience analysis classified 18 relevant, 14 irrelevant and three uncertain. Video research returned five analyses and three opportunities. Free retrieval succeeded in a tested auto-generated Hindi caption example.

Six assistant-prepared, clinically unreviewed source summaries were uploaded. A comparison topic was narrowed during human review because the documents supported background information rather than an ICL/LASIK comparison. A LinkedIn draft was generated from four selected statements and exported with paragraph references and the exact CTA. Blog and Google Business Profile drafts were subsequently generated from the same four statements, exported and checked for valid references and the exact CTA. The blog introduction contains an extra management claim not established by its citation; it is flagged for removal during review.

Known issues include ambiguous-number interpretation, overly broad topic framing and excerpts that may not support an entire finding. Clinical review remains pending. No campaign content was published.

[View today's PDF, screenshots and draft evidence](https://gtm-content-progress-20261002.netlify.app/)

## Hybrid retrieval follow-up on 4 October 2026

57 automated tests pass, with mocked model responses and semantic candidate fixtures. Actual local-model evaluation found the expected document for 9/9 answerable questions in the original set (BM25: 7/9), and 6/6 additional answerable questions (BM25: 5/6). Every successful expected document ranked first. These are small hand-labelled examples, including synthetic software documents, not a general accuracy estimate or evidence-sufficiency benchmark. See the dated HYBRID report for live scope-check findings and limits.

## October 5: LangGraph workflow validation

The local implementation adds a mandatory source-support review after drafting. Each review covers the headline and every body sentence; the exact CTA is checked separately against the brief. The reviewer receives cited excerpts, not permission to use its own knowledge as evidence. Citation excerpts are checked against source text before a review request is sent.

The graph retains each generated draft and its review, allows two revisions, and pauses for explicit user acceptance only after the automated check passes. Failed or incomplete checks block the workflow. Acceptance is an editorial decision, not clinical approval or publication.

Checkpoints are held in session-local memory and are lost when the session or server ends. API credentials are kept outside graph state and exports. A drafting run uses two model calls when it passes immediately, and up to six if both revisions are needed; earlier analysis and planning calls are additional.

Eleven new automated tests cover complete review coverage, invalid citations, uncertainty, review failures, bounded revision, pause/resume, credential exclusion and no-evidence blocking. These use mocked model responses. Live Gemini validation completed on October 5 using the lens-replacement question and three source summaries. The initial blog failed on two sentences, the graph requested one revision, and the revised draft passed seven review units and paused for user review. No manual text correction was applied. The audit preserves both attempts. One flag was overly strict, illustrating that model review is fallible. This check covers the generated draft, not every research interpretation or topic rationale. October 4 published samples still reflect the manual review described in their correction log.

## Direct topics and campaign packages

Choose either audience-led discovery or “I already have a topic.” Direct-topic mode requires no YouTube collection or audience analysis. It still requires uploaded evidence, a research question, a campaign brief and review of retrieved passages before topic planning. It explicitly identifies the topic as user-selected and does not claim audience interest or market demand.

From a reviewed topic, generate any combination of LinkedIn post, Blog and Google Business Profile post as one package. Each format independently runs the existing LangGraph drafting, support-check and bounded-revision workflow. A failed format does not erase successful formats. Each passing format pauses for its own acceptance or rejection. Editing the topic, selected facts, sources, brief, formats, model or editorial direction invalidates the package.

Download Markdown with paragraph statement references and source excerpts, or a JSON audit containing every original draft, review and revision. Markdown excludes blocked and rejected content and labels pending approvals; JSON retains failed attempts for inspection. A complete three-format run uses 6–18 model calls for drafting and review, in addition to planning. Nothing is published automatically. State remains session-local.

Blocked or rejected formats can be retried individually. The audit retains earlier runs and the successful formats are preserved. Planning also checks citation locations: if an unchanged quote occurs in exactly one other retrieved passage from the same document, the passage reference can be corrected with an audit entry. Missing, ambiguous, unknown-source or cross-document matches are still rejected.

Validation: 81 automated tests pass, using mocked model responses. In the live direct-topic package test, LinkedIn passed; Blog was automatically rewritten after an uncited introduction, but its subsequent review hit Gemini HTTP 429. Google Business Profile review also hit HTTP 429. Both remain blocked and the package is explicitly incomplete. All three passing live outputs have not yet been verified. The source summaries still require clinical review.

Quota diagnostics now distinguish daily exhaustion, per-minute limits, zero quotas and unknown 429 errors from Google's response metadata. The sidebar access check sends one small test request and consumes quota. Changing the key or model clears its displayed diagnosis. Live diagnosis on October 5 confirmed daily quota exhaustion for the configured Gemini model; the next reset is October 6 at 12:30 PM IST. 88 automated tests pass.
