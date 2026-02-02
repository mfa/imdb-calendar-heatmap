# IMDB Calendar Heatmaps

Generate GitHub-style calendar heatmaps from IMDB ratings exports.

Blog post: <https://madflex.de/personal-imdb-calendar-heatmaps>

## Usage

1. Export your ratings from IMDB and place the CSV in `personal/`
2. Run:

```bash
uv run python plot.py
```

Output is saved to `personal/calendar_heatmaps/`.
