from pathlib import Path

path = Path(__file__).parent / "file.txt"

with open(path, "r", encoding="utf-8") as f:
    text = f.read()

letters = 0
for char in text:
    if "A" <= char <= "Z" or "a" <= char <= "z":
        letters += 1
words = len(text.split())
lines = len(text.splitlines())

print("latin letters:", letters)
print("words:", words)
print("lines:", lines)
