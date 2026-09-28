from pathlib import Path
from datetime import datetime
import csv
import json
import shutil

base = Path(__file__).parent
project = base / "project"
data_dir = project / "data"
results_dir = project / "results"

data_dir.mkdir(parents=True, exist_ok=True)
results_dir.mkdir(parents=True, exist_ok=True)

students_file = data_dir / "students.csv"
shutil.copy(base / "students.csv", students_file)

result = []

with open(students_file, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        grades = [
            int(row["math"]),
            int(row["physics"]),
            int(row["cs"]),
            int(row["history"]),
            int(row["english"])
        ]

        result.append({
            "full_name": row["full_name"],
            "group": row["group"],
            "average_grade": round(sum(grades) / len(grades), 2)
        })

report = results_dir / "report.json"

if report.exists():
    answer = input("report.json exists. overwrite? (yes/no): ").lower()
else:
    answer = "yes"

if answer == "yes":
    with open(report, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

archive = base / "results.zip"

if archive.exists():
    archive.unlink()

shutil.make_archive(
    str(base / "results"),
    "zip",
    root_dir=project,
    base_dir="results"
)

if report.exists():
    info = report.stat()
    print("size:", info.st_size)
    print("modified:", datetime.fromtimestamp(info.st_mtime))
