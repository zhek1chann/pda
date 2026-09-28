from pathlib import Path
import re

base = Path(__file__).parent

with open(base / "words.txt", "r", encoding="utf-8") as f:
    text = f.read()

with open(base / "forbidden_words.txt", "r", encoding="utf-8") as f:
    forbidden = f.read().split()

for word in forbidden:
    text = re.sub(
        re.escape(word),
        "*" * len(word),
        text,
        flags=re.IGNORECASE
    )

print(text)
