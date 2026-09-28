from pathlib import Path

base = Path(__file__).parent
folder = base / "search_files"
folder.mkdir(exist_ok=True)

texts = [
    "Python is useful for data analysis.",
    "Mathematics is important in data science.",
    "Probability theory is useful.",
    "SQL is used with databases.",
    "Python and probability theory are used in projects."
]

for i, text in enumerate(texts, 1):
    with open(folder / f"file{i}.txt", "w", encoding="utf-8") as f:
        f.write(text)

query = input("search: ").lower()
found = []

for path in folder.glob("*.txt"):
    with open(path, "r", encoding="utf-8") as f:
        if query in f.read().lower():
            found.append(path.name)

if found:
    for name in found:
        print(name)
else:
    print("not found")
