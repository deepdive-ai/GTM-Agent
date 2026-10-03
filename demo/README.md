# Interactive campaign sample

[Try the public sample](https://gtm-campaign-sample.netlify.app/)

A browser-based guided sample of the GTM workflow, using saved Nexus Vision research and outputs from 2 October 2026. No installation, account or API key is needed. This static sample is separate from the Python Streamlit app; it does not run fresh collection, AI generation or indexed RAG.

Visitors choose one of three directions, inspect selected audience comments and source passages, then review a saved draft or download an evidence request. The supported direction provides saved LinkedIn, blog and Google Business Profile outputs. Editing the selected facts disables reuse of a saved draft. Clinical-review-pending status and the blog's unsupported sentence remain visible.

Feedback is kept in the browser tab and can be downloaded with interaction notes. There is no automatic transmission or central analytics. A real volunteer must report their experience before claiming independent user testing.

## Run locally

```sh
python3 -m http.server 8080 --directory demo
```

From a repository checkout, open http://localhost:8080/. The public deployment serves the same index.html and sample.json.

## Verification on 3 October 2026

Developer browser testing confirmed topic selection, source expansion, review confirmation, changed-fact blocking, all three formats, the blog warning, missing-evidence routing and downloadable JSON for notes, evidence requests, reviewed briefs and the saved blog. All sample factual excerpts were checked against the source catalog; JavaScript syntax validation passed. This is not independent user testing or a clinical accuracy evaluation.
