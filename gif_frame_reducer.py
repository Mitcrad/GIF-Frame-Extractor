#!/usr/bin/env python3
"""Reduce GIF frame count while preserving the animation's overall timing.

Example:
    python gif_frame_reducer.py input.gif --every 4
    python gif_frame_reducer.py input.gif --max-frames 120
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Iterator

from PIL import Image, ImageSequence


def mb(size: int) -> str:
    return f"{size / 1024 / 1024:.2f} MB"


def default_output_path(source: Path) -> Path:
    return source.with_name(f"{source.stem}_reduced.gif")


def frame_durations(source: Path, every: int) -> list[int]:
    """Sum each dropped-frame group into the duration of its kept frame."""
    durations: list[int] = []
    with Image.open(source) as gif:
        for index, frame in enumerate(ImageSequence.Iterator(gif)):
            duration = int(frame.info.get("duration", 100))
            # GIF delay is stored in centiseconds; zero-delay frames are common,
            # but 10 ms is friendlier to decoders that ignore zero delays.
            duration = max(duration, 10)
            group = index // every
            if group == len(durations):
                durations.append(duration)
            else:
                durations[group] += duration
    return durations


def kept_frames(source: Path, every: int) -> Iterator[Image.Image]:
    """Yield composited RGBA frames without holding the entire animation in RAM."""
    with Image.open(source) as gif:
        for index, frame in enumerate(ImageSequence.Iterator(gif)):
            if index % every == 0:
                # copy() detaches the image from the source file before the next seek.
                yield frame.convert("RGBA").copy()


def reduce_gif(source: Path, output: Path, every: int) -> tuple[int, int, int]:
    with Image.open(source) as gif:
        total_frames = getattr(gif, "n_frames", 1)
        loop = int(gif.info.get("loop", 0))

    durations = frame_durations(source, every)
    frames = kept_frames(source, every)
    try:
        first = next(frames)
    except StopIteration as error:
        raise ValueError("GIF 中没有可处理的帧。") from error

    # optimize=True stores only changed regions where possible.  A generator is
    # used for later frames so very large GIFs do not need all frames in memory.
    first.save(
        output,
        format="GIF",
        save_all=True,
        append_images=frames,
        duration=durations,
        loop=loop,
        disposal=2,
        optimize=True,
    )
    return total_frames, len(durations), output.stat().st_size


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="通过抽帧缩小 GIF，播放总时长保持不变。"
    )
    parser.add_argument("input", type=Path, help="原 GIF 文件路径")
    parser.add_argument("-o", "--output", type=Path, help="输出 GIF 路径")
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument(
        "--every", type=int, metavar="N", help="每 N 帧保留 1 帧（例如 4）"
    )
    choice.add_argument(
        "--max-frames", type=int, metavar="N", help="最多保留 N 帧，自动计算抽帧间隔"
    )
    parser.add_argument("--overwrite", action="store_true", help="允许覆盖已有输出文件")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.input.expanduser().resolve()
    if not source.is_file():
        print(f"找不到输入文件：{source}", file=sys.stderr)
        return 2
    if source.suffix.lower() != ".gif":
        print("输入文件必须是 .gif。", file=sys.stderr)
        return 2

    with Image.open(source) as gif:
        total = getattr(gif, "n_frames", 1)

    every = args.every
    if args.max_frames is not None:
        if args.max_frames < 1:
            print("--max-frames 必须至少为 1。", file=sys.stderr)
            return 2
        every = max(1, math.ceil(total / args.max_frames))
    if every is None or every < 1:
        print("--every 必须至少为 1。", file=sys.stderr)
        return 2

    output = (args.output or default_output_path(source)).expanduser().resolve()
    if output == source:
        print("输出文件不能覆盖输入文件。", file=sys.stderr)
        return 2
    if output.exists() and not args.overwrite:
        print(f"输出文件已存在：{output}\n请换一个文件名，或添加 --overwrite。", file=sys.stderr)
        return 2
    output.parent.mkdir(parents=True, exist_ok=True)

    original_size = source.stat().st_size
    print(f"输入：{source.name}（{total} 帧，{mb(original_size)}）")
    print(f"处理方式：每 {every} 帧保留 1 帧，预计输出 {math.ceil(total / every)} 帧…")
    try:
        total_frames, output_frames, output_size = reduce_gif(source, output, every)
    except Exception as error:
        print(f"处理失败：{error}", file=sys.stderr)
        return 1

    # Do not silently leave a partial file if saving failed; success has a size.
    reduction = (1 - output_size / original_size) * 100 if original_size else 0
    print(f"完成：{output}")
    print(f"帧数：{total_frames} → {output_frames}")
    print(f"大小：{mb(original_size)} → {mb(output_size)}（减少 {reduction:.1f}%）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
