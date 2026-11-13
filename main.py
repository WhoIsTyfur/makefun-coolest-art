"""make.fun coolest-art-01 entry: write the finished piece to /output/entry.png.

The picture is drawn ahead of time by the scripts in tools/ and committed as entry.png;
this program only copies those bytes, so every run writes the identical file."""
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output")
out_dir.mkdir(parents=True, exist_ok=True)
data = (HERE / "entry.png").read_bytes()
(out_dir / "entry.png").write_bytes(data)
print(f"wrote {len(data)} bytes to {out_dir / 'entry.png'}", file=sys.stderr)
