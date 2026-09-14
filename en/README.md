# English edition — initial implementation

Source review and translation snapshot: September 13, 2026.

This initial edition translates the home page (`/en/`) and the introduction guide (`/en/start/`). It preserves the Japanese site's water effects, artwork, main sections, and outbound destinations. Article collections and interactive apps are currently in Japanese; their English entry points state this.

## Files and maintenance

- `index.html`: English home page, profile, news, app introductions, and the 28 translated `KOTOBA` reflections. `WEEKLY` contains a manually translated newsletter issue. Update its title, episode, and URL when selecting another issue.
- `home-content.js`: six translated teaser labels. Each `number` is the original Japanese collection's one-based entry number, used in `#no-XX` deep links. Keep the original numbers when editing or replacing teasers. This file is not automatically synchronized with the Japanese data arrays.
- `start/index.html`: English visitor guide, with its own navigation and styles.
- `english.css`: layout adjustments for English text and mobile displays.
- `language-switch.css`: language selector used by the English home and both Japanese entry pages.
- `site.webmanifest`: English app name and `/en/` launch URL/scope; original icons are reused.

The existing `scripts/update_weekly.py` updates the Japanese home page only. Do not run it against the English page: it fetches Japanese titles. Update the English newsletter text and the Japanese source together as an editorial task. The English navigation deliberately says “Newsletter”, without implying automated weekly translation.

The Japanese home and start page have reciprocal `canonical`/`hreflang` metadata and visible language links. English pages likewise have `lang="en"`, translated metadata, and Japanese/English alternatives. Shared resources use root-relative paths. Preview using an HTTP server with the repository root as document root, rather than opening an HTML file directly.

## Remaining translation work

- Atlas of Consciousness: page UI and 13 entries.
- Law of Attraction Lab: page UI and 12 entries.
- Michiyo’s Guidance: page UI, 12 categories, 67 questions and answers, prompts, and source references.
- Home-screen installation instructions and dream experience announcement.
- Shared portal navigation for the remaining pages and apps.
- Oracle, soul, and interests apps: sources are not present in this repository.

English names such as “Spiritual Metascience Institute”, “House of the Soul”, and “Soul Independence” are working translations. Confirm preferred brand/course names during editorial review. Book references keep romanized Japanese titles, because official English editions were not established.

No deployment, Git commit/push, domain change, or GitHub Pages setting change is part of this implementation.
