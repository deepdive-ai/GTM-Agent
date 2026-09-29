# GTM Agent

A general-purpose AI content agent designed to turn reference material and a campaign brief into audience-specific content, review it, and return drafts with source references. The planned design supports different businesses, industries, and topics through campaign-specific inputs.

**Current stage:** Initial source documents and campaign configuration prepared for the first example, with reusable content and research guardrails documented. The reusable agent and ingestion pipeline are not implemented yet.

**Last progress update:** 29 September 2026.

## Problem and proposed solution

Creating useful content requires reliable information about the subject, a clear audience, and an objective. Generic drafts can miss a brand's voice, lose source attribution, or make unsupported claims. These challenges apply to product launches, educational content, service promotions, and other campaigns across industries.

GTM Agent will retrieve relevant material from a campaign's knowledge base, draft content for the specified audience, and use a review subagent to check factual grounding and campaign alignment. Keratoconus content for Nexus Vision Speciality Eye Care is the first example used to develop and evaluate this workflow. Healthcare is one use case, not the scope of the core agent.

## Scope and campaign configuration

The core workflow will handle retrieval, planning, drafting, review, revision, and output saving. Business and domain details will come from campaign inputs rather than being hard-coded into the agent.

| Input | What changes between campaigns |
| --- | --- |
| Campaign brief | Topic, business, audience, goal, formats, language, tone, and call to action |
| Reference documents | Product facts, service details, research, FAQs, or other relevant evidence |
| Brand guidance | Voice, terminology, preferred wording, and style rules |
| Domain guidance | Additional checks appropriate to the subject, such as medical claim review for healthcare |

For example, a software launch could supply product documentation and signup goals; an education business could supply course details and an enrolment objective. The intended workflow stays the same. When implemented, each campaign's retrieval context should be isolated to avoid mixing facts or brand details between businesses.

The initial output formats are **LinkedIn posts, blog articles, and Google Business Profile posts**. Supporting more topics and supporting more formats are separate capabilities. Video scripts and video generation are being explored as future extensions, not implemented features. Scheduling, publishing, and performance tracking are outside the initial generation-and-review scope.

To prepare another campaign, supply its own brief, source documents, and guidance. An operational campaign-selection interface will be added during implementation; the repository currently contains only the first example's inputs.

## First example campaign: Nexus Vision

| Field | Decision |
| --- | --- |
| Topic | Keratoconus |
| Content formats | LinkedIn posts, blog articles, Google Business Profile posts |
| Audience | Patients |
| Clinic | Nexus Vision Speciality Eye Care |
| Location | Padmarao Nagar, Secunderabad, Hyderabad |
| Goal | Encourage patients to visit the clinic |
| Call to action | Book an appointment: call +91 8247710054 |
| Language | English |
| Tone | Warm and reassuring |
| Writing preference | Do not use em dashes in generated content |

Campaign timing and advertising service area are still to be selected. The clinic's location does not automatically define the advertising audience.

## Implementation status

| Component | Status | Evidence or next action |
| --- | --- | --- |
| First example: subject references | Prepared | Six cited keratoconus topic files |
| First example: business profile | Prepared | Website-sourced Nexus Vision location, contact details, and services |
| Campaign brief and editorial guidance | Prepared | Audience, formats, goal, CTA, language, tone, and writing rules recorded |
| Document chunking check | Verified locally | Current documents checked with the reference splitter settings; see progress log |
| Shared factual guardrails | Documented | [Content and research guardrails](guidelines/factual_guardrails.md); runtime enforcement is not implemented |
| Application and campaign configuration | Not implemented | Create project structure, dependencies, and reusable campaign inputs |
| Ingestion, embeddings, and retrieval | Not implemented | Add loading, source metadata, and vector search |
| Main agent and review subagent | Not implemented | Add drafting, review, revision, and saving |
| Demo interface and evaluation | Not implemented | Build and test a complete campaign-generation run |

## Planned architecture

```text
Campaign brief + sources + brand/domain guidance
                  |
          Load and chunk documents
                  |
       Embed and store in Pinecone
                  |
     Main agent retrieves and drafts
                  |
       Review subagent checks draft
                  |
     Revise and save with source references
                  |
              Human review
```

Planned stack: Python, Deep Agents, LangChain/LangGraph, Hugging Face embeddings, Pinecone, and Streamlit. These integrations are not installed or implemented in this repository yet.

Source URLs should be carried in chunk metadata and exposed during retrieval. Required editorial rules should be included in the instructions for the selected campaign, so their application does not depend on a guidance document being retrieved. Shared checks will cover source support, audience fit, format, tone, and CTA. Domain-specific checks, including clinical review for medical content, will apply only where relevant.

