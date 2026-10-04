# 4 October 2026: Full hybrid campaign workflow verified

A new live Streamlit run used **How long will my lenses last?** as the research question. The audience evidence is one original comment from the 1 October collection: “Will have to change lens after interval of time”. No new collection was performed.

## Completed workflow

1. Nine existing reference summaries were indexed into eleven passages. Hybrid BM25 plus local MiniLM retrieval returned six candidates.
2. Gemini 2.5 Flash proposed one lifespan topic with seven cited statements. The separate Gemini scope check passed.
3. Codex reviewed all seven statements against their excerpts. They cite four passages across three documents. Clinical review remains pending.
4. The actual Streamlit writer generated LinkedIn, Blog and Google Business Profile outputs separately from the same statements. All three raw exports are retained.
5. Codex editorial review corrected the topic's unsupported “frequently” description to one cited audience comment. The blog's uncited introductory management claim and inferred extension of lens life were removed. Explicit Cleveland Clinic attribution was added to each format's general lifespan estimate.
6. Reviewed outputs retain paragraph references, original-source links, the exact phone CTA and no em dashes. The public sample displays the edited copies and labels them accordingly.

## Results and limitations

| Format | Reviewed body word count | Review result |
| --- | --- | --- |
| LinkedIn | 143 | Claims align with selected excerpts; explicit attribution added |
| Short blog | 167 | Unsupported opening and lifespan-extension inference removed; explicit attribution added |
| Google Business Profile | 144 | Claims align with selected excerpts; explicit attribution added |

The blog is deliberately a short explanation, not a 400–650-word article. Its raw model review note says the evidence was insufficient for a longer article. No claim of format-quality benchmarking is made.

The system performed retrieval, scope review and generation. The editorial corrections were made by Codex after export, not automatically by the app and not by a clinician. `generation_input_fingerprint` identifies the original generation input; edited copies have a separate content hash and review record. Exact references and scope checks do not prove factual accuracy. Clinical approval is still required before these medical drafts are used as campaign content.

The original output's frequency claim and blog additions show that scope review is not a factual review. The reviewed public demonstration is not a clinical approval or evidence of business results. No LinkedIn or Google campaign posts were published.

## Evidence

- `campaign-evidence.json`: original topic, retrieval, relevant audience comment, all three raw outputs and review log. Unrelated audience comments are excluded from this selected proof bundle.
- `linkedin-raw.json`, `blog-raw.json`, `gbp-raw.json`: actual Gemini exports.
- Corresponding `*-reviewed.json` and `*-reviewed.txt`: editorially corrected copies.
- `review-log.json`: corrections, kept separate from original generation.

The local full report is retained privately for reproducibility; selected public evidence contains only the relevant audience comment. The public sample remains a static interactive demonstration and does not run Gemini for visitors.

[Try the updated sample](https://gtm-campaign-sample.netlify.app/).
