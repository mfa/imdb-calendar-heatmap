import csv
import math
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

TITLE_TYPE_COLORS = {
    "TV Episode": "#4f46e5",  # indigo
    "Movie": "#16a34a",       # green
    "TV Series": "#ea580c",   # orange
    "Short": "#0d9488",       # teal
}

TYPE_MAPPING = {
    "TV Movie": "Movie",
    "TV Mini Series": "TV Series",
    "TV Short": "Short",
    "TV Special": "TV Series",
    "Video": None,
    "Video Game": None,
}

DEFAULT_COLOR = "#64748b"


def hex_to_rgb(hex_color: str) -> tuple[float, float, float]:
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16) / 255
    g = int(hex_color[2:4], 16) / 255
    b = int(hex_color[4:6], 16) / 255
    return (r, g, b)


def rgb_to_hex(rgb: tuple[float, float, float]) -> str:
    return "#{:02x}{:02x}{:02x}".format(
        int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)
    )


def blend_colors(colors: list[str]) -> str:
    if len(colors) == 1:
        return colors[0]
    rgb_values = [hex_to_rgb(c) for c in colors]
    avg_r = sum(c[0] for c in rgb_values) / len(rgb_values)
    avg_g = sum(c[1] for c in rgb_values) / len(rgb_values)
    avg_b = sum(c[2] for c in rgb_values) / len(rgb_values)
    return rgb_to_hex((avg_r, avg_g, avg_b))


def load_imdb_ratings(csv_path: Path) -> list[dict]:
    ratings = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            date_str = row.get("Date Rated", "")
            title_type = row.get("Title Type", "")
            if date_str and title_type:
                mapped_type = TYPE_MAPPING.get(title_type, title_type)
                if mapped_type is None:
                    continue
                try:
                    date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    ratings.append({"date": date, "title_type": mapped_type})
                except ValueError:
                    continue
    return ratings


def aggregate_by_date(ratings: list[dict]) -> dict:
    by_date: dict = defaultdict(lambda: {"count": 0, "types": set()})
    for r in ratings:
        by_date[r["date"]]["count"] += 1
        by_date[r["date"]]["types"].add(r["title_type"])
    return dict(by_date)


def get_color_for_date(types: set[str]) -> str:
    colors = [TITLE_TYPE_COLORS.get(t, DEFAULT_COLOR) for t in types]
    return blend_colors(colors)


