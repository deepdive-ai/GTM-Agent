# GTM Content Agent: Quick Run Guide

A repeatable process from a campaign brief to a reviewed, saved content package. Generating or saving a package does not publish it.

## Before you start

Open the local Streamlit app using the [setup instructions](../social_listening/README.md). Expand the sidebar with the top-left arrow if necessary. Enter your Gemini key in **Gemini API key (session only)** and press Enter. Keep keys out of documents, exports and Git. Generation depends on your account's quota.

## Run steps

1. **Enter your brief.** Choose **I already have a topic** for the simplest demonstration. A brief means the instructions entered in the app's fields: business, target audience, campaign goal, content formats, call to action, language and tone. No separate brief document is required. For example: a Hyderabad coworking business; small teams; workspace enquiries; “Book a workspace tour”; English; a warm, practical tone.

2. **Add source documents.** Upload UTF-8 Markdown or text files with the facts your content can use, including original-source links and relevant qualifications. Set **Source review status** accurately. Assistant-prepared summaries are not automatically business-approved. When reopening a campaign, use its saved documents.

3. **Retrieve and check evidence.** Enter the research question and choose keyword or hybrid search. Inspect the retrieved passages. **Claim checkpoint: do they actually support the question, including limits, dates and exceptions?** If evidence is missing, add sources or narrow the question. Check the passage-review box only after reviewing them.

4. **Generate and review the topic.** Click **Generate source-grounded topics**. Compare the proposed statements with their cited excerpts. **Claim checkpoint: remove unsupported statements and check that company-specific facts have not become general claims.** Review the title, select the statements to use, add editorial direction if needed, and confirm that you reviewed the topic scope. Editorial direction does not supply new factual evidence.

5. **Generate the package.** Under **Create a campaign package**, explicitly select the required formats, then click **Generate campaign package**. Check this selection even if you selected formats in the brief. Each format receives a source-support review and up to two automatic revisions. Inspect blocked results; use a review-resume control when offered, or address the evidence/scope problem before retrying. For a quota error, follow the displayed retry guidance rather than repeatedly clicking Generate.

6. **Review each draft.** Open each format's tab, its sources and review notes, and its automatic review history. **Claim checkpoint: compare every factual claim with its citation, especially prices, availability, benefits and outcomes.** Check the CTA, tone and any platform warnings. Accept or reject each draft separately. Automated checks establish neither independent truth nor business approval; regulated content may require specialist review. A blocked or withheld draft is not ready to publish.

7. **Save and export.** Enter a **Campaign name** and click **Save campaign**. Save again after review decisions or changes. This retains the brief, sources, drafts and review history locally, without API keys. Download the Markdown package and JSON audit if needed. The audit retains failed attempts; blocked or withheld draft text may be excluded from the Markdown package. Reopen through **Saved campaigns → Local campaigns → Open campaign**. Save current work before opening another campaign.

## A demonstration in a few minutes

Reopen a prepared campaign and show the brief, one retrieved passage, one draft claim beside its citation, the review result, and the saved package. Clearly identify saved outputs as a replay. A fresh run follows the same steps, but API response times, revisions and quota limits make its duration variable.

**Finished when:** the campaign is saved, each format's review status is visible, and factual claims can be traced to their supporting excerpts. Saving is not publication or proof that every claim is correct.
