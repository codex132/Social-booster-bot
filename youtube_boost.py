# youtube_boost.py
# platform : YouTube
# method   : clones + runs MShawon/YouTube-Viewer (headless Chromium)
# metric   : views (likes/subs need a logged-in session — views are free)

import subprocess
import sys
import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)

REPO_URL = "https://github.com/MShawon/YouTube-Viewer.git"
REPO_DIR = Path("./YouTube-Viewer")


def _ensure_repo():
    if not REPO_DIR.exists():
        log.info("Cloning YouTube-Viewer…")
        subprocess.run(
            ["git", "clone", REPO_URL, "--depth", "10", str(REPO_DIR)],
            check=True,
        )
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "setuptools<59", "-q"],
            check=True,
        )
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r",
             str(REPO_DIR / "requirements.txt"), "-q"],
            check=True,
        )


def boost_youtube(
    video_url: str,
    threads: int = 2,
    duration_minutes: int = 30,
) -> dict:
    """
    Run YouTube-Viewer for `duration_minutes` using `threads` headless browsers.
    Estimated views: threads × minutes × 2  (one view every ~30 s per thread).
    Views without proxies can partially drop after 24–48 h — run longer sessions
    and loop daily for stickier counts.
    """
    results = {
        "estimated_views": 0,
        "runtime_minutes": duration_minutes,
        "errors": [],
    }

    try:
        _ensure_repo()
    except Exception as e:
        results["errors"].append(f"repo setup failed: {e}")
        return results

    urls_file = REPO_DIR / "urls.txt"
    urls_file.write_text(video_url.strip() + "\n")

    # YouTube-Viewer CLI: --threads N  --duration N (minutes)  --headless
    cmd = [
        sys.executable,
        str(REPO_DIR / "youtube_viewer.py"),
        "--threads", str(threads),
        "--duration", str(duration_minutes),
        "--headless",
    ]

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(REPO_DIR),
            capture_output=True,
            text=True,
            timeout=duration_minutes * 60 + 120,
        )
        results["estimated_views"] = threads * duration_minutes * 2
        if proc.returncode not in (0, None):
            snippet = (proc.stderr or proc.stdout or "")[:300]
            results["errors"].append(snippet)
            log.warning(f"YouTube-Viewer exited {proc.returncode}: {snippet}")
    except subprocess.TimeoutExpired:
        results["estimated_views"] = threads * duration_minutes * 2
    except Exception as e:
        results["errors"].append(str(e))
        log.error(f"YouTube-Viewer error: {e}")

    return results
