from pathlib import Path
import csv
import re

BASE_DIR = Path(__file__).resolve().parent.parent
BATCH = "25"
RESULT_DIR = BASE_DIR / "Result" / BATCH


def get_semester_files() -> list[tuple[int, Path]]:
    files = []
    for path in RESULT_DIR.glob("*.csv"):
        match = re.search(r"Sem_(\d+)_Result", path.name)
        if match:
            semester = int(match.group(1))
            files.append((semester, path))
    files.sort(key=lambda item: item[0])
    return files


def normalize_roll(roll: str) -> str:
    roll = (roll or "").strip().upper()
    if len(roll) < 3:
        return roll
    return f"{roll[:2]}{roll[2]}{roll[-3:]}"


def load_semester(file_path: Path) -> dict:
    data = {}
    with file_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            roll = (row.get("roll") or "").strip()
            if not roll:
                continue
            try:
                cg = float((row.get("cg") or "").strip())
            except ValueError:
                continue

            key = normalize_roll(roll)
            data[key] = {
                "roll": roll,
                "name": (row.get("name") or "").strip(),
                "branch": (row.get("branch") or "").strip(),
                "cg": cg,
            }
    return data


def calculate_cgpa() -> list[dict]:
    semester_files = get_semester_files()
    if not semester_files:
        raise FileNotFoundError(f"No semester CSV files found in {RESULT_DIR}")

    semester_data = [load_semester(path) for _, path in semester_files]
    all_keys = set().union(*(data.keys() for data in semester_data))

    results = []
    for key in sorted(all_keys):
        entries = [data.get(key) for data in semester_data]
        present_entries = [entry for entry in entries if entry]
        if not present_entries:
            continue

        cgs = [entry["cg"] for entry in present_entries]
        cgpa = round(sum(cgs) / len(cgs), 2)

        first_entry = present_entries[0]
        row = {
            "roll": first_entry["roll"],
            "name": first_entry["name"],
            "branch": first_entry["branch"],
            "cgpa": cgpa,
        }

        for idx, (semester, _) in enumerate(semester_files):
            entry = semester_data[idx].get(key)
            row[f"sem{semester}_cg"] = entry["cg"] if entry else ""

        results.append(row)

    results.sort(key=lambda x: (-x["cgpa"], x["name"], x["roll"]))

    output_path = RESULT_DIR / f"{BATCH}_CGPA_Result.csv"
    with output_path.open("w", encoding="utf-8", newline="") as f:
        fieldnames = ["roll", "name", "branch"] + [f"sem{semester}_cg" for semester, _ in semester_files] + ["cgpa"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"Saved {len(results)} students to {output_path}")
    return results


if __name__ == "__main__":
    calculate_cgpa()
