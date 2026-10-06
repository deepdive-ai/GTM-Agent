### 6 October 2026: Saved campaigns and successful review resumption

Added local campaign saving and reopening with documents, inputs, drafts, prior runs and per-format decisions. API key fields and executable graph objects are excluded from snapshots. Interrupted claim checks can resume on an existing draft; already checked drafts can resume human approval without another model request.

**Live verified:** Reopened Nexus Vision and resumed the Blog and Google Business Profile checks using Gemini. Both passed with unchanged draft text and unchanged attempt counts (2 and 1 respectively). Blog reviewed 9 units; Google Business Profile reviewed 7. LinkedIn had already passed. All three await human review and medical content still needs clinical approval. Earlier failures remain in the audit.

**Validation:** 93 automated tests pass, including fresh-session reopening, credential exclusion, session-key retention, stale-save protection and review resumption. Automated model responses are mocked. The two resumed checks above were live Gemini calls.

[Public evidence and saved drafts](https://gtm-campaign-sample.netlify.app/progress-oct6) · [Audit and screenshots](docs/progress/2026-10-06/)

Next: test a new non-medical business with its own source documents, audience and campaign goal, then independent user testing. Campaign storage is local, not cloud sync. Public pages display saved outputs, not hosted generation.

