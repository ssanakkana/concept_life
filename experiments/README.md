# 研究地图交互原型

Streamlit「研究地图」页和独立分享版共用 `map_template.html`。Streamlit 读取当前本地 M8 产物，分享版内嵌生成时的图数据。

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

- 默认显示地图内的 300 个概念。社区各有一个标注的代表概念，悬停在节点上可以查看最多 8 条主要连线。
- 点击概念时，镜头按比例放大节点及其最强的 5 个邻居，其他节点变成浅灰色小点。可按需展开聚焦概念的全部地图内邻居。
- 点击空白或按 Escape 恢复聚焦前的视野。「切换精简图」只显示社区代表概念。
- 可拖动节点、平移和缩放。URL 参数支持按概念 ID 或完整名称直接聚焦，如 `?focus=Transformer`。

## 数据

- 300 个节点、1,537 条边，来自 M8 的 top 300 裁剪图。
- 社区是 Louvain，颜色只表示社区，不是排名。
- betweenness 高的概念很多是泛概念，见 `docs/PITFALLS.md` 的 `P-052`。

更新分享版时，先用想分享的 M8 产物生成 HTML，再运行单文件构建脚本。