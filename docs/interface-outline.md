# GTM Content Agent: Lightweight interface outline

Chosen interface: **Streamlit**, a browser-based interface for entering a campaign brief, generating drafts and reviewing evidence.

This is the intended interface outline. The existing prototype already supports campaign work; the clearer starting screen below is planned, not yet implemented.

## What the user sees first

**Create content grounded in your sources.**

Two starting choices: **Start a new campaign** or **Open a saved campaign**. A sample brief explains what to enter. API setup belongs in a clearly labelled settings area with masked fields.

## One-page flow

**Input → Generate → Review → Save / Export**

| Area | User actions and visible results |
| --- | --- |
| **1. Input** | Enter business, target audience, campaign goal, language, tone and call to action. Add source documents and an audience question, or select a question from collected audience insights. Choose content formats. |
| **2. Generate** | Retrieve relevant source passages, inspect suggested topics and approve the scope. Click **Generate drafts**. Display progress through drafting and automated checks, with clear error and retry messages. |
| **3. Review** | Show the original question beside each draft. Expand supporting excerpts and inspect flagged claims. Keep the direct answer separate from supplementary advice. Accept or reject each draft. |
| **4. Output** | Save the campaign and download drafts with sources and review status. Clearly distinguish drafts awaiting review from accepted drafts. Nothing is automatically published. |

## Where the user checks claims

Before generation, review the proposed statements and their evidence. After generation, compare each paragraph with its cited excerpts, inspect automated findings, and check for unsupported implications or topic drift before accepting it. No matching evidence means no generation request is sent. Automated checks do not establish source truth or replace clinical approval for medical content. Keep any pending-review notice beside the call to action.

## Demonstration scope

Use a prepared brief and source set to demonstrate input, generation, review and saving. Live generation depends on provider availability; saved outputs can demonstrate the review interface but must be labelled as saved examples.
