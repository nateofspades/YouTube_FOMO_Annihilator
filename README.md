# YouTube FOMO Annihilator

## Page with ranked results

https://nateofspades.github.io/YouTube_FOMO_Annihilator

## What the above page offers

An independent, automated daily leaderboard of the top-10 YouTube videos from selected YouTube channels for each of the following categories:

- AI news
- AI agents and automation
- AI podcasts
- Business podcasts
- Emerging businesses & startups
- Science & future technology
- Software & developer tools

## Using the site

The live site has one leaderboard page with two filters:

- Category
- Date

The newest published date is selected by default. The earliest date for which results are available is September 26, 2026. The table includes:

- Rank
- YouTube Video
- YouTube Channel
- Length
- Views

## Ranking method

For each category, the automation:

1. Reviews videos from the selected YouTube channels that were published in the preceding 7 days.
2. Keeps videos with English audio-language metadata and a category-topic match. AI agents and automation and AI podcasts first require a high-signal AI topic match in the title. If fewer than 10 videos qualify, the automation broadens that category’s matching rule to title, description, and tags so the published list can reach 10 when enough relevant videos exist.
3. Sorts qualifying videos by current public YouTube Data API v3 `viewCount`.
4. Publishes the top-10 as date-stamped JSON for the site’s Category and Date filters.

This project ranks qualifying videos from the selected YouTube channels; it does not claim to rank every relevant video on YouTube.

## Categories and sources

- AI news
- AI agents and automation
- AI podcasts
- Business podcasts
- Emerging businesses & startups
- Science & future technology
- Software & developer tools

The list of channels used for the AI news category is in config/channels.json. The lists for the other six categories are in config/categories.json.

Channel expansions are additive: existing entries are retained. New sources use verified stable channel IDs. Where a requested podcast is a show within a broader channel, `playlist_sources` restricts collection to its verified official show playlist rather than including the owner's unrelated uploads. Show playlists are scanned completely because their ordering need not follow video publication dates; the same 7-day eligibility window and ranking rules still apply.

The requested-source inventory in config/source-expansion.json records each requested addition as added, already present, or pending verification. Pending sources are not collected and are not silently replaced with similarly named channels.

## Daily automation and publishing

GitHub Actions targets 04:00 every day in `America/New_York`, starting October 25, 2026. The workflow uses GitHub's native schedule `timezone` support, so the target remains 4:00 a.m. local time in both EDT and EST (08:00 UTC during daylight time, 09:00 UTC during standard time). Scheduling is best-effort: GitHub can delay or drop a scheduled run, so an exact start or completion time is not guaranteed. Scheduled runs are idempotent: after all seven categories have that New York date's top-10 snapshot, another scheduled attempt does not recollect. A manual `workflow_dispatch` run forces an immediate refresh of all seven categories. The previous daytime UTC triggers have been removed.

An independent Hermes watchdog runs at 22:30 UTC. It verifies that every category has a valid date-stamped JSON file with exactly 10 results. If anything is missing, it dispatches the GitHub workflow, waits for it to finish, and verifies the result again. If recovery fails, it opens one GitHub issue for that date. This removes reliance on GitHub's best-effort schedule alone, but fresh data still depends on the YouTube API, GitHub availability, and the watchdog service.

Every successful run:

1. Runs the unit tests.
2. Collects and ranks videos.
3. Commits updated data under `docs/data/` when it changed.
4. Deploys the site to GitHub Pages.

The workflow definition is `.github/workflows/update-leaderboard.yml`.

## Local development

Run the test suite:

```sh
python3 -m unittest discover -s tests -v
```

Serve the published site locally:

```sh
python3 -m http.server 8765 --directory docs
```

Then open `http://127.0.0.1:8765/`.

## Data source

Automation uses the YouTube Data API v3.

## Independence and trademark notice

This is an independent, unofficial project. It is not affiliated with, sponsored by, endorsed by, or approved by YouTube, Google LLC, or any listed channel. The project does not represent YouTube, Google, or any of their products or services.

“YouTube” is used only to identify the third-party platform and API used by the project. YouTube is a trademark of Google LLC. Video titles, thumbnails, channel names, and other third-party content remain the property of their respective owners.
