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
2. Keeps videos with English audio-language metadata and a category-topic match. AI agents and automation and AI podcasts require a high-signal AI topic match in the title, so incidental mentions do not qualify.
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

## Daily automation and publishing

GitHub Actions runs once daily at 10:00 UTC. That time falls on the same `America/New_York` calendar date in both standard and daylight time, so each successful run produces one date-stamped daily snapshot. A manual `workflow_dispatch` run forces an immediate refresh of all seven categories.

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
