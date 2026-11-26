#!/usr/bin/env python3
"""Build a standalone interactive research map.

The HTML embeds the top-300 nodes and pruned co-occurrence edges. It uses a
local D3 copy in experiments/d3.v7.min.js, so opening it does not need network.

Usage:
    uv run python scripts/build_map_html.py
    # open experiments/map_interactive.html in a browser
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def load_csv(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--nodes",
        type=Path,
        default=ROOT / "data" / "processed" / "research_map_nodes.csv",
    )
    parser.add_argument(
        "--edges",
        type=Path,
        default=ROOT / "data" / "processed" / "research_map_edges.csv",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=ROOT / "runs" / "m8" / "community_summary.json",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "experiments" / "map_interactive.html",
    )
    args = parser.parse_args()

    node_rows = load_csv(args.nodes)
    edge_rows = load_csv(args.edges)
    summary = json.loads(args.summary.read_text(encoding="utf-8"))

    nodes = [
        {
            "id": row["concept_id"],
            "name": row["name"],
            "community": int(row["community"]),
            "total": int(row["total_count"]),
            "betweenness": float(row["betweenness"]),
            "degree": int(row["degree"]),
            "x": float(row["x"]),
            "y": float(row["y"]),
        }
        for row in node_rows
    ]
    links = [
        {
            "source": row["source"],
            "target": row["target"],
            "support": int(row["support"]),
        }
        for row in edge_rows
    ]
    payload = {
        "nodes": nodes,
        "links": links,
        "communities": summary["communities"],
        "stats": {
            "nodes": summary["map"]["nodes"],
            "edges": summary["map"]["edges"],
            "communities": summary["n_communities"],
            "modularity": summary["modularity"],
        },
    }
    data_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")

    html = TEMPLATE.replace("__DATA_JSON__", data_json)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html, encoding="utf-8")
    print(f"wrote {args.out} ({len(html) / 1024:.1f} KB)")
    print(f"nodes={len(nodes)} links={len(links)}")
    if not (args.out.parent / "d3.v7.min.js").exists():
        print("warning: d3.v7.min.js is missing next to the HTML", file=sys.stderr)


TEMPLATE = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>研究地图 · Concept Life</title>
<style>
  :root {
    --ink: #17202a;
    --muted: #5d6d7e;
    --line: #d9e1ec;
    --paper: #f6f8fb;
    --panel: rgba(255, 255, 255, 0.94);
    --accent: #2c5a86;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; height: 100%; }
  body {
    color: var(--ink);
    background: var(--paper);
    font-family: "Segoe UI", "Microsoft YaHei", "PingFang SC", sans-serif;
    overflow: hidden;
  }
  header {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 18px;
    padding: 16px 22px 12px;
    border-bottom: 1px solid var(--line);
    background: rgba(255, 255, 255, 0.72);
    backdrop-filter: blur(8px);
  }
  h1 { margin: 0; font-size: 22px; letter-spacing: 0.02em; }
  .sub { margin: 4px 0 0; color: var(--muted); font-size: 12.5px; }
  .controls { display: flex; gap: 8px; flex-wrap: wrap; }
  button {
    border: 1px solid var(--line);
    background: #fff;
    color: var(--ink);
    border-radius: 999px;
    padding: 7px 13px;
    font-size: 12.5px;
    cursor: pointer;
  }
  button:hover { border-color: var(--accent); color: var(--accent); }
  main { position: relative; height: calc(100vh - 82px); }
  svg { width: 100%; height: 100%; display: block; cursor: grab; }
  svg:active { cursor: grabbing; }
  .link { stroke: #9aa7b8; }
  .node circle { stroke: #fff; }
  .node text {
    fill: #34495e;
    pointer-events: none;
    paint-order: stroke;
    stroke: rgba(255, 255, 255, 0.9);
    stroke-width: 2.5px;
  }
  #legend[hidden] { display: none !important; }
  #legend {
    position: absolute;
    top: 14px;
    right: 14px;
    width: 238px;
    max-height: calc(100% - 28px);
    overflow: auto;
    padding: 12px 13px;
    border: 1px solid var(--line);
    border-radius: 14px;
    background: var(--panel);
    box-shadow: 0 10px 30px rgba(23, 32, 42, 0.08);
    font-size: 12px;
  }
  #legend h2 { margin: 0 0 8px; font-size: 13px; }
  .legend-row {
    display: grid;
    grid-template-columns: 10px 1fr auto;
    gap: 7px;
    align-items: start;
    padding: 5px 0;
    border-top: 1px solid #eef2f7;
  }
  .legend-row:first-of-type { border-top: 0; }
  .dot { width: 10px; height: 10px; border-radius: 50%; margin-top: 3px; }
  .legend-name { font-weight: 600; }
  .legend-top { color: var(--muted); font-size: 10.5px; line-height: 1.35; }
  .legend-size { color: var(--muted); font-variant-numeric: tabular-nums; }
  #tooltip {
    position: absolute;
    display: none;
    pointer-events: none;
    max-width: 260px;
    padding: 9px 11px;
    border: 1px solid var(--line);
    border-radius: 10px;
    background: rgba(255, 255, 255, 0.97);
    box-shadow: 0 8px 24px rgba(23, 32, 42, 0.12);
    font-size: 12px;
    line-height: 1.45;
    z-index: 5;
  }
  #tooltip b { color: var(--accent); }
  #focus-label {
    position: absolute;
    left: 50%;
    bottom: 16px;
    transform: translateX(-50%);
    display: none;
    padding: 7px 14px;
    border: 1px solid var(--line);
    border-radius: 999px;
    background: var(--panel);
    color: var(--muted);
    font-size: 12.5px;
    box-shadow: 0 8px 24px rgba(23, 32, 42, 0.08);
    z-index: 4;
  }
  #hint {
    position: absolute;
    left: 16px;
    bottom: 14px;
    color: var(--muted);
    font-size: 11.5px;
  }
  @media (max-width: 760px) {
    header { align-items: flex-start; flex-direction: column; }
    #legend { width: 190px; }
    #hint { display: none; }
  }
</style>
</head>
<body>
<header>
  <div>
    <h1>研究地图</h1>
    <p class="sub" id="stats"></p>
  </div>
  <div class="controls">
    <button id="reset-view">重置视图</button>
    <button id="reheat">重新布局</button>
    <button id="toggle-labels">显示全部标签</button>
  </div>
</header>
<main>
  <svg id="graph"></svg>
  <aside id="legend"><h2>社区</h2><div id="legend-body"></div></aside>
  <div id="tooltip"></div>
  <div id="focus-label"></div>
  <div id="hint">拖动节点 · 滚轮缩放 · 点击节点聚焦 · 点击空白退出</div>
</main>
<script src="d3.v7.min.js"></script>
<script id="graph-data" type="application/json">__DATA_JSON__</script>
<script>
const DATA = JSON.parse(document.getElementById("graph-data").textContent);
const nodes = DATA.nodes.map(d => ({...d}));
const links = DATA.links.map(d => ({...d}));
const byId = new Map(nodes.map(d => [d.id, d]));

const palette = [
  "#4e79a7", "#f28e2b", "#e15759", "#76b7b2",
  "#59a14f", "#edc948", "#b07aa1", "#ff9da7",
  "#9c755f", "#bab0ac", "#86bcb6", "#d37295"
];
const color = d3.scaleOrdinal(palette);
const extent = d3.extent(nodes, d => d.total);
const radius = d3.scaleSqrt().domain(extent).range([4, 20]);
const baseR = d => radius(d.total);

document.getElementById("stats").textContent =
  `${DATA.stats.nodes} 个概念 · ${DATA.stats.edges} 条边 · ` +
  `${DATA.stats.communities} 个社区 · modularity ${DATA.stats.modularity.toFixed(3)}`;

const main = document.querySelector("main");
let width = main.clientWidth;
let height = main.clientHeight;
const svg = d3.select("#graph").attr("viewBox", [0, 0, width, height]);
const viewport = svg.append("g");

const zoom = d3.zoom()
  .scaleExtent([0.25, 5])
  .on("zoom", event => viewport.attr("transform", event.transform));
svg.call(zoom);

const link = viewport.append("g")
  .attr("class", "links")
  .selectAll("line")
  .data(links)
  .join("line")
  .attr("class", "link")
  .attr("stroke-width", d => Math.min(2.4, 0.25 + Math.sqrt(d.support) / 7))
  .attr("stroke-opacity", d => 0.035 + 0.09 * Math.min(1, d.support / 80));

const node = viewport.append("g")
  .attr("class", "nodes")
  .selectAll("g")
  .data(nodes)
  .join("g")
  .attr("class", "node")
  .call(dragBehavior)
  .on("click", (event, d) => { event.stopPropagation(); focusNode(d); })
  .on("mouseenter", (event, d) => showTooltip(event, d))
  .on("mousemove", moveTooltip)
  .on("mouseleave", hideTooltip);

node.append("circle")
  .attr("r", baseR)
  .attr("fill", d => color(d.community))
  .attr("stroke-width", 1.4);

const labels = node.append("text")
  .text(d => d.name)
  .attr("x", d => baseR(d) + 4)
  .attr("y", 4)
  .attr("font-size", 9.5)
  .style("display", d => d.total >= 2000 ? null : "none");

// Seed the force layout with the spring positions, scaled to the canvas.
nodes.forEach(d => {
  d.x = width * 0.12 + d.x * width * 0.76;
  d.y = height * 0.12 + d.y * height * 0.76;
});

const simulation = d3.forceSimulation(nodes)
  .force("link", d3.forceLink(links)
    .id(d => d.id)
    .distance(d => 70 + 120 / Math.sqrt(d.support))
    .strength(d => Math.min(0.35, d.support / 200)))
  .force("charge", d3.forceManyBody().strength(-180).distanceMax(700))
  .force("x", d3.forceX(width / 2).strength(0.025))
  .force("y", d3.forceY(height / 2).strength(0.025))
  .force("collide", d3.forceCollide().radius(d => baseR(d) + 4))
  .alphaDecay(0.02)
  .on("tick", ticked);

function ticked() {
  link
    .attr("x1", d => d.source.x)
    .attr("y1", d => d.source.y)
    .attr("x2", d => d.target.x)
    .attr("y2", d => d.target.y);
  node.attr("transform", d => `translate(${d.x},${d.y})`);
}

function dragBehavior(selection) {
  selection.call(d3.drag()
    .on("start", (event, d) => {
      event.sourceEvent.stopPropagation();
      if (!event.active) simulation.alphaTarget(0.28).restart();
      d.fx = d.x;
      d.fy = d.y;
    })
    .on("drag", (event, d) => { d.fx = event.x; d.fy = event.y; })
    .on("end", (event, d) => {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }));
}

let focusedId = null;
let neighborWeight = new Map();
let maxWeight = 1;
let showAllLabels = false;
let previousTransform = d3.zoomIdentity;
let focusToken = 0;

function endpointId(value) {
  return typeof value === "object" ? value.id : value;
}

function focusForce(alpha) {
  if (!focusedId) return;
  const center = byId.get(focusedId);
  if (!center) return;
  nodes.forEach(n => {
    if (n.id === focusedId) return;
    const weight = neighborWeight.get(n.id) || 0;
    if (!weight) return;
    const strength = 0.02 + 0.10 * (weight / maxWeight);
    n.vx += (center.x - n.x) * strength * alpha;
    n.vy += (center.y - n.y) * strength * alpha;
  });
}

function focusViewport(d) {
  const members = nodes.filter(n => n.id === d.id || neighborWeight.has(n.id));
  if (!members.length) return;
  const xs = members.map(n => n.x);
  const ys = members.map(n => n.y);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const spanX = Math.max(120, maxX - minX);
  const spanY = Math.max(120, maxY - minY);
  const scale = Math.max(0.8, Math.min(2.0, 0.72 * Math.min(width / spanX, height / spanY)));
  const cx = (minX + maxX) / 2;
  const cy = (minY + maxY) / 2;
  const transform = d3.zoomIdentity
    .translate(width / 2 - scale * cx, height / 2 - scale * cy)
    .scale(scale);
  svg.transition().duration(650).call(zoom.transform, transform);
}

function focusNode(d) {
  if (focusedId === d.id) { resetFocus(); return; }
  if (!focusedId) previousTransform = d3.zoomTransform(svg.node());
  focusedId = d.id;
  neighborWeight = new Map();
  maxWeight = 1;
  links.forEach(l => {
    const source = endpointId(l.source);
    const target = endpointId(l.target);
    if (source === d.id) {
      neighborWeight.set(target, Math.max(neighborWeight.get(target) || 0, l.support));
      maxWeight = Math.max(maxWeight, l.support);
    }
    if (target === d.id) {
      neighborWeight.set(source, Math.max(neighborWeight.get(source) || 0, l.support));
      maxWeight = Math.max(maxWeight, l.support);
    }
  });

  node.select("circle").transition().duration(420)
    .attr("r", n => {
      if (n.id === d.id) return baseR(n) * 3.4;
      if (neighborWeight.has(n.id)) {
        return baseR(n) * (1 + 1.25 * neighborWeight.get(n.id) / maxWeight);
      }
      return baseR(n) * 0.5;
    })
    .attr("opacity", n =>
      n.id === d.id || neighborWeight.has(n.id) ? 1 : 0.06)
    .attr("stroke-width", n => n.id === d.id ? 3.5 : 1.4)
    .attr("stroke", n => n.id === d.id ? "currentColor" : "#ffffff")
    .style("filter", n =>
      n.id === d.id ? "drop-shadow(0 0 10px rgba(44,90,134,.75))" : null);

  labels.transition().duration(420)
    .style("display", n =>
      (showAllLabels || n.id === d.id || neighborWeight.has(n.id)) ? null : "none")
    .attr("opacity", n =>
      n.id === d.id || neighborWeight.has(n.id) ? 1 : 0.12)
    .attr("font-size", n => n.id === d.id ? 14 : 10.5)
    .attr("font-weight", n => n.id === d.id ? 700 : 400);

  link.transition().duration(420)
    .attr("stroke-opacity", l => {
      const source = endpointId(l.source);
      const target = endpointId(l.target);
      return source === d.id || target === d.id ? 0.9 : 0.008;
    })
    .attr("stroke-width", l => {
      const source = endpointId(l.source);
      const target = endpointId(l.target);
      return source === d.id || target === d.id
        ? Math.min(5, 1.0 + Math.sqrt(l.support) / 2)
        : 0.3;
    });

  node.filter(n => n.id === d.id || neighborWeight.has(n.id)).raise();
  simulation.force("focus", focusForce);
  const badge = document.getElementById("focus-label");
  badge.style.display = "block";
  badge.textContent =
    `聚焦：${d.name} · 社区 ${d.community} · ${neighborWeight.size} 个直接邻居`;
  simulation.alpha(0.4).restart();
  document.getElementById("legend").hidden = true;
  const token = ++focusToken;
  setTimeout(() => {
    if (token === focusToken && focusedId === d.id) focusViewport(d);
  }, 650);
}

function resetFocus() {
  focusToken++;
  focusedId = null;
  neighborWeight = new Map();
  document.getElementById("legend").hidden = false;
  node.select("circle").transition().duration(420)
    .attr("r", baseR)
    .attr("opacity", 1)
    .attr("stroke-width", 1.4)
    .attr("stroke", "#ffffff")
    .style("filter", null);
  labels.transition().duration(420)
    .style("display", n => (showAllLabels || n.total >= 2000) ? null : "none")
    .attr("opacity", 1)
    .attr("font-size", 9.5)
    .attr("font-weight", 400);
  link.transition().duration(420)
    .attr("stroke-opacity", d => 0.035 + 0.09 * Math.min(1, d.support / 80))
    .attr("stroke-width", d => Math.min(2.4, 0.25 + Math.sqrt(d.support) / 7));
  simulation.force("focus", null);
  document.getElementById("focus-label").style.display = "none";
  svg.transition().duration(650).call(zoom.transform, previousTransform);
  simulation.alpha(0.2).restart();
}

svg.on("click", resetFocus);

function showTooltip(event, d) {
  const tooltip = document.getElementById("tooltip");
  tooltip.innerHTML =
    `<b>${d.name}</b><br>` +
    `社区 ${d.community} · 论文 ${d.total}<br>` +
    `betweenness ${d.betweenness.toFixed(4)} · degree ${d.degree}`;
  tooltip.style.display = "block";
  moveTooltip(event);
}
function moveTooltip(event) {
  const tooltip = document.getElementById("tooltip");
  const rect = main.getBoundingClientRect();
  let x = event.clientX - rect.left + 14;
  let y = event.clientY - rect.top + 14;
  if (x + 270 > width) x -= 285;
  if (y + 90 > height) y -= 100;
  tooltip.style.left = `${x}px`;
  tooltip.style.top = `${y}px`;
}
function hideTooltip() {
  document.getElementById("tooltip").style.display = "none";
}

document.getElementById("reset-view").addEventListener("click", () => {
  if (focusedId) {
    resetFocus();
  } else {
    svg.transition().duration(650).call(zoom.transform, d3.zoomIdentity);
  }
});
document.getElementById("reheat").addEventListener("click", () => {
  simulation.alpha(1).restart();
});
document.getElementById("toggle-labels").addEventListener("click", event => {
  showAllLabels = !showAllLabels;
  event.target.textContent = showAllLabels ? "隐藏全部标签" : "显示全部标签";
  labels.style("display", n => {
    if (showAllLabels) return null;
    if (focusedId) return n.id === focusedId || neighborWeight.has(n.id) ? null : "none";
    return n.total >= 2000 ? null : "none";
  });
});

const legendBody = document.getElementById("legend-body");
DATA.communities.forEach(community => {
  const row = document.createElement("div");
  row.className = "legend-row";
  const dot = document.createElement("span");
  dot.className = "dot";
  dot.style.background = color(community.community);
  const body = document.createElement("div");
  const name = document.createElement("div");
  name.className = "legend-name";
  name.textContent = `社区 ${community.community}`;
  const top = document.createElement("div");
  top.className = "legend-top";
  top.textContent = community.top_concepts.slice(0, 3).join("、");
  body.append(name, top);
  const size = document.createElement("span");
  size.className = "legend-size";
  size.textContent = community.size;
  row.append(dot, body, size);
  legendBody.append(row);
});

const focusParam = new URLSearchParams(location.search).get("focus");
if (focusParam) {
  setTimeout(() => {
    const target = nodes.find(n =>
      n.id === focusParam || n.name.toLowerCase() === focusParam.toLowerCase());
    if (target) focusNode(target);
  }, 1800);
}

window.addEventListener("resize", () => {
  width = main.clientWidth;
  height = main.clientHeight;
  svg.attr("viewBox", [0, 0, width, height]);
  simulation.force("center", d3.forceCenter(width / 2, height / 2));
  simulation.alpha(0.3).restart();
});
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
