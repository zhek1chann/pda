from pathlib import Path
import re

path = Path(__file__).parent / "file.txt"

with open(path, "r", encoding="utf-8") as f:
    text = f.read()

letters = len(re.findall(r"[A-Za-z]", text))
words = len(text.split())
lines = len(text.splitlines())

print("latin letters:", letters)
print("words:", words)
print("lines:", lines)
