# Retrieval evaluation: 4 October 2026

Ran 15 hand-labelled queries against two isolated document collections: nine existing medical summaries and three explicitly synthetic TaskNest software documents. The synthetic fixture is test data, not a real client or user validation.

## Results

Of nine answerable queries, seven returned the expected document within six passages, and all seven ranked it first. This small convenience sample is diagnostic, not a general accuracy percentage.

All five answerable medical queries found the expected document, including “When should I change my lenses?” and “How long will my lenses last?” Two of four software queries succeeded. The two failures returned no passages:

- “Can I download my work as a spreadsheet?” missed the CSV task-export instructions.
- “How can I pay yearly instead of every month?” missed the monthly-to-annual billing instructions.

Four deliberately unanswerable price, warranty or refund queries returned background documents. Those documents do not establish the requested business facts. This evaluation's missing-answer labels are hand-authored judgments, not an automated semantic sufficiency check. The unrelated orchid query and the medical query against only software documents returned no matches.

All 48 existing automated tests still pass. Their model responses are mocked; they do not establish live Gemini abstention accuracy.

## Decision

The failures justify evaluating hybrid keyword and semantic retrieval. Do not add hardcoded lens/software synonym rules to pass these examples. Compare the same labelled cases and additional held-out questions before replacing the current retriever. Keep no-match blocking and human evidence review. Improving retrieval alone will not solve unsupported claims.

Reproduce from the repository root:

```sh
python social_listening/evaluate_retrieval.py docs/progress/2026-10-04/sources /tmp/retrieval-evaluation.json
```

[Detailed results and synthetic fixtures](expanded-retrieval-evaluation.json).

## Live Gemini missing-evidence test

Asked: “What is the price and warranty for scleral lenses at Nexus Vision?” with the campaign goal explicitly requiring missing-evidence handling. The first attempt returned HTTP 503. One retry succeeded.

Gemini did not invent a price or warranty. Its pricing topic had no supported statements, was labelled “Needs source evidence,” and requested pricing and warranty details. However, it also proposed a separate general lifespan/replacement topic and introduced insurance into the pricing topic. The missing-fact behavior passed this example; adherence to the selected question failed. This is not a clean overall pass. No content draft was generated for this test.

Next implementation work should address question-scope drift alongside hybrid retrieval. A more capable retriever alone cannot prevent the planner answering a different question.

The visible result is saved in `missing-evidence-live-ui.txt` and `missing-evidence-live.jpg`. This is UI evidence, not a downloaded structured API response. The nonmedical evaluation tests retrieval only; it is not a live nonmedical generation test.

These evaluation additions are saved locally. GitHub was not updated in this follow-up because the connection attempt failed.
