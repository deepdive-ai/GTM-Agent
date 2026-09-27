# GTM Agent

An AI content-generation project designed to turn verified reference material and a campaign brief into audience-specific marketing drafts, review them, and return content with source references.

**Current stage:** Knowledge-base preparation completed. Agent implementation is next.

**Last progress update:** 27 September 2026.

## Problem and proposed solution

Creating patient-facing content requires both reliable medical information and a clear campaign objective. Generic drafts can miss the intended audience, lose source attribution, or make unsupported claims.

GTM Agent will retrieve relevant material from a curated knowledge base, draft content for the specified audience, and use a review subagent to check factual grounding and campaign alignment. The first use case is a keratoconus patient campaign for Nexus Vision Speciality Eye Care.

## First campaign

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
| Medical references | Prepared | Six cited keratoconus topic files |
| Clinic reference | Prepared | Website-sourced location, contact details, and services |
| Campaign brief and editorial guidance | Prepared | Audience, formats, goal, CTA, language, tone, and writing rules recorded |
| Document chunking check | Verified locally | Current documents checked with the reference splitter settings; see progress log |
| Application and configuration | Not implemented | Create project structure and dependency configuration |
| Ingestion, embeddings, and retrieval | Not implemented | Add loading, source metadata, and vector search |
| Main agent and review subagent | Not implemented | Add drafting, review, revision, and saving |
| Demo interface and evaluation | Not implemented | Build and test a complete campaign-generation run |

## Planned architecture

```text
Reference documents + campaign brief
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

Source URLs should be carried in chunk metadata and exposed during retrieval. Required editorial rules should also be included in the agent instructions, so their application does not depend on a guidance document being retrieved.

## Repository contents

| Location | Contents |
| --- | --- |
| [data/raw/products/](data/raw/products/) | Six medical topic summaries and the Nexus Vision clinic profile |
| [Campaign brief](data/raw/campaigns/keratoconus_campaign_brief.md) | User-selected campaign decisions |
| [Editorial guidance](data/raw/campaigns/keratoconus_editorial_guidance.md) | Factual, tone-related, and writing constraints |

The `products` folder is a document-category convention inherited from the intended ingestion structure. It holds subject and service references; keratoconus is a medical condition.

Medical summaries cite Mayo Clinic, Moorfields Eye Hospital, and AAO EyeWiki. Clinic details come from the clinic's own website. These are starter references and have not received clinical review. They do not support invented prices, credentials, treatment guarantees, or claims that every procedure is available at the clinic.

## Daily progress

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

## Planned demo success criteria

- Retrieve relevant evidence for a patient-facing keratoconus request.
- Generate LinkedIn posts, blog articles, and Google Business Profile posts in English with a warm, reassuring tone and the appropriate appointment CTA for each channel.
- Preserve source references and avoid unsupported clinical or clinic-specific claims.
- Apply the no-em-dashes rule and have the review subagent flag violations.
- Save the draft and review notes for human approval before publication.
