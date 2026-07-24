"""Generate a small, realistic citizen-complaints dataset for the demo.

Produces:
  * citizen_complaints.csv   (~350 rows over ~8 weeks)
  * citizen_complaints.json  (same data, JSON records)

The data is seeded so trends and one clear anomaly are reproducible:
  * "Koramangala" is a persistent hotspot.
  * "Waste Collection" spikes hard in the final week (the planted anomaly).

Areas are real Bengaluru ward names (exact keys in bengaluru_wards.py) so the
hotspot map shows real BBMP ward locations out of the box instead of the
placeholder fallback -- a fictional place name like the old "Riverside" never
matches a real ward, which meant the map's headline feature never actually
demonstrated itself on the bundled demo dataset.
"""

from __future__ import annotations

import json
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)

AREAS = [
    "Koramangala", "Jayanagar", "Malleshwaram", "Basavanagudi",
    "Rajajinagar", "BTM Layout", "Domlur", "Vijayanagar",
]
CATEGORY_TYPES = {
    "Waste Collection": ["Missed pickup", "Overflowing bin", "Illegal dumping", "Delayed collection"],
    "Water Supply": ["Low pressure", "Leak", "Contaminated water", "No supply"],
    "Roads": ["Pothole", "Broken streetlight", "Damaged signage", "Blocked drain"],
    "Sanitation": ["Blocked sewer", "Public toilet issue", "Stagnant water", "Foul smell"],
    "Noise": ["Loud construction", "Late-night party", "Traffic noise", "Industrial noise"],
    "Public Health": ["Mosquito breeding", "Stray animals", "Food safety", "Open garbage"],
}
CATEGORY_DEPT = {
    "Waste Collection": "Sanitation Dept",
    "Water Supply": "Water Board",
    "Roads": "Public Works",
    "Sanitation": "Sanitation Dept",
    "Noise": "Environment Cell",
    "Public Health": "Health Dept",
}
SEVERITIES = ["low", "medium", "high", "critical"]
SEVERITY_WEIGHTS = [0.35, 0.4, 0.2, 0.05]
STATUSES = ["Open", "In Progress", "Resolved", "Escalated"]
STATUS_WEIGHTS = [0.35, 0.25, 0.35, 0.05]

NOTES = [
    "Resident reported repeatedly this month.",
    "Third complaint from the same street.",
    "Flagged by community volunteer.",
    "Escalated after no response in 72 hours.",
    "Photo evidence attached by citizen.",
    "Affects a school zone nearby.",
    "Recurring issue during monsoon.",
    "Reported via city helpline.",
    "",
]

WEEKS = 8
START = date.today() - timedelta(weeks=WEEKS)


def weighted_area() -> str:
    # Koramangala is a persistent hotspot.
    weights = [3 if a == "Koramangala" else 1 for a in AREAS]
    return random.choices(AREAS, weights=weights, k=1)[0]


def make_rows() -> list[dict]:
    rows: list[dict] = []
    for week in range(WEEKS):
        # Base volume rises slightly week over week.
        base = 30 + week * 3
        for _ in range(base):
            day = START + timedelta(weeks=week, days=random.randint(0, 6))
            category = random.choice(list(CATEGORY_TYPES))
            rows.append(_row(day, category))

        # Planted anomaly: Waste Collection surge in Koramangala in the last week.
        if week == WEEKS - 1:
            for _ in range(45):
                day = START + timedelta(weeks=week, days=random.randint(0, 6))
                rows.append(_row(day, "Waste Collection", area="Koramangala", severity="high"))

    random.shuffle(rows)
    return rows


def _row(day: date, category: str, area: str | None = None, severity: str | None = None) -> dict:
    complaint = random.choice(CATEGORY_TYPES[category])
    return {
        "date": day.isoformat(),
        "area": area or weighted_area(),
        "category": category,
        "complaint_type": complaint,
        "severity": severity or random.choices(SEVERITIES, weights=SEVERITY_WEIGHTS, k=1)[0],
        "status": random.choices(STATUSES, weights=STATUS_WEIGHTS, k=1)[0],
        "department": CATEGORY_DEPT[category],
        "notes": random.choice(NOTES),
    }


def main() -> None:
    out_dir = Path(__file__).parent
    rows = make_rows()

    # CSV
    import csv

    fields = ["date", "area", "category", "complaint_type", "severity", "status", "department", "notes"]
    csv_path = out_dir / "citizen_complaints.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    # JSON
    json_path = out_dir / "citizen_complaints.json"
    json_path.write_text(json.dumps({"records": rows}, indent=2), encoding="utf-8")

    print(f"Wrote {len(rows)} rows to {csv_path.name} and {json_path.name}")


if __name__ == "__main__":
    main()
