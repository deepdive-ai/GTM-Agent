# 4 October: Local passage retrieval connected to Gemini

The Streamlit prototype now performs lexical RAG: it splits uploaded documents into overlapping passages, builds a local BM25 index, retrieves candidate evidence for a question, and sends those passages to the topic planner. Selected statements and excerpts then feed the writer. No embedding API or vector database is used.

## Actual live run

- Reused the 1 October collection: 35 comments across five YouTube videos. No new collection or video analysis was performed today.
- Uploaded nine existing assistant-prepared source summaries, with clinical review pending. They produced eleven indexed passages.
- Query: “Why do scleral lenses need replacement over time?” Six passages were retrieved. They include an irrelevant cross-linking passage and overlapping lens passages; retrieval is not perfect.
- Gemini 2.5 Flash proposed one topic, linked to the actual replacement question comment, and eight cited statements. Review excluded the fourth statement because it combined separate source points into an inference.
- Generated a LinkedIn draft using seven selected statements. Its four attached passages come from three documents. The writer used retrieved evidence, not the entire uploaded collection.
- The first draft added “valuable tool for many” and “like all medical devices.” Review requested regeneration. The exported second draft removes that opening and attributes the general lifespan to Cleveland Clinic.
- Remaining review issue: the final factual paragraph adds “to ensure your lenses continue to meet your needs.” The cited excerpt supports provider-recommended follow-up but does not explicitly establish that assurance. Remove that clause before publication. The unmodified model output is retained in the evidence file; it is not approved content.
- The exact phone CTA and no-em-dashes constraint passed. All citations were checked against retrieved passage IDs and exact excerpts; character offsets reproduce original document text.

## Tests and limits

48 automated tests passed. API responses in automated tests are mocked. Coverage includes unrelated queries, exact offsets, metadata preservation, bounded retrieval, cross-campaign isolation, changed questions/documents, rejection of citations outside retrieved evidence, and the planner-to-writer path.

In the live UI, “orchid irrigation” returned no matches and blocked generation. The local retrieval evaluation includes five queries. A price query can retrieve background lens material without answering price: matching words do not demonstrate evidence sufficiency. There was no live Gemini price test.

This is one retrieval-assisted draft, not a cross-industry benchmark or clinical validation. Keyword retrieval can miss synonyms and translations. The original summaries remain unapproved. No campaign content was published. The Netlify sample remains the saved 3 October example.

## Files

- [Live exported report](live-evidence.json): actual Gemini analysis, topic, draft, retrieved evidence and original source texts.
- [Local retrieval evaluation](retrieval-evaluation.json): five local search results, without Gemini generation.
- [Live draft screenshot](live-draft.jpg).
- [Source summaries](sources/).

Next: evaluate paraphrased questions, incomplete evidence and a nonmedical campaign; improve semantic support review before public campaign use.

## Follow-up

[Hybrid comparison, scope check and live rejection evidence](HYBRID.md) records the later implementation and 57-test verification. Earlier results above describe the initial lexical version.
