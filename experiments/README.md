# 研究地图交互原型

这是 M8 研究地图的独立交互版本，还没有接进 Streamlit demo。

## 三种版本

- `map_interactive.html`：本地开发版，引用同目录的 `d3.v7.min.js`。生成物，git 忽略。
- `map_standalone.html`：单文件版，D3 内联，下载后双击即可打开。进 git，方便直接发给队友。
- `map_artifact.html`：Artifact 版，D3 走 CDN。生成物，git 忽略；当前会话认证不支持发布 Artifact。

## 生成

```bash
uv run python scripts/build_map_html.py
uv run python scripts/build_map_standalone.py
uv run python scripts/build_map_artifact.py
```

生成脚本读取：

- `data/processed/research_map_nodes.csv`
- `data/processed/research_map_edges.csv`
- `runs/m8/community_summary.json`

## 交互

- 拖动节点，滚轮缩放，拖动画布。
- 点击节点：聚焦。节点放大 3.4 倍，直接邻居按边权放大，其他节点变暗，邻居会被轻量拉近。
- 聚焦时图例隐藏，视野自动平移到“节点 + 邻居”的包围盒；点击空白恢复原视野和图例。
- 按钮：重置视图、重新布局、显示或隐藏全部标签。
- URL 参数：`?focus=<concept_id>` 可以在页面加载后自动聚焦某个节点，方便截图和演示。

## 数据

- 300 个节点、1,537 条边，来自 M8 的 top 300 裁剪图。
- 社区是 Louvain，颜色只表示社区，不是排名。
- betweenness 高的概念很多是泛概念，见 `docs/PITFALLS.md` 的 `P-052`。

## 状态

原型，未接入 demo。确认交互和视觉后再替换 `app.py` 的研究地图页。
