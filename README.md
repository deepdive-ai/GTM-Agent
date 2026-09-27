# GTM Agent

Source material for creating keratoconus educational content with a GTM agent.

## Source document

- [Keratoconus source material](data/raw/products/keratoconus_source_material.md): paraphrased factual summaries with citations to Mayo Clinic, Moorfields Eye Hospital, and the American Academy of Ophthalmology's EyeWiki.

The document was compiled on 27 September 2026. It contains summaries and links, not full copies of the referenced publications. It has not received clinical review.

## How to use

The folder structure matches the source-document conventions of [The Gen Academy's GTM agent](https://github.com/The-Gen-Academy/3D-GTM-Agent). This repository currently stores source material; it does not contain the agent application.

1. Copy `data/raw/products/keratoconus_source_material.md` into the corresponding folder in your agent project.
2. Create a separate campaign brief under `data/raw/campaigns/` specifying the target audience, geography, goal, tone, and call to action. These have not yet been selected.
3. Ingest the documents into your configured knowledge base, keeping unrelated demo material separate.
4. Generate a draft and obtain clinical review before publishing medical content.

The `products` folder holds subject reference material for compatibility with the original agent; keratoconus is a medical condition, not a product.

Do not commit API keys, `.env` files, or private patient information.
