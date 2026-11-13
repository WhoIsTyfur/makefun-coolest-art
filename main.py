"""make.fun coolest-art-01 entry: write the finished piece to /output/entry.png.

The picture is drawn ahead of time by the scripts in tools/ and committed as entry.png;
this program only copies those bytes, so every run writes the identical file."""
import os
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAX_BYTES = 1048576
MAX_SIDE = 1024

data = (HERE / "entry.png").read_bytes()

# Guard the gate's rules before writing: a PNG, within 1 MiB and 1024 x 1024.
if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
    sys.exit("entry.png is not a PNG")
width, height = struct.unpack(">II", data[16:24])
if len(data) > MAX_BYTES or width > MAX_SIDE or height > MAX_SIDE:
    sys.exit(f"entry.png breaks the limits: {len(data)} bytes, {width}x{height}")
if not data.endswith(b"IEND\xaeB`\x82"):
    sys.exit("entry.png is truncated")

out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output")
out_dir.mkdir(parents=True, exist_ok=True)
(out_dir / "entry.png").write_bytes(data)
print(f"wrote {len(data)} bytes ({width}x{height}) to {out_dir / 'entry.png'}", file=sys.stderr)