## Current repository contents

| Location | Contents |
| --- | --- |
| [Shared guardrails](guidelines/factual_guardrails.md) | Reusable factual, research, evidence, and publication rules for every campaign |
| [data/raw/products/](data/raw/products/) | Six medical topic summaries and the Nexus Vision clinic profile |
| [Campaign brief](data/raw/campaigns/keratoconus_campaign_brief.md) | User-selected campaign decisions |
| [Editorial guidance](data/raw/campaigns/keratoconus_editorial_guidance.md) | Factual, tone-related, and writing constraints |

The `products` folder is a document-category convention inherited from the intended ingestion structure. It holds subject and service references; keratoconus is a medical condition.

Medical summaries cite Mayo Clinic, Moorfields Eye Hospital, and AAO EyeWiki. Clinic details come from the clinic's own website. These are starter references and have not received clinical review. They do not support invented prices, credentials, treatment guarantees, or claims that every procedure is available at the clinic.

## Daily progress

### 29 September 2026: Factual guardrails defined

**Completed**

- Saved [reusable content and research guardrails](guidelines/factual_guardrails.md) for all industries and formats.
- Defined how to flag missing details and evidence, ask focused questions, and resolve or remove unsupported claims before publication.
- Added rules against invented metrics and customer claims, and separated factual claims from suggestions.
- Required evidence for trend and performance claims, original content, source traceability, campaign alignment, privacy, and human approval.

**Validation and next work**

- Checked that the note explicitly covers missing evidence and includes all 12 agreed rules.
- Documentation only: these rules are not yet enforced by a working agent. Niche research and performance analysis are not implemented.
- Next: include the shared guardrails in drafting and review instructions when implementing the agent.

### 28 September 2026: General-purpose scope clarified

**Completed**

- Updated the project description and problem statement to cover content across industries and topics.
- Documented the separation between the reusable agent, campaign inputs, brand guidance, and domain-specific review rules.
- Kept Nexus Vision as the first example and clarified the three initial formats and future video exploration.
- Generalized the planned evaluation criteria and retained example-specific checks.

**Validation and next work**

- Documentation-only update. This does not add working agent capabilities or establish performance on other domains.
- Next: implement reusable campaign configuration and document ingestion, then test retrieval before adding drafting and review.


### 27 September 2026: Scope and knowledge-base preparation

**Completed**

- Created the public repository and defined the first patient campaign.
- Prepared six medical topic files, each with its source citation.
- Added the clinic profile, campaign brief, and separate editorial guidance.
- Confirmed English, a warm and reassuring tone, the phone CTA, and the no-em-dashes rule.
- Selected LinkedIn posts, blog articles, and Google Business Profile posts as the initial output formats.

**Validation and findings**

- Inspected the reference application's loader and chunker. Its recursive character splitter uses a 1,000-character limit and 150-character overlap, without special handling for Markdown citations.
- Found that the initial combined document separated an eye-rubbing passage from its citation.
- Reorganized the material into short files. Local checks with the same splitter settings confirmed that each current ingestion document stays in one chunk, with medical citations attached.
- No embedding, Pinecone ingestion, retrieval, or agent-generation run has been completed. The chunking check is not an end-to-end application test.

**Next work**

1. Create the Python application structure and configuration.
2. Implement document loading and preserve source attribution through chunking.
3. Add embeddings and retrieval, then inspect returned evidence before connecting the agent.

**Open decisions**

- Select campaign timing and advertising service area.
- Choose the model/provider and configure the development environment and Pinecone namespace.

Future daily entries should record the work completed, verification results, remaining issues, and next actions under the actual date. Preserve earlier entries; record planned work as planned rather than completed.

## Running the project

There is no runnable application yet. Setup commands and a demo walkthrough will be added when the implementation has been tested. API keys and `.env` files must remain outside this public repository.

## Planned evaluation criteria

- Use the selected campaign's sources and settings without leaking information from another campaign.
- Generate the requested initial formats with the configured audience, language, tone, and CTA.
- Preserve source references, flag unsupported claims, and apply brand and relevant domain rules.
- Save drafts and review notes for human approval before publication.
- Test a second, nonmedical campaign to demonstrate that the workflow can change topics without changing core agent logic. This test has not been run.

For the Nexus Vision example, additionally check patient-appropriate wording, English, a warm and reassuring tone, the correct phone CTA, and the no-em-dashes rule. Medical content requires clinical review before publication.
