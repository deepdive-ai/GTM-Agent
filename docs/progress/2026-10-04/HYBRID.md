# Hybrid retrieval and question-scope checks

Implemented on 4 October 2026. Keyword BM25 remains the default. Select **Hybrid (experimental, local semantic + keyword)** in Streamlit to try the new method.

## What changed

- Optional local FastEmbed all-MiniLM-L6-v2 embeddings supply semantic candidates alongside BM25. Reciprocal rank fusion combines rankings; semantic similarity breaks fusion ties. A provisional cosine cutoff of 0.35 excludes weak semantic candidates. No paid embedding API or hosted vector database is used.
- Local model weights download once (roughly 90 MB). Document vectors are request-local. Only the public embedding model is cached. Documents are not transmitted for retrieval; subsequent Gemini planning still sends reviewed evidence as before.
- The UI names the applied question with “Results updated for” and identifies the active method. Method changes invalidate reviewed evidence and previous plans.
- Removed contradictory instructions permitting background-topic substitution. Exactly one topic is allowed. A second Gemini request checks the title, rationale, statements and missing-evidence questions for scope drift. Failed or invalid reviews block acceptance. This adds a Gemini call and can consume additional quota.

## Measured results

| Evaluation | BM25 expected document found | Hybrid expected document found |
| --- | --- | --- |
| Original nine answerable questions | 7/9 | 9/9 |
| Six additional answerable questions | 5/6 | 6/6 |

In each successful case the expected document ranked first, measured by its first occurrence among up to six passages. This is a document-level metric, not proof the first passage answers the full question. The final tie-break also moves the actual lifespan explanation above the source-citation passage for the tested lens-lifespan question.

Hybrid recovered the original spreadsheet/download and yearly/monthly payment paraphrases. The additional set was written after implementation without tuning the model or cutoff to its outcomes. All tested unrelated controls returned no matches. Price, warranty and refund questions still retrieved background material without containing the requested answer. Similarity is not evidence sufficiency.

The collections are nine existing medical summaries and three explicitly synthetic software documents. This small hand-labelled evaluation is not an independent benchmark, clinical validation, real nonmedical customer test or general accuracy estimate.

## Live scope test and remaining limits

Asked about Nexus Vision's lens price and warranty using hybrid retrieval. The first scope-review version accepted one missing-evidence topic but overlooked an extra insurance request. That UI result is retained in `hybrid-scope-first-attempt.txt`.

After tightening both instructions to cover scope expansion in evidence requests, the next live planner response again added insurance. The separate scope check rejected it and the app accepted no brief. See `hybrid-scope-rejected.txt` and the screenshot. This verifies the rejection path on an actual model response. It does not prove the generator now always stays in scope or that every scope check is correct. A failed check currently requires retrying; there is no automatic repair loop.

57 automated tests passed. Model and semantic responses in unit tests are mocked. The comparison JSON files use the actual downloaded embedding model; the UI rejection is a live Gemini result. Positive acceptance of a focused missing-evidence response is covered by mocked tests, not a new successful live example in this follow-up.

The English encoder has a 256-token limit per passage and may truncate token-dense chunks for embeddings; BM25 and generation still receive the complete stored passage. Cross-language performance is untested. Source quality and semantic factual support still need review. No campaign content was published and Netlify remains unchanged.

## Reproduce

From the repository root:

```sh
python -m pip install -r social_listening/requirements-hybrid.txt
python social_listening/evaluate_retrieval.py docs/progress/2026-10-04/sources /tmp/hybrid.json --mode hybrid
python social_listening/evaluate_retrieval.py docs/progress/2026-10-04/sources /tmp/held-out.json --mode hybrid --held-out
python -m unittest discover -s social_listening -p 'test_*.py'
```

Use `--mode bm25` for the baseline. Synthetic software upload files are available in `synthetic-software/` for separate manual retrieval tests.