def create_calendar_heatmap(
    ratings_by_date: dict,
    year: int,
    output_path: Path,
    max_count: int,
) -> None:
    year_data = {d: v for d, v in ratings_by_date.items() if d.year == year}

    # Layout: 53 weeks (columns) x 7 days (rows), Sunday at top
    cell_size = 1.0
    gap = 0.15

    fig, ax = plt.subplots(figsize=(12, 2.5))

    start_date = datetime(year, 1, 1).date()
    end_date = datetime(year, 12, 31).date()

    start_weekday = start_date.weekday()
    start_weekday_sun = (start_weekday + 1) % 7  # Convert to Sunday=0

    year_types = set()
    current_date = start_date

    while current_date <= end_date:
        day_of_year = (current_date - start_date).days
        weekday = current_date.weekday()
        row = (weekday + 1) % 7  # Sunday=0 at top

        total_days_from_visual_start = day_of_year + start_weekday_sun
        col = total_days_from_visual_start // 7

        x = col * (cell_size + gap)
        y = (6 - row) * (cell_size + gap)

        if current_date in year_data:
            data = year_data[current_date]
            year_types.update(data["types"])
            base_color = get_color_for_date(data["types"])
            intensity = min(math.log1p(data["count"]) / math.log1p(max_count), 1.0)
            intensity = max(0.4, intensity)
            bg_rgb = hex_to_rgb("#ebedf0")
            color_rgb = hex_to_rgb(base_color)
            final_rgb = tuple(
                bg_rgb[i] * (1 - intensity) + color_rgb[i] * intensity
                for i in range(3)
            )
            facecolor = final_rgb
        else:
            facecolor = "#ebedf0"

        rect = Rectangle(
            (x, y), cell_size, cell_size,
            facecolor=facecolor,
            edgecolor="white",
            linewidth=0.5
        )
        ax.add_patch(rect)
        current_date += timedelta(days=1)

    total_weeks = 53
    ax.set_xlim(-gap, total_weeks * (cell_size + gap))
    ax.set_ylim(-gap, 7 * (cell_size + gap))
    ax.set_aspect("equal")
    ax.axis("off")

    # Month labels
    month_positions = {}
    current_date = start_date
    while current_date <= end_date:
        if current_date.day == 1 or current_date == start_date:
            day_of_year = (current_date - start_date).days
            total_days_from_visual_start = day_of_year + start_weekday_sun
            col = total_days_from_visual_start // 7
            month_name = current_date.strftime("%b")
            if month_name not in month_positions:
                month_positions[month_name] = col * (cell_size + gap)
        current_date += timedelta(days=1)

    for month, x_pos in month_positions.items():
        ax.text(x_pos, 7 * (cell_size + gap) + 0.3, month, fontsize=9, va="bottom")

    # Day labels (every other day)
    day_labels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    for i, label in enumerate(day_labels):
        if i % 2 == 1:
            y = (6 - i) * (cell_size + gap) + cell_size / 2
            ax.text(-0.8, y, label, fontsize=8, va="center", ha="right")

    legend_elements = []
    for title_type in sorted(year_types):
        color = TITLE_TYPE_COLORS.get(title_type, DEFAULT_COLOR)
        legend_elements.append(
            plt.Rectangle((0, 0), 1, 1, facecolor=color, label=title_type)
        )

    ax.legend(
        handles=legend_elements,
        loc="upper left",
        bbox_to_anchor=(1.01, 1),
        fontsize=8,
        frameon=False,
    )

    plt.tight_layout()
    fig.savefig(output_path, dpi=100, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main():
    personal_dir = Path(__file__).parent / "personal"
    csv_files = list(personal_dir.glob("*.csv"))

    if not csv_files:
        print("No CSV file found in personal folder")
        return

    csv_path = csv_files[0]
    print(f"Loading ratings from: {csv_path}")

    ratings = load_imdb_ratings(csv_path)
    print(f"Loaded {len(ratings)} ratings")

    ratings_by_date = aggregate_by_date(ratings)
    print(f"Aggregated to {len(ratings_by_date)} unique dates")

    max_count = max(d["count"] for d in ratings_by_date.values()) if ratings_by_date else 1
    print(f"Max ratings per day: {max_count}")

    years = sorted(set(d.year for d in ratings_by_date.keys()), reverse=True)
    print(f"Years: {min(years)} - {max(years)}")

    output_dir = personal_dir / "calendar_heatmaps"
    output_dir.mkdir(exist_ok=True)

    for year in years:
        output_path = output_dir / f"imdb_ratings_{year}.png"
        create_calendar_heatmap(ratings_by_date, year, output_path, max_count)
        print(f"Generated: {output_path}")

    md_path = personal_dir / "calendar_heatmaps" / "ratings_overview.md"
    with open(md_path, "w") as f:
        f.write("# IMDB Ratings Calendar Heatmaps\n\n")

        f.write("## Color Legend\n\n")
        f.write("| Title Type | Color |\n")
        f.write("|------------|-------|\n")
        for title_type, color in sorted(TITLE_TYPE_COLORS.items()):
            f.write(f"| {title_type} | {color} |\n")
        f.write("\n")
        f.write("*Color intensity indicates number of ratings per day. ")
        f.write("Mixed colors appear when multiple title types are rated on the same day.*\n\n")

        f.write("## Yearly Overview\n\n")
        for year in years:
            f.write(f"### {year}\n\n")
            f.write(f"![IMDB Ratings {year}](imdb_ratings_{year}.png)\n\n")

    print(f"Generated markdown: {md_path}")
    print("Done!")


if __name__ == "__main__":
    main()
