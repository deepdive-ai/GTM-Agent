# 5 October 2026 progress

LangGraph now coordinates retrieval/planning and drafting, source-support review, at most two revisions and a user-review pause. Direct-topic mode works without audience research. Campaign packages have individual format statuses, approvals, retries and exportable prior-run history.

## Verified and incomplete results

- 88 automated tests pass; model responses in tests are mocked.
- A separate live single-blog run rejected unsupported wording, automatically revised it and passed its second check. No manual text edits were applied. User acceptance and clinical review remain pending.
- The direct-topic campaign package is incomplete: LinkedIn passed, while Blog and Google Business Profile reviews hit HTTP 429. A small diagnostic confirmed daily quota exhaustion for the configured model. The blog had first been automatically rewritten after an uncited introduction. Blocked drafts are excluded from reviewable Markdown and retained in the audit.
- The reviewer can overflag wording or miss errors. It checks draft source support, not independent truth or every research interpretation. Session checkpoints are not durable across restarts.

## Inspect

[Public evidence page](https://gtm-campaign-sample.netlify.app/progress-oct5)

- [Automatic correction audit](automatic-review-oct5.json)
- [Campaign audit and earlier attempts](campaign-audit-oct5.json)
- [Reviewable campaign package](campaign-package-oct5.md)
- [Test summary](tests-oct5.txt)
- [Automatic review screenshot](workflow-oct5.jpg)
- [Campaign package screenshot](campaign-oct5.jpg)
- [Daily quota diagnosis screenshot](quota-oct5.jpg)

No campaign posts were published. These are saved development results, not a live public AI service. The October 4 sample retains its original manual-review history. Next: complete quota-blocked live reviews, durable campaign storage, independent user testing and broader nonmedical evaluation.
