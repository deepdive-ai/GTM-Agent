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
4. Upload 1-10 UTF-8 Markdown or plain-text documents and enter business, audience, goal, formats, CTA, language, tone and source review status. Generate up to three proposed topics and explanatory statements.
5. Review a topic, narrow its title if needed, select supported statements, choose one output format and confirm review. Generate a draft, inspect paragraph references, and download TXT or JSON.

LinkedIn, blog and Google Business Profile are selectable formats. The writer generates one selected format per request. Choosing several formats in the brief does not generate a batch.

## Evidence and guardrails

Audience comments justify topic selection; uploaded documents support explanations. Video speaker claims are research context and require independent support before being used as facts. Topic statements cite exact excerpts from uploaded sources. Video research selects numbered source passages; the app attaches original text. Unknown IDs, invented excerpts and invalid references are rejected.

The writer receives selected statements, original excerpts, campaign inputs and unresolved questions. Every explanatory paragraph must reference known statements. The CTA must exactly match the brief; generated prose cannot contain em dashes. Original quotations retain their punctuation. Missing evidence is displayed explicitly, and unsupported questions must remain unanswered. Human review checks whether the evidence supports the full meaning. Citation checks establish traceability, not semantic or clinical correctness.

Sources are supplied material, not automatically verified facts. Review confirmation does not certify accuracy or approve publication. Changing inputs clears stale derived outputs. Nothing is scheduled or published to campaign channels.

## Current grounding method and next RAG milestone

The planner sends whole uploaded documents to Gemini. The writer uses selected statements and their excerpts. There is no indexed chunk retrieval, embeddings, vector store, LangGraph workflow or review subagent yet.

Next: load and chunk documents with source metadata, index them, retrieve relevant passages for each topic and evaluate retrieval before connecting it to drafting. Source review remains necessary after RAG is added.

## Limits and storage

- Collection: up to ten videos and 100 recent top-level comments per video; no replies or exhaustive search. Publication window filters videos. English is a search hint, not a language/location filter.
- Audience analysis: up to 100 comments and 150,000 serialized input characters. Themes can overlap; counts refer to comment IDs, not unique people.
- Source planning: up to ten documents, 100,000 document characters and 200,000 combined input characters.
- Transcript retrieval: local `youtube-transcript-api`, English/Hindi preference, bounded timeouts, up to 40,000 characters per transcript. Blocked/missing captions remain explicitly unavailable. No Apify actors, paid proxies, authentication cookies or paid transcription fallback.
- Video research: up to 200,000 serialized input characters. No silent truncation. Auto-generated captions can be wrong; short excerpts may fail to support all implications of a finding.
- SQLite stores collections locally; snapshots older than 29 days are removed on database access. AI results, transcripts, uploaded documents and drafts remain session-only and can be exported. Manage downloaded copies separately.
- Snapshots and accumulated engagement totals do not establish trends, causal performance, medical facts, geographic demand or bookings. Automatic metric-change calculations and monitoring are not implemented.

Before commercial distribution, review current platform policies for the intended integration. This is a development prototype.

## Verification on 2 October 2026

```sh
python3 -m unittest discover -s . -p 'test_*.py'
```

Thirty-five tests passed, covering mocked API failures, evidence validation, missing-evidence handling, stale-input checks, CTA checks, source passage attachment and Streamlit UI flows. They are not an accuracy benchmark.

The live sample used an existing collection of 35 comments across five videos. The audience analysis classified 18 relevant, 14 irrelevant and three uncertain. Video research returned five analyses and three opportunities. Free retrieval succeeded in a tested auto-generated Hindi caption example.

Six assistant-prepared, clinically unreviewed source summaries were uploaded. A comparison topic was narrowed during human review because the documents supported background information rather than an ICL/LASIK comparison. A LinkedIn draft was generated from four selected statements and exported with paragraph references and the exact CTA. Blog and Google Business Profile drafts were subsequently generated from the same four statements, exported and checked for valid references and the exact CTA. The blog introduction contains an extra management claim not established by its citation; it is flagged for removal during review.

Known issues include ambiguous-number interpretation, overly broad topic framing and excerpts that may not support an entire finding. Clinical review remains pending. No campaign content was published.

[View today's PDF, screenshots and draft evidence](https://gtm-content-progress-20261002.netlify.app/)
