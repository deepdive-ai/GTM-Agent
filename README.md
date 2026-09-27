# GTM Agent

A planned go-to-market content agent that uses supplied reference material and a campaign brief to draft, review, and refine content.

Keratoconus education is the first use case. The first campaign targets patients, aims to encourage visits to an eye clinic, and uses the call to action **Book an appointment**. The clinic is Nexus Vision Speciality Eye Care in Padmarao Nagar, Secunderabad, Hyderabad. The user-selected booking channel is **Call +91 8247710054**. Campaign language is **English**, with a **warm and reassuring** tone. Advertising geography and other creative preferences remain to be selected.

## Project status

**Preparation stage:** this repository currently contains source documents, a campaign brief, and editorial guidance. The agent, ingestion pipeline, review subagent, command-line interface, and Streamlit interface have not been implemented here. The architecture below is planned, not a description of working features.

## Planned workflow

1. Read reference documents and a user-defined campaign brief.
2. Clean and split documents into chunks while preserving source attribution.
3. Embed and store the chunks in a searchable knowledge base.
4. Retrieve relevant evidence for the requested topic and audience.
5. Draft a campaign brief and requested formats, such as social posts, email, blogs, and ads.
6. Delegate checks of factual grounding, tone, completeness, and unsupported claims to a review subagent.
7. Revise and save drafts with source references for human review.

The reference implementation uses Deep Agents, LangChain/LangGraph, Hugging Face embeddings, Pinecone, and Streamlit. We plan to follow that structure and add explicit source-URL metadata. Automated review will support, not replace, clinical review for medical campaigns.

## Repository structure

```text
data/raw/
  products/
    keratoconus_condition_and_symptoms.md
    keratoconus_causes_and_progression.md
    keratoconus_diagnosis_and_treatment_goals.md
    keratoconus_vision_correction_and_monitoring.md
    keratoconus_cross_linking_expectations.md
    keratoconus_eye_rubbing.md
    nexus_vision_clinic_profile.md
  campaigns/
    keratoconus_editorial_guidance.md
    keratoconus_campaign_brief.md
```

The `products` folder follows the reference project's document-type convention; it holds subject reference material and does not mean keratoconus is a product. Campaign guidance is stored separately from medical facts. The [campaign brief](data/raw/campaigns/keratoconus_campaign_brief.md) records the user-selected audience, goal, and call to action, along with outstanding details.

## Keratoconus source material

The six topic files contain paraphrased summaries with source URLs from Mayo Clinic, Moorfields Eye Hospital, and AAO EyeWiki. Compiled on 27 September 2026, they are starter references, not exhaustive medical guidance or clinician-approved copy. They do not establish local treatment availability, clinic services, prices, or regulatory approvals. The separate [clinic profile](data/raw/products/nexus_vision_clinic_profile.md) records website-listed contact details and services, distinguishing clinic claims from medical evidence.

Each topic file is shorter than the reference chunker's 1,000-character limit. Because that implementation splits each file independently, the complete topic and its citation remain together under the tested settings. Markdown headings alone do not enforce chunk boundaries. Longer future documents will require another check and source metadata support.

## Setup and ingestion

There are no runnable agent commands in this repository yet. To try these documents with the original application:

1. Set up the reference repository according to its README.
2. Copy the topic files and campaign guidance into the matching `data/raw` folders.
3. Supply a campaign brief with audience, geography, objective, tone, service details where relevant, and call to action.
4. Use a separate configured knowledge-base namespace and a source directory containing only the intended campaign documents to avoid mixing unrelated demo material.
5. Run the reference application's ingestion command and inspect its saved chunks before generating drafts.

When building this agent, preserve source URLs, titles, and review dates as chunk metadata and expose them to the drafting and review agents. The reference loader currently treats source URLs as document text rather than extracting them into metadata. Editorial guidance retrieved from the knowledge base is also not guaranteed to appear in every request; required rules should be included in the agent's instructions when implemented.

## Next milestones

- Choose the campaign formats, timing, and advertising service area.
- Implement loading, chunking, embedding, retrieval, and source attribution.
- Add the main agent, review subagent, and output saving.
- Add configuration and runnable CLI/UI instructions after validation.

Keep API keys, `.env` files, and private patient information out of this public repository.
