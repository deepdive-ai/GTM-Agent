# Audience Listening Lab

Local social listening prototype for GTM Agent. Searches YouTube, collects a bounded sample of recent top-level comments, uses Gemini to interpret multilingual comments, and exposes the original evidence for review. Basic keyword grouping remains available as a comparison.

## Run

From this folder:

```sh
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py --server.address 127.0.0.1
```

Choose **Explore synthetic demo** to test the interface without an API key. All demo comments are invented and clearly labelled.

For live collection, create a Google Cloud project, enable YouTube Data API v3, and create an API key restricted to that API. Enter it in the masked sidebar field, or set YOUTUBE_API_KEY in your local environment. Do not commit keys or paste them into chat. An API key is required even within Google's free quota.

Official setup: https://developers.google.com/youtube/v3/getting-started

## AI analysis

Open a saved collection, enter a separate Gemini API key in the masked sidebar field, and click **Analyze audience signals**. The YouTube key collects data; the Gemini key analyzes it. Do not collect again just to analyze an existing run.

On that click, topic, comment text/IDs, and video titles are sent to Google Gemini. No author profiles or YouTube credentials are sent. Gemini account availability, quota and pricing apply; use within a free tier depends on your account. Keys stay in session memory, never reports or SQLite.

The default model is gemini-2.5-flash; the model field supports another compatible generateContent model. The response uses structured JSON. Every comment must be classified as relevant, irrelevant or uncertain with an English interpretation and reason. Relevant comments support themes, suggestions, and requests for missing business evidence. The app rejects unknown evidence IDs and computes counts and links from the original records. These checks validate traceability, not semantic accuracy.

Analysis is capped at 100 comments and 150,000 serialized input characters per run. There is no silent truncation. AI analysis is held in the current session and included in the evidence JSON download. Changing the source report clears stale analysis. Saved collection history does not retain AI results yet.

Verification: mocked transport and Streamlit UI tests pass. Live Gemini interpretation and browser JSON download verified on 1 October 2026 using the existing 35-comment sample. The final run classified 18 comments as relevant and 17 as irrelevant, producing four themes. Counts and evidence IDs passed validation. It captured per-eye pricing, wear duration, gym use, bubbles and replacement. This is a single-sample check, not an accuracy benchmark. Remaining limitation: the model expanded the ambiguous phrase "45" to "presumably 45,000"; reviewers must not use that as a verified price. The real sample to evaluate contains 35 comments across five videos. Check that the model captures questions about per-eye pricing, wear duration, gym use, bubbles and replacement, while separating unrelated prescription/surgery questions. The expected concerns are a human evaluation checklist, not prewritten model outputs.

## Scope and limits

- Up to ten videos and 100 recent top-level comments per video per run. No replies or exhaustive search.
- Each run uses one search request, one video-details request, and at most one comment request per video. Check the project's current quota in Google Cloud.
- Publication window applies to videos; English is a search relevance hint. No verified geographic targeting or audience identification.
- AI relevance, language interpretation and theme suggestions require human review. Theme counts use distinct comment IDs, with distinct text counts also exported. Counts are not unique people. The optional keyword comparison uses exact-text deduplication.
- Reports never imply that engagement proves bookings, that a theme is trending, or that a patient comment is a medical fact.
- SQLite stores runs locally. Prior comment IDs for the exact query identify newly observed comments, not popularity changes. Snapshots older than 29 days are removed on database access. Manage downloaded exports separately.
- AI interpretations and supporting IDs are included in JSON downloads.
- Synthetic demo data never enters live collection history.
- No publishing, scheduling, or account-wide monitoring. AI analysis may incur Gemini charges depending on your account.

Before commercial distribution, review current YouTube API policies, data retention, and permitted analytics for the intended product. This prototype has not been validated as a production integration.

## Verification

```sh
python3 -m unittest discover -s . -p 'test_*.py'
```

Tests use mocked API responses; a live API collection requires your key.
