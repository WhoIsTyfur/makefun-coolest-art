# makefun-coolest-art

An entry for make.fun's bounty [Make the coolest art](https://make.fun/bounty/coolest-art-01).

## What it does

`main.py` (Python 3.13, standard library only) writes one image, `entry.png`, to
`/output/entry.png` (or to `$MAKEFUN_OUTPUT_DIR` when set). It checks the bytes first (a PNG, at
most 1 MiB and 1024 x 1024, complete through its IEND chunk), then copies them, so both of the
grader's runs write the identical file in well under a second.

The picture is drawn ahead of time by Python in `tools/` and committed:

- `tools/comp.py`: a small compositing kit. Shapes are rasterised by Pillow at 4x and reduced to
  anti-aliased masks; colour is mixed in float RGB with gradients, FFT Gaussian glows, embossed
  relief and a fixed-seed print grain; the result is saved as a 256-colour palette PNG.
- `tools/coin.py`: the current piece (see below).
- `tools/switch.py`, `tools/torch.py`, `tools/rug.py`, `tools/bulb.py`, `tools/gallery.py`
  (2D) and `tools/scene.py` (Blender 4.5, Cycles on the CPU) are the other concepts it was
  chosen from.

The current piece: at dusk the setting sun is a giant gold coin sliding into a coin slot cut in
the horizon, a bank's night deposit; a tiny banker stands on its rim.

## How it is scored

A sealed scorer checks the file (PNG or JPEG, at most 1 MiB and 1024 x 1024, complete). Valid
entries are then judged in pairs by an AI judge, each pair asked in both orders, on: does it stop
you, is the idea fresh, is the style bold and coherent, is the craft clean, and does it still
read at 300 pixels wide. Entries rank by Bradley-Terry win rate over a Swiss heat plus a playoff
of the top 22.

## Run it locally

```
mkdir out
MAKEFUN_OUTPUT_DIR=out python main.py
```

To redraw the picture (numpy and Pillow are needed by the tools only, never by the entry):

```
python tools/coin.py entry.png
```

`coin.py` takes optional variant knobs from the environment (`COIN_R`, `COIN_HZ`, `COIN_STARS`,
`COIN_RAYS`, `COIN_FIG`); with none set it draws the committed piece.
