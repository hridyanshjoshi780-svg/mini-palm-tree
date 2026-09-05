#!/usr/bin/env python3
"""
TERMTUBE — watch YouTube in your terminal as live ANSI/truecolor video.

Downloads the video with yt-dlp, decodes raw frames with ffmpeg, renders
each frame as colored half-block characters (2 vertical pixels per cell
using ▀ with distinct fg/bg color), and plays audio in sync via ffplay.

Requires: ffmpeg + ffplay on PATH, and the yt-dlp python package.
    pip install yt-dlp

Run:
    python3 termtube.py "https://www.youtube.com/watch?v=..."
    python3 termtube.py "search: lofi hip hop radio"
    python3 termtube.py "search: lofi hip hop radio" --cols 100

Controls: Ctrl+C to quit.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time

try:
    from yt_dlp import YoutubeDL
except ImportError:
    print("Missing dependency. Install it with:\n    pip install yt-dlp")
    sys.exit(1)


BLOCK = "\u2580"  # ▀ upper half block
RESET = "\x1b[0m"
HIDE_CURSOR = "\x1b[?25l"
SHOW_CURSOR = "\x1b[?25h"
HOME = "\x1b[H"
CLEAR = "\x1b[2J"


def check_binaries():
    for exe in ("ffmpeg", "ffplay"):
        if shutil.which(exe) is None:
            print(f"'{exe}' not found on PATH. Install ffmpeg first.")
            sys.exit(1)


def resolve_source(query: str, workdir: str) -> str:
    """Download the video (or first search result) to a local file, return path."""
    if query.startswith("search:"):
        query = "ytsearch1:" + query[len("search:"):].strip()
    elif "://" not in query:
        query = "ytsearch1:" + query

    out_template = os.path.join(workdir, "video.%(ext)s")
    ydl_opts = {
        "format": "bestvideo[height<=480]+bestaudio/best[height<=480]/best",
        "outtmpl": out_template,
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }
    print("Fetching video info...")
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=True)
        if "entries" in info:
            info = info["entries"][0]
        title = info.get("title", "unknown")
        duration = info.get("duration")
    print(f"Downloaded: {title}")

    for fname in os.listdir(workdir):
        if fname.startswith("video."):
            return os.path.join(workdir, fname), title, duration
    raise RuntimeError("Download finished but output file not found.")


def probe_fps(path: str) -> float:
    try:
        out = subprocess.check_output(
            ["ffprobe", "-v", "0", "-select_streams", "v:0",
             "-show_entries", "stream=r_frame_rate",
             "-of", "csv=p=0", path],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        num, _, den = out.partition("/")
        den = den or "1"
        fps = float(num) / float(den)
        return fps if 1 <= fps <= 60 else 24.0
    except Exception:
        return 24.0


class AudioPlayer:
    def __init__(self, path: str):
        self.path = path
        self.proc = None

    def start(self):
        self.proc = subprocess.Popen(
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", self.path],
            stdin=subprocess.DEVNULL,
        )

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()


class FrameRenderer:
    """Turns raw RGB24 frame bytes into an ANSI truecolor string."""

    def __init__(self, cols: int, rows_px: int):
        self.cols = cols
        self.rows_px = rows_px  # pixel rows, must be even (2 per text row)

    def render(self, frame: bytes) -> str:
        w, h = self.cols, self.rows_px
        out = []
        row_bytes = w * 3
        for y in range(0, h, 2):
            top = frame[y * row_bytes:(y + 1) * row_bytes]
            bot_start = (y + 1) * row_bytes
            bottom = frame[bot_start:bot_start + row_bytes] if y + 1 < h else top
            line_parts = []
            prev = None
            for x in range(w):
                i = x * 3
                tr, tg, tb = top[i], top[i + 1], top[i + 2]
                br, bg, bb = bottom[i], bottom[i + 1], bottom[i + 2]
                key = (tr, tg, tb, br, bg, bb)
                if key != prev:
                    line_parts.append(
                        f"\x1b[38;2;{tr};{tg};{tb}m\x1b[48;2;{br};{bg};{bb}m"
                    )
                    prev = key
                line_parts.append(BLOCK)
            out.append("".join(line_parts) + RESET)
        return "\n".join(out)


def get_target_size(cols_arg):
    term_cols, term_rows = shutil.get_terminal_size(fallback=(100, 40))
    cols = cols_arg or min(term_cols, 120)
    rows = int(cols * 0.5)  # roughly correct aspect for half-block cells
    rows_px = max(20, min(rows * 2, (term_rows - 3) * 2))
    return cols, rows_px


def play(path: str, title: str, cols_arg):
    fps = probe_fps(path)
    cols, rows_px = get_target_size(cols_arg)
    renderer = FrameRenderer(cols, rows_px)
    frame_size = cols * rows_px * 3

    ffmpeg_cmd = [
        "ffmpeg", "-loglevel", "quiet", "-i", path,
        "-vf", f"scale={cols}:{rows_px}",
        "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-r", f"{fps}", "-",
    ]
    proc = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, bufsize=frame_size * 2)

    audio = AudioPlayer(path)
    audio.start()

    sys.stdout.write(HIDE_CURSOR + CLEAR)
    frame_idx = 0
    start_time = time.time()
    try:
        while True:
            buf = proc.stdout.read(frame_size)
            if len(buf) < frame_size:
                break
            target_time = start_time + frame_idx / fps
            now = time.time()
            if target_time > now:
                time.sleep(target_time - now)
            elif now - target_time > 0.5:
                frame_idx += 1
                continue  # falling behind, skip render but keep pace

            art = renderer.render(buf)
            sys.stdout.write(HOME)
            sys.stdout.write(f" {title[:cols]}\n")
            sys.stdout.write(art + "\n")
            sys.stdout.flush()
            frame_idx += 1
    except KeyboardInterrupt:
        pass
    finally:
        proc.terminate()
        audio.stop()
        sys.stdout.write(SHOW_CURSOR + RESET + "\n")
        sys.stdout.flush()


def main():
    parser = argparse.ArgumentParser(description="Watch YouTube in your terminal.")
    parser.add_argument("query", help="YouTube URL, or 'search: <terms>'")
    parser.add_argument("--cols", type=int, default=None,
                         help="Character columns wide (default: fit terminal, max 120)")
    args = parser.parse_args()

    check_binaries()

    with tempfile.TemporaryDirectory(prefix="termtube_") as workdir:
        path, title, duration = resolve_source(args.query, workdir)
        if duration:
            mins, secs = divmod(int(duration), 60)
            print(f"Duration: {mins}:{secs:02d}  |  starting playback...")
        time.sleep(1)
        play(path, title, args.cols)


if __name__ == "__main__":
    main()