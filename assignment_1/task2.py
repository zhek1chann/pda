from pathlib import Path

base = Path(__file__).parent
folder = base / "search_files"

query = input().lower()
found = []

for path in sorted(folder.glob("*.txt")):
    with open(path, "r", encoding="utf-8") as f:
        if query in f.read().lower():
            found.append(path.name)

if found:
    for name in found:
        print(name)
else:
    print("В данных файлах отсутствует поисковый запрос.")
