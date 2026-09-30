"""Package every demo setting into one HTML file for offline presenting."""

import json
import base64
import re
from pathlib import Path
from experiment import run


def build(destination="results/demo.html"):
    root = Path(__file__).parent
    cache = {
        f"seed={seed}&budget={budget}&repeats={repeats}": run(seed, budget, repeats)
        for seed in (7, 42, 101)
        for budget in (16, 32, 64)
        for repeats in (10, 20, 40)
    }
    source = (root / "static/index.html").read_text()
    font = base64.b64encode((root / "static/vendor/roboto.woff2").read_bytes()).decode()
    source = re.sub(
        r'<link rel="stylesheet" href="style.css"\s*/?>',
        lambda _: "<style>" + (root / "static/style.css").read_text() + "</style>",
        source,
    )
    source = re.sub(
        r"url\([\"\']vendor/roboto.woff2[\"\']\)",
        lambda _: "url('data:font/woff2;base64," + font + "')",
        source,
    )
    source = source.replace(
        '<script src="vendor/material.js"></script>',
        "<script>" + (root / "static/vendor/material.js").read_text() + "</script>",
    )
    payload = json.dumps(cache, separators=(",", ":"), allow_nan=False).replace(
        "<", "\\u003c"
    )
    source = source.replace(
        '<script src="app.js"></script>',
        "<script>window.DEMO_CACHE="
        + payload
        + ";</script><script>"
        + (root / "static/app.js").read_text()
        + "</script>",
    )
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source)
    return path


if __name__ == "__main__":
    print(build().resolve())
