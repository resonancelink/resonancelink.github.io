# English edition

Translation snapshot: September 14, 2026.

The English edition includes the home page and visitor guide, all 13 Atlas of Consciousness entries, all 12 Law of Attraction Lab entries, all 67 Guidance answers across 12 categories, all 77 oracle cards, the Soul Compass, and all 18 questions and six result types in Discover What You Love. Questions, answers, reflection prompts, result descriptions, and navigation are translated.

## Sources and behavior

The Japanese collections are maintained in this repository. The oracle, soul, and interests apps were translated from the user's separate source projects. Their English editions are served here under `/en/michiyo_oraclecards/`, `/en/tamashii_shindan/`, and `/en/suki_shindan/`. The original Japanese app repositories remain their own projects. Oracle artwork is reused from `/michiyo_oraclecards/images/`; its visible card titles are already English.

Question order, answer weights, result keys, numerology calculations, and tie handling retain the Japanese behavior. Soul quiz ties can be resolved randomly, as in the original app. These experiences offer spiritual reflection, not medical or psychological diagnosis.

## Maintenance

- Update Japanese and English content together. English data is a manually maintained translation, not automatic live translation.
- `home-content.js` contains six translated teasers. Preserve each original one-based entry number used in `#no-XX` links.
- The existing `scripts/update_weekly.py` updates only the Japanese home page. Translate the selected newsletter title and description separately for the English home page.
- `portal-nav.js` in this directory provides English navigation; the root shared navigation provides English links from the Japanese apps.
- Each English page has English metadata and Japanese/English alternate links. Per-app manifests launch the corresponding English route.
- Preview with an HTTP server rooted at the repository. Opening HTML files directly does not reproduce root-relative paths.
- Newsletter articles, videos, books, external services, installation instructions, and the dream experience announcement retain their Japanese destinations, identified where linked. This edition does not translate third-party websites.

Brand/course names are working translations; Japanese book titles are romanized where no official English edition was established. Guidance source dates and identifiers are preserved, with translated titles. Support information links to the provider's multilingual service page instead of implying that Japanese-only support details apply to English readers.

Validation covered complete content counts, script syntax, internal links, 821 calculation comparisons against the original logic, and browser flows through the actual question and result screens. Publication uses the existing GitHub Pages configuration; no domain or hosting setting change is required.
