from pathlib import Path

mapping = Path("mapping.txt")

s = ""
for n in mapping.read_text().splitlines():
    s += f"{n}::{Path(f'{n}.mp3')}\n"

# -2 gets rid of last newline
mapping.write_text(s[:-1])
