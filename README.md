# YouTube FOMO Annihilator

An independent, automated leaderboard for recently published English-language AI videos. Each daily update is intended to identify the ten qualifying videos with the highest public YouTube `viewCount` among a curated set of AI-focused channels.

## Status

Project setup is in progress. Automation and the GitHub Pages dashboard have not yet been deployed.

## Planned ranking rules

At 6:00 a.m. in the `America/New_York` time zone, the project will:

1. Review videos from the approved channel universe that were published in the preceding seven days.
2. Keep videos whose YouTube language metadata identifies English audio and that satisfy the project's AI-topic criteria.
3. Rank qualifying videos by the current public YouTube API `viewCount` value, from highest to lowest.
4. Publish the top ten and a timestamped historical record to GitHub Pages.

The resulting leaderboard will be described accurately as the top ten qualifying videos from the curated channel universe; it does not claim to rank every AI video on YouTube.

## Initial channel universe

| # | Channel |
| --- | --- |
| 1 | [AI Explained](https://www.youtube.com/@aiexplained-official) |
| 2 | [Matt Wolfe](https://www.youtube.com/@mreflow) |
| 3 | [TheAIGRID](https://www.youtube.com/@TheAiGrid) |
| 4 | [WorldofAI](https://www.youtube.com/@intheworldofai) |
| 5 | [All About AI](https://www.youtube.com/@AllAboutAI) |
| 6 | [The AI Advantage](https://www.youtube.com/@aiadvantage) |
| 7 | [Aitrepreneur](https://www.youtube.com/@aitrepreneur) |
| 8 | [Two Minute Papers](https://www.youtube.com/@TwoMinutePapers) |
| 9 | [Google DeepMind](https://www.youtube.com/@googledeepmind) |
| 10 | [OpenAI](https://www.youtube.com/@openai) |
| 11 | [Anthropic](https://www.youtube.com/@anthropic-ai) |
| 12 | [Hugging Face](https://www.youtube.com/@HuggingFace) |

This list is a versioned editorial input to the project and may be reviewed or updated as the project evolves.

## Data source

The planned automation will use the YouTube Data API v3. An API key will be stored only as a GitHub Actions repository secret and will never be committed to this repository.

## Independence and trademark notice

This is an independent, unofficial project. It is not affiliated with, sponsored by, endorsed by, or approved by YouTube, Google LLC, or any channel listed above. The project does not represent YouTube, Google, or any of their products or services.

“YouTube” is used only to identify the third-party platform and API used by the project. YouTube is a trademark of Google LLC. All video titles, thumbnails, channel names, and other third-party content remain the property of their respective owners.

## License

A license will be selected before the first production release.
