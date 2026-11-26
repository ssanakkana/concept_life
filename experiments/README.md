# 研究地图交互原型

这是 M8 研究地图的独立交互版本，还没有接进 Streamlit demo。

## 生成和打开

```bash
uv run python scripts/build_map_html.py
# 用浏览器打开 experiments/map_interactive.html
```

生成脚本读取：

- `data/processed/research_map_nodes.csv`
- `data/processed/research_map_edges.csv`
- `runs/m8/community_summary.json`

HTML 内嵌数据，D3 7.9.0 使用本目录的 `d3.v7.min.js`，不依赖网络。

## 交互

- 拖动节点，滚轮缩放，拖动画布。
- 点击节点：聚焦。节点放大 3.4 倍，直接邻居按边权放大，其他节点变暗，邻居会被轻量拉近。
- 点击空白：退出聚焦。
- 按钮：重置视图、重新布局、显示或隐藏全部标签。
- URL 参数：`?focus=<concept_id>` 可以在页面加载后自动聚焦某个节点，方便截图和演示。

## 数据

- 300 个节点、1,537 条边，来自 M8 的 top 300 裁剪图。
- 社区是 Louvain，颜色只表示社区，不是排名。
- betweenness 高的概念很多是泛概念，见 `docs/PITFALLS.md` 的 `P-052`。

## 状态

原型，未接入 demo。确认交互和视觉后再替换 `app.py` 的研究地图页。
