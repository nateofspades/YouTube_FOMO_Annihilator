# YouTube FOMO Annihilator

An independent automated set of daily top-10 leaderboards for recently published English-language videos from curated YouTube channel universes. Each leaderboard ranks qualifying videos by current public YouTube `viewCount` within its category; it does not claim to rank every relevant video on YouTube.

## Categories

- [Artificial intelligence](https://nateofspades.github.io/YouTube_FOMO_Annihilator/)
- Emerging businesses and startups
- Science and future technology
- Software and developer tools

The three additional category source universes and their source types are versioned in `config/categories.json`. The existing AI universe remains in `config/channels.json`.

## Daily automation

The GitHub Actions workflow runs the AI leaderboard and all three additional categories every day at midnight `America/New_York`. GitHub Actions schedules are best effort: the workflow schedules both 04:00 and 05:00 UTC to cover daylight saving time, and the program accepts only the target New York local hour. `workflow_dispatch` runs all four leaderboards immediately.

Each update:

1. Reviews videos from the maintained curated source universe published in the preceding seven days.
2. Keeps videos with English audio language metadata and a category-topic match in title, description, or tags.
3. Ranks qualifying videos by current public YouTube API `viewCount`.
4. Publishes date-stamped JSON to GitHub Pages. The site’s Date filter defaults to the newest published date and can show earlier dates on the same page.

Results show each video’s channel and length rounded to the nearest minute.

## Data source

Automation uses the YouTube Data API v3. `YOUTUBE_API_KEY` is a GitHub Actions repository secret and is never committed. The API key should be restricted to YouTube Data API v3 rather than GitHub-hosted runner IP addresses.

## Independence and trademark notice

This is an independent, unofficial project. It is not affiliated with, sponsored by, endorsed by, or approved by YouTube, Google LLC, or any channel listed above. The project does not represent YouTube, Google, or any of their products or services.

“YouTube” is used only to identify the third-party platform and API used by the project. YouTube is a trademark of Google LLC. All video titles, thumbnails, channel names, and other third-party content remain the property of their respective owners.
