#!/usr/bin/env python3
"""Turn the standalone interactive map into an Artifact-ready HTML file.

The Artifact host wraps the file in its own document skeleton, so this strips
the <html>/<head>/<body> wrappers, switches D3 to the CDN, and adds the light
and dark theme tokens required by the artifact page contract.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "experiments" / "map_interactive.html"
OUT = ROOT / "experiments" / "map_artifact.html"

THEME = r"""
:root {
  --bg: #f6f8fb;
  --panel: rgba(255, 255, 255, 0.94);
  --ink: #17202a;
  --muted: #5d6d7e;
  --line: #d9e1ec;
  --link: #9aa7b8;
  --accent: #2c5a86;
  --node-stroke: #ffffff;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #0f1720;
    --panel: rgba(22, 32, 43, 0.94);
    --ink: #e8eef5;
    --muted: #9fb0c0;
    --line: #2a3a4a;
    --link: #5b7086;
    --accent: #7ab7e8;
    --node-stroke: #0f1720;
    color-scheme: dark;
  }
}
:root[data-theme="dark"] {
  --bg: #0f1720;
  --panel: rgba(22, 32, 43, 0.94);
  --ink: #e8eef5;
  --muted: #9fb0c0;
  --line: #2a3a4a;
  --link: #5b7086;
  --accent: #7ab7e8;
  --node-stroke: #0f1720;
  color-scheme: dark;
}
html, body { height: 100%; }
body {
  display: flex;
  flex-direction: column;
  background: var(--bg);
  color: var(--ink);
  padding-left: max(16px, env(safe-area-inset-left, 0px));
  padding-right: max(16px, env(safe-area-inset-right, 0px));
}
header {
  flex-shrink: 0;
  background: var(--panel);
  border-color: var(--line);
}
main { flex: 1; min-height: 0; height: auto; }
button { background: var(--panel); color: var(--ink); border-color: var(--line); }
button:hover { color: var(--accent); border-color: var(--accent); }
.link { stroke: var(--link); }
.node text { fill: var(--ink); stroke: var(--bg); }
#legend, #tooltip, #focus-label {
  background: var(--panel);
  color: var(--ink);
  border-color: var(--line);
}
#tooltip b { color: var(--accent); }
#legend, #tooltip { box-shadow: 0 10px 30px rgba(0, 0, 0, 0.14); }
@media (max-width: 720px) {
  header { flex-direction: column; align-items: flex-start; }
  #legend { display: none; }
  #hint { display: none; }
}
"""


def main() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    style_match = re.search(r"<style>(.*?)</style>", source, re.S)
    body_match = re.search(r"<body>(.*?)</body>", source, re.S)
    if not style_match or not body_match:
        raise SystemExit("could not parse the standalone map")
    style = style_match.group(1)
    body = body_match.group(1)
    body = body.replace(
        '<script src="d3.v7.min.js"></script>',
        '<script src="https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js"></script>',
    )
    artifact = (
        "<title>研究地图</title>\n"
        '<meta name="claude:viewport-fit-sides" content="cover">\n'
        f"<style>{style}\n{THEME}</style>\n"
        f"{body}"
    )
    OUT.write_text(artifact, encoding="utf-8")
    print(f"wrote {OUT} ({len(artifact) / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
