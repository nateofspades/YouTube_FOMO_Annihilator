# YouTube FOMO Annihilator

## Live leaderboard

https://nateofspades.github.io/YouTube_FOMO_Annihilator

An independent, automated daily leaderboard of the top 10 YouTube videos from curated channels. Results are available for Artificial intelligence, Emerging businesses & startups, Science & future technology, and Software & developer tools.

## Using the site

The live site has one leaderboard page with two filters:

- Category — choose one of the four curated channel categories.
- Date — open the calendar icon or date field to choose a published leaderboard date.

The newest published date is selected by default. The calendar makes unavailable dates non-selectable: dates before the first publication are crossed out, and dates after the current date are greyed out. Every result row remains on one line without horizontal scrolling or truncated text. The table includes:

- Rank
- YouTube Video — linked to the video on YouTube
- Channel
- Length — rounded to the nearest minute
- Views — current public YouTube view count

## Ranking method

For each category, the automation:

1. Reviews videos from the maintained curated channel universe that were published in the preceding seven days.
2. Keeps videos with English audio-language metadata and a category-topic match in their title, description, or tags.
3. Sorts qualifying videos by current public YouTube Data API v3 `viewCount`.
4. Publishes the top 10 as date-stamped JSON for the site’s Category and Date filters.

This project ranks qualifying videos from its curated channels; it does not claim to rank every relevant video on YouTube.

## Categories and sources

- Artificial intelligence
- Emerging businesses & startups
- Science & future technology
- Software & developer tools

The Artificial intelligence source universe is maintained in `config/channels.json`. The other category universes, along with their source types, are maintained in `config/categories.json`.

## Daily automation and publishing

GitHub Actions runs daily at midnight in `America/New_York`. To handle daylight-saving time, the workflow is scheduled at both 04:00 and 05:00 UTC; the application only proceeds during the matching New York midnight hour. A manual `workflow_dispatch` run forces an immediate refresh of all four categories.

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

## Data source and API key security

Automation uses the YouTube Data API v3. The `YOUTUBE_API_KEY` GitHub Actions repository secret is not committed to the repository. Restrict the key to the YouTube Data API v3; it should not rely on GitHub-hosted runner IP-address restrictions.

## Independence and trademark notice

This is an independent, unofficial project. It is not affiliated with, sponsored by, endorsed by, or approved by YouTube, Google LLC, or any listed channel. The project does not represent YouTube, Google, or any of their products or services.

“YouTube” is used only to identify the third-party platform and API used by the project. YouTube is a trademark of Google LLC. Video titles, thumbnails, channel names, and other third-party content remain the property of their respective owners.
