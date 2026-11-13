# makefun-coolest-art

An entry for make.fun's bounty [Make the coolest art](https://make.fun/bounty/coolest-art-01).

## What it does

`main.py` (Python 3.13, standard library only) writes one image, `entry.png`, to
`/output/entry.png` (or to `$MAKEFUN_OUTPUT_DIR` when set). The picture is drawn ahead of time
by the scripts in `tools/` (flat shapes rasterised with Pillow at 4x supersampling, a fixed-seed
paper grain, then reduced to a palette PNG) and committed; `main.py` copies those exact bytes,
so both of the grader's runs write the same file in well under a second.

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

To redraw the picture (needs numpy and Pillow, used only by the tools, never by the entry):

```
python tools/switch.py entry.png
```
