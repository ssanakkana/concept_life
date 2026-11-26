# Concept Life

学术概念的生命周期挖掘：兴起、发展、爆发、衰退、复活、被替代，以及下一阶段的上升概念预测。

这个仓库是 AI3602 期末项目的代码框架。先导项目在 `../kg_search/`，本仓库复用它的 Acemap 缓存，但从一个更小、更可扩展的问题重新开始：一个概念在语料里是怎么活过一生的。

## 当前状态

| 阶段 | 内容 | 状态 |
| --- | --- | --- |
| M0 | 从先导缓存到论文表、概念时间线、上升概念榜 | 已实现 |
| M1 | Acemap 全量抓取、领域过滤、数据质量报告 | 已实现，42,460 篇论文，10,957 个概念 |
| M2 | 生命周期事件：出生、爆发、峰值、衰退、复活、死亡 | 已实现，3,003 个事件，黄金案例 30/30 |
| M3 | 候选替代检测、趋势预测 | 已实现，趋势 precision@10 0.20，替代候选 30 对 |
| M4 | Streamlit demo、海报、讲稿 | demo 已实现，9 页 smoke test 通过；海报和讲稿未做 |
| M5 | 生命周期聚类（扩展） | 已实现，5 类，silhouette 0.285 |
| M6 | 替代复核页（扩展） | 已实现，20/20 标注，precision@10 0.60，precision@20 0.45 |
| M7 | 生命周期早期预测（扩展） | 已实现，5 折 accuracy 0.656，macro-F1 0.482 |
| M8 | 研究地图（扩展） | 已实现，8 个社区，modularity 0.328 |

扩展想法和备选方向在 `docs/IDEAS.md`。当前仓库已实现 M0 到 M8 和 demo，海报和讲稿还没有。

## 环境

- Python 3.10 及以上。
- 推荐用 uv 管理本地环境：

```bash
uv sync
```

`uv sync` 会创建 `.venv` 并安装 `pyproject.toml` 里的依赖，`uv.lock` 锁定版本。所有命令都可以写成 `uv run python ...` 或 `uv run streamlit ...`。
- `requirements.txt` 是 pip 兼容清单，给不用 uv 的环境。
- M0 只用标准库；M1 需要 `requests`；M2 需要 `numpy`；M4 demo 需要 `streamlit`、`pandas`、`altair`。

## 仓库结构

```text
concept_life/
├── AGENTS.md                 # AI 协作规范，唯一事实来源
├── CLAUDE.md                 # Claude Code 的入口，指向 AGENTS.md
├── README.md                 # 本文件：结构、复现、产物格式
├── pyproject.toml            # uv 依赖清单，demo 和脚本共用
├── uv.lock                   # uv 锁定版本
├── requirements.txt          # pip 兼容清单
├── .gitignore                # 忽略数据、运行产物、缓存、.venv
├── configs/
│   ├── default.json          # M0 配置：缓存路径、年份、窗口、阈值
│   ├── m1.json               # M1 配置：全量缓存、CS 领域过滤、停用词
│   ├── m2.json               # M2 配置：分析区间和生命周期事件阈值
│   ├── m3.json               # M3 配置：替代候选和趋势预测窗口
│   ├── m5.json               # M5 配置：生命周期聚类特征和 k 范围
│   ├── m7.json               # M7 配置：早期窗口、切分年份、模型参数
│   ├── m8.json               # M8 配置：图规模、边阈值、Louvain 分辨率
│   ├── golden_cases.json     # 9 个黄金案例的期望年份范围
│   └── queries.json          # 170 个抓取查询，分 seeds/classic/recent
├── docs/
│   ├── PLAN.md               # M0 到 M4 的阶段、任务、验收标准
│   ├── WORKLOG.md            # 每次工作做了什么、结果、坑、下一步
│   ├── PITFALLS.md           # 已知的坑，动手前先看
│   ├── DECISIONS.md          # 影响架构和评测口径的决定
│   ├── IDEAS.md              # 扩展想法池，带 ID、成本、评估、风险
│   ├── DATA_SOURCES.md       # 添加 Acemap 以外数据源的做法
│   └── AI_USAGE.md           # 课程提交用的 AI 使用说明
├── experiments/
│   ├── README.md             # 交互地图原型说明
│   ├── d3.v7.min.js          # 本地 D3，离线可用
│   ├── map_interactive.html  # 本地开发版，git 忽略
│   ├── map_standalone.html   # 单文件版，进 git，可直接分发
│   └── map_artifact.html     # Artifact 版，git 忽略
├── scripts/
│   ├── m0_from_cache.py      # M0 命令行入口
│   ├── crawl.py              # M1 Acemap 抓取，缓存、断点续抓、manifest
│   ├── data_report.py        # M1 数据质量报告：年份、字段、层级、缺失
│   ├── m2_events.py          # M2 生命周期事件，写 events.jsonl
│   ├── m3_replacements.py    # M3 候选替代检测，写 replacements.jsonl
│   ├── m3_trend.py           # M3 趋势预测回测，写 metrics 和预测表
│   ├── m5_clusters.py        # M5 生命周期聚类，写 clusters CSV 和 summary
│   ├── m7_early.py           # M7 早期预测，写 metrics 和预测表
│   ├── m8_map.py             # M8 共现图、Louvain、桥接概念、地图产物
│   ├── build_map_html.py     # 交互地图原型的 HTML 生成器
│   ├── build_map_standalone.py # 单文件版生成器，内联 D3
│   ├── build_map_artifact.py # Artifact 版生成器，D3 走 CDN
│   ├── evaluate_replacements.py # M6 从人工标签算 precision@k
│   ├── smoke_demo.py         # M4 七个 Streamlit 页面的冒烟测试
│   └── check_golden_cases.py # M2 黄金案例回归检查
├── src/
│   └── concept_life/
│       ├── __init__.py       # 包版本
│       ├── config.py         # 默认配置和 JSON 覆盖
│       ├── schema.py         # Paper / Concept 数据契约和 Acemap 解析
│       ├── ingest.py         # 读缓存、去重、写 JSONL
│       ├── series.py         # 逐年计数、展示名
│       ├── rising.py         # share 归一化的上升榜
│       ├── mine.py           # 基于 share 的生命周期事件规则
│       ├── replace.py        # 共现、Jaccard、Pearson、候选替代
│       ├── predict.py        # 趋势特征、逻辑回归、precision@k、NDCG
│       ├── cluster.py        # 形状特征、numpy K-means、silhouette
│       ├── early.py          # 早期特征、softmax、macro-F1、混淆矩阵
│       ├── community.py      # Louvain 社区发现、betweenness 桥接分数
│       ├── dashboard.py      # demo 的只读数据加载
│       └── app.py            # Streamlit 五页界面
├── tests/
│   ├── test_schema.py        # 解析、层级过滤、top-k、领域过滤
│   ├── test_ingest.py        # 停用词、空概念论文丢弃
│   ├── test_temporal.py      # share 归一化、new 概念、最小计数
│   ├── test_mine.py          # 完整生命周期、休眠复活、短序列
│   ├── test_replace.py       # Pearson、Jaccard、合成替代对
│   ├── test_predict.py       # 指标、未来信息不泄漏
│   ├── test_cluster.py       # K-means、silhouette、flash 特征
│   ├── test_early.py         # 早期特征不读未来、softmax、macro-F1
│   ├── test_map.py           # Louvain 两个块、桥接节点 betweenness
│   └── test_dashboard.py     # 时间线补年、概念排序、事件统计
├── data/
│   ├── raw/                  # 原始响应和 manifest，只增不改，git 忽略
│   │   └── acemap/           # 抓取响应，文件名是查询哈希 + 页码
│   └── processed/            # 论文表和时间线，可重建，git 忽略
└── runs/
    ├── m0/                   # M0 运行的配置和摘要，git 忽略
    └── m1/                   # M1 运行的配置、摘要和报告，git 忽略
```

`data/` 和 `runs/` 是运行产物，git 忽略，目录由脚本按需创建。产物可以随时删掉重跑。

## 文件职责

| 文件 | 职责 | 不做什么 |
| --- | --- | --- |
| `schema.py` | 把 Acemap 原始记录解析成 `Paper` 和 `Concept`，过滤层级和分数 | 不读文件，不写文件 |
| `ingest.py` | 遍历缓存目录，按 id 去重，写 `papers.jsonl` | 不做统计，不做图 |
| `series.py` | 从 `Paper` 列表生成每个概念的逐年计数和展示名 | 不做归一化，不做排名 |
| `rising.py` | 用前后窗口的 share 差值和增长率排名 | 不读文件，不画图 |
| `config.py` | 默认配置和 JSON 覆盖，深合并 | 不校验业务语义 |
| `m0_from_cache.py` | 串起上面四步，写 CSV 和 summary | 不实现 M1 之后的逻辑 |
| `crawl.py` | 按查询和页码抓 Acemap，缓存原始响应，写 manifest | 不解析、不做领域过滤 |
| `data_report.py` | 读 `papers.jsonl`，输出年份、字段、层级、缺失统计 | 不做排名，不做图 |
| `mine.py` | 按 share 规则检测出生、爆发、峰值、衰退、休眠、复活、死亡 | 不读文件，不写文件 |
| `replace.py` | 共现支持度、Jaccard、Pearson、候选替代检测 | 不做因果判断，不自动下结论 |
| `predict.py` | 趋势特征、相对/绝对标签、逻辑回归、precision@k、NDCG | 不做随机切分，不引入未来图 |
| `m2_events.py` | 读 `concept_series.csv`，写 `events.jsonl` 和事件表 | 不做替代检测，不做趋势预测 |
| `m3_replacements.py` | 读序列、事件、论文，写替代候选和人工复核表 | 不把候选当替代事实 |
| `m3_trend.py` | 三窗口回测，写指标和预测表 | 不用未来共现边 |
| `check_golden_cases.py` | 用 9 个黄金案例检查事件年份 | 不做历史考证，只做回归 |
| `queries.json` | 170 个抓取查询，分 `seeds`、`classic`、`recent` | 不保证每个查询都有结果 |
| `m1.json` | M1 覆盖配置：全量缓存、CS 过滤、停用词 | 不改变 `default.json` 的 M0 行为 |
| `m2.json` | M2 分析区间和事件阈值 | 不改变 M1 的过滤行为 |
| `m3.json` | M3 替代候选和趋势预测配置 | 不改变 M2 的事件规则 |
| `golden_cases.json` | 黄金案例的期望年份范围 | 不保证现实发明年 |
| `cluster.py` | 形状特征、numpy K-means、silhouette、规则标签 | 不把 total_count 或绝对年份放进聚类 |
| `m5_clusters.py` | 读序列和事件，写聚类 CSV 和 summary | 不做早期分类预测 |
| `m5.json` | M5 聚类特征阈值和 k 范围 | 不改变 M2 的事件规则 |
| `early.py` | 早期特征、softmax、macro-F1、混淆矩阵 | 不用 birth+2 之后的年份 |
| `m7_early.py` | 5 折和出生年份切分，写 metrics 和预测表 | 不把聚类标签当现实金标 |
| `m7.json` | M7 早期窗口、切分年份、模型参数 | 不改变 M5 聚类标签 |
| `community.py` | Louvain 社区发现、betweenness 桥接分数 | 不做时间演化匹配 |
| `m8_map.py` | 建共现图、跑社区、裁剪地图、写节点和边 | 不画全图，只画 top 300 |
| `m8.json` | M8 图规模、边阈值、Louvain 分辨率 | 不改变 M3 的替代候选 |
| `build_map_html.py` | 生成独立交互地图 HTML | 不接 Streamlit，不写数据 |
| `build_map_standalone.py` | 把 D3 内联，生成单文件版 | 不重新计算图 |
| `build_map_artifact.py` | 生成 Artifact 版，D3 走 CDN | 不发布 Artifact |
| `dashboard.py` | demo 的只读数据加载、复核标签合并和 precision 计算 | 不写原始数据，不调 API |
| `app.py` | Streamlit 七页界面，含替代复核和保存 | 不做模型训练 |
| `evaluate_replacements.py` | 从 `replacement_review.csv` 算 precision@10/20 | 不替人做判断 |
| `smoke_demo.py` | 用 AppTest 执行九个页面 | 不做视觉回归 |

## 数据流

```text
../kg_search/cache/*.json
        │
        ▼
   ingest.load_cache         解析、按 level 过滤、按 id 去重
        │
        ▼
   data/processed/papers.jsonl
        │
        ├──► series.build_series ──► concept_series.csv
        │
        └──► rising.rising_table ──► top_rising.csv
                                      │
                                      ▼
                                 runs/m0/summary.json
```

M1 的数据流是在 M0 前面加一段抓取：

```text
configs/queries.json
        │
        ▼
   scripts/crawl.py ──► data/raw/acemap/*.json
        │               data/raw/acemap_manifest.jsonl
        │               data/raw/crawl_summary.json
        ▼
   m0_from_cache.py --config configs/m1.json
        │
        ▼
   data/processed/papers.jsonl
        │
        └──► data_report.py ──► runs/m1/report/
```

所有频率都用“占当年论文总数的比例”，不用原始计数。语料每年在增长，原始计数会把“语料变大”误判成“概念变热”。

## 复现 M0

前提：先导项目的缓存还在 `../kg_search/cache/`。可以先检查：

```bash
ls ../kg_search/cache | head
```

在 `concept_life` 目录下运行：

```bash
uv run python scripts/m0_from_cache.py
```

预期输出：

```text
papers: 1054
concepts: 2471
years: {'min': 1990, 'max': 2024}
wrote: ...\data\processed
top rising:
   1. Artificial neural network                     delta_share=+0.065470  growth=1.60  count=59
   2. Health care                                   delta_share=+0.035398  growth=new  count=12
   3. Task (project management)                     delta_share=+0.027847  growth=1.70  count=23
   4. The Internet                                  delta_share=+0.026549  growth=new  count=9
   5. Process (computing)                           delta_share=+0.024155  growth=2.41  count=14
```

数字取决于缓存内容。如果缓存变了，论文数和概念数会变；只要 `papers` 大于 1000、`concepts` 大于 2000，说明解析正常。

从零重建：

```bash
# Bash
rm -rf data/processed runs/m0
uv run python scripts/m0_from_cache.py
```

```powershell
# PowerShell
Remove-Item -Recurse -Force data\processed, runs\m0
uv run python scripts/m0_from_cache.py
```

M0 不发起网络请求。断网也能跑。

## M1 全量抓取

M1 会真正访问 Acemap，需要 `requests`。先安装依赖：

```bash
pip install -r requirements.txt
```

抓取 170 个查询，每个查询 4 页，每页 100 条：

```bash
uv run python scripts/crawl.py --pages 4 --size 100
```

产物：

- `data/raw/acemap/`：原始响应文件，文件名是查询哈希加页码。
- `data/raw/acemap_manifest.jsonl`：每次请求的状态、结果数、错误。
- `data/raw/crawl_summary.json`：查询数、请求数、缓存命中、失败数、耗时。

断点续抓：直接重跑同一条命令，已有文件会跳过。只想检查缓存覆盖：

```bash
uv run python scripts/crawl.py --offline --pages 4 --size 100
```

抓完用 M1 配置重跑 M0，再做质量报告：

```bash
uv run python scripts/m0_from_cache.py --config configs/m1.json --runs runs/m1
uv run python scripts/data_report.py --papers data/processed/papers.jsonl --config configs/m1.json
```

`configs/m1.json` 做三件事：把缓存目录指向 `data/raw/acemap`，只保留 `topics` 里含 `computer science` 的论文，丢掉 `Field (mathematics)`、`Key (lock)` 这类歧义概念。没有 `topics` 的论文默认保留，数量会写进报告。

报告产物在 `runs/m1/report/`：

- `year_histogram.csv` 和 `year_histogram.txt`：逐年论文数。
- `field_counts.csv`：领域和子领域分布。
- `level_counts.csv`：概念层级分布。
- `summary.json`：论文数、概念数、缺失 DOI、缺失 topics、前后窗口论文数。

本次全量结果：679 次请求，67,896 条原始记录，0 失败，601MB。去重和 CS 过滤后 42,460 篇论文，10,957 个概念，283,434 个概念实例，平均每篇 6.68 个。CS 覆盖 99.5%，206 篇没有 topics。年份 1990 到 2025，2021 年峰值 7,106 篇，2024 年 1,481 篇，2025 年 265 篇。近两年不完整，生命周期分析主区间设为 1995-2023，见 `D-010`。如果某年论文太少，先扩查询集，不要直接做生命周期事件。

## M2 生命周期事件

M2 读 `data/processed/concept_series.csv`，给每个概念打生命周期事件。分析区间 1995 到 2023，所有阈值在 `configs/m2.json`。

```bash
uv run python scripts/m2_events.py --config configs/m2.json
uv run python scripts/check_golden_cases.py
```

产物：

- `data/processed/events.jsonl`：一行一个事件，字段是 `concept_id`、`name`、`type`、`year`、`score`、`evidence`。
- `data/processed/concept_events.csv`：表格版，`evidence` 是 JSON 字符串。
- `runs/m2/summary.json`：事件计数、分析区间和阈值。

本次结果：1,793 个概念有事件，共 3,003 个事件。出生 1,793，爆发 508，峰值 367，衰退 234，休眠 49，复活 49，死亡 3。黄金案例 30/30 通过。

事件规则：

- `birth`：分析区间内第一次出现。
- `burst`：相对前三年均值的 z-score 至少 2，绝对占比增加至少 0.002，相对增加至少 20%。
- `peak`：有效年份里 share 最大的年份，峰值年至少 5 篇。
- `decline`：峰值后连续两年平均 share 低于峰值的 65%。
- `dormancy`：峰值后连续两年活跃度低于 3 篇。
- `revival`：休眠后的第一个活跃年。
- `death`：休眠持续到分析区间结束。

死亡只有 3 个，因为 42,460 篇语料里概念很少完全消失。海报上写“在语料中消失”，不要把 death 当主结论，见 `D-012`。黄金案例的年份是语料相对年份，不是现实发明年，见 `D-013`。

## M3 候选替代与趋势预测

替代检测读序列、事件和论文表，输出候选对和人工复核表：

```bash
uv run python scripts/m3_replacements.py
```

产物：

- `data/processed/replacements.jsonl` 和 `replacements.csv`。
- `runs/m3/replacement_summary.json`。
- `runs/m3/replacement_review.csv`，初始模板，`valid_1_0` 留空。
- `data/labels/replacement_review.csv`，人工标签文件，进 git；demo 的替代复核页读写这个文件。

本次结果：234 个衰退概念、523 个上升概念、52,349 个共现对、30 个候选对。前十里有 Machine translation→Transformer、Distributed learning→Federated learning 等合理对，也有 Pascal、Workload、Java 这种标签噪声。共现相似度偏向互补概念，RNN→Transformer 因为直接共现太少被漏掉，所以这是候选生成，不是自动替代。

人工复核在 demo 的“替代复核”页做。逐对看旧概念和新概念的时间线，标“是 / 否 / 不确定”，保存回 `data/labels/replacement_review.csv`。标完运行：

```bash
uv run python scripts/evaluate_replacements.py
```

输出 precision@10 和 precision@20。未标注和“不确定”不计入分母，页面会显示“已标注 X/10”；top-10 没标完时，不要把部分标注的 precision 当成完整 top-10 精确率。

本次 20 对全部标完，采用“焦点转移”标准，9 对判为有效：Cryptocurrency→Blockchain、Machine translation→Language model、Machine translation→Transformer、Cryptocurrency→Smart contract、Distributed learning→Federated learning、Query language→SQL、Utility computing→Edge computing、Residual neural network→Pruning、Static analysis→Malware。precision@10 = 0.60，precision@20 = 0.45。11 对由人初判，9 对由 AI 补判，其中 5 对在讨论后改判；最终 20 对由人工确认。报告写“1 人 + AI 辅助复核”，见 `D-022`。

趋势预测读同样的数据，做三窗口回测：

```bash
uv run python scripts/m3_trend.py
```

产物：

- `runs/m3/trend_metrics.json`。
- `data/processed/trend_predictions.csv`。

任务定义：给定 T 年的特征，预测 T+1 到 T+2 的相对份额增长 top-k。每个窗口只用 T 年以前的共现图，避免未来泄漏。标签是相对增长，并要求未来份额至少 0.5%。候选要求 T 年份额至少 0.3%、累计至少 10 篇。

本次结果：模型 precision@10 0.200、precision@20 0.150、nDCG@20 0.208；growth 基线 0.100、0.133、0.107；random 0.033、0.067、0.085。模型高于基线，但绝对精度不高，逐窗口方差大，概念标签噪声是主要误差源。

## M5 生命周期聚类（扩展）

用形状特征把概念聚成几类，回答“概念有哪几种活法”。

```bash
uv run python scripts/m5_clusters.py
```

产物：

- `data/processed/lifecycle_clusters.csv`：每个概念的 cluster、label 和形状特征。
- `runs/m5/clusters_summary.json`：k、silhouette、各簇的 centroid 和例子。

本次结果：k=5，silhouette 0.285（k=3 0.248，k=4 0.260，k=6 0.235），1,791 个概念。五类是昙花一现 781、新兴型 465、衰退型 331、爆发后衰退 177、复活型 37。

特征只用 span、active_ratio、peak_position、peak_share、decline_speed、recent_to_peak、volatility、years_since_peak 和事件 flag。total_count 和绝对年份只用于展示，不进入聚类，否则会按大小或年代分簇。类型名由 centroid 规则生成，是描述性的，不是金标。没有出现“常青型”，因为语料在增长，成熟概念的 share 也会自然下降，见 `D-020`。复活型只有 37 个，且复活事件有噪声。

## M4 Streamlit Demo

先同步环境：

```bash
uv sync
```

启动 demo：

```bash
uv run streamlit run src/concept_life/app.py
```

浏览器打开 `http://localhost:8501`。demo 只读预计算产物，不调用 API，断网可用。

demo 的“生命周期类型”页依赖 M5，第一次启动前先跑 `uv run python scripts/m5_clusters.py`，否则会提示缺少 `lifecycle_clusters.csv`。

九个页面：

- 总览：42,460 篇论文、10,957 个概念、3,003 个事件、30 个替代候选；年份直方图和事件分布。
- 概念时间线：选择概念，看 share 曲线和事件虚线，下面是事件表和证据。
- 生命周期类型：五类概念的柱状图、peak position × decline speed 散点、按类型看 top 30。
- 早期预测：只用前三年特征预测五类，同分布 5 折和出生年份切分，混淆矩阵和测试例子。
- 研究地图：Louvain 社区着色的概念图、社区表、桥接概念榜。
- 上升与替代：上升榜、候选替代表、人工复核表。
- 替代复核：逐对看时间线，标是/否/不确定，保存后算 precision。
- 趋势回测：模型和三条基线的指标，2020 窗口的预测表。
- 数据与方法：数据来源、方法、局限。

冒烟测试：

```bash
uv run python scripts/smoke_demo.py
```

预期九个页面各 0 异常。`streamlit.testing.v1.AppTest` 会真正执行页面代码，不只是检查服务器端口。

## M7 生命周期早期预测（扩展）

用出生后前三年的信号预测 M5 的五类生命周期。

```bash
uv run python scripts/m7_early.py
```

产物：

- `runs/m7/early_metrics.json`：5 折、时间切分、混淆矩阵、按类指标。
- `data/processed/early_predictions.csv`：2013-2018 出生概念的测试预测。

本次结果：1,333 个概念。同分布 5 折 accuracy 0.656、macro-F1 0.482，多数类 0.476；按出生年份切分，训练 ≤2012 共 365 个、测试 2013-2018 共 968 个，accuracy 0.666、macro-F1 0.455，多数类只有 0.073。昙花一现 F1 0.78，新兴型召回 0.35，复活型测试只有 4 个。

特征是 birth 到 birth+2 的 11 个早期指标，标签是 M5 的全轨迹聚类类型。时间切分是压力测试：晚出生概念的观察窗口更短，测试集类别分布偏向昙花一现和新兴型，所以 macro-F1 和按类 support 比 accuracy 更重要。类型标签是描述性的，不是现实命运，见 `D-023`、`D-024`。

## M8 研究地图（扩展）

用共现图做 Louvain 社区发现，画一张研究地图，并找桥接概念。

```bash
uv run python scripts/m8_map.py
```

产物：

- `data/processed/communities.csv`：500 个概念的社区、度数、betweenness。
- `data/processed/research_map_nodes.csv` 和 `research_map_edges.csv`：top 300 节点和裁剪后的边。
- `runs/m8/community_summary.json`：modularity、社区大小、每个社区的 top 概念、桥接榜。

本次结果：500 个节点、17,661 条边、8 个社区，modularity 0.328。地图画 300 个节点、1,537 条边。社区大致对应云/系统、ML/CV、软件、图/嵌入、数据库/搜索、概率/因果等。桥接榜前面是 Set (abstract data type)、Process (computing)、Artificial neural network、Scalability 等，很多是泛概念，不是真正的跨领域桥梁；这是概念标签噪声，见 `P-052`。

地图只画 top 300 节点和每个节点最强的 6 条边，避免糊成一团。Louvain 固定 seed=42，社区编号按大小和最小节点 id 排序，换 seed 会变。

交互原型在 `experiments/map_interactive.html`，由 `scripts/build_map_html.py` 生成。它用本地 D3 做力导向布局，支持拖动、缩放、点击节点聚焦、点击空白退出。聚焦时图例隐藏，视野自动平移到“节点 + 邻居”的包围盒。单文件版 `experiments/map_standalone.html` 把 D3 内联，进 git，下载后双击即可。还没接进 Streamlit demo，确认后再替换研究地图页。

## 产物格式

`data/processed/papers.jsonl` 每行一篇论文：

```json
{
  "id": "W...",
  "title": "Physics-informed machine learning",
  "year": 2021,
  "doi": "10.1038/s42254-021-00314-5",
  "cited_by_count": 4284,
  "concepts": [
    {"id": "Sk...", "name": "Machine learning", "level": 2, "score": 0.62}
  ],
  "fields": ["Artificial Intelligence", "Computer Science"]
}
```

`concepts` 已按 `min_level` 过滤，按 API 返回顺序截断到 `top_k_per_paper` 个，按 id 去重。

`data/processed/concept_series.csv` 每个概念每年一行：

| 列 | 含义 |
| --- | --- |
| `concept_id` | Acemap 概念 id，聚合主键 |
| `name` | 出现次数最多的展示名 |
| `year` | 年份 |
| `count` | 当年提到该概念的论文数 |
| `share` | `count` 除以当年论文总数 |

`data/processed/top_rising.csv` 上升榜：

| 列 | 含义 |
| --- | --- |
| `rank` | 名次 |
| `concept_id` | 概念 id |
| `name` | 展示名 |
| `prev_count` / `curr_count` | 前后窗口的论文数 |
| `prev_share` / `curr_share` | 前后窗口的占比 |
| `delta_share` | `curr_share - prev_share`，主排序键 |
| `growth` | `curr_share / prev_share`；历史为 0 时写 `new` |
| `is_new` | 历史窗口计数是否为 0 |

`runs/m0/config.json` 是本次运行合并后的完整配置。`runs/m0/summary.json` 是论文数、概念数、年份范围、各窗口论文数和上升榜前十。海报上的每个数字都应该能在这两个文件里追溯到。

## 配置

`configs/default.json`：

| 字段 | 含义 | 默认值 |
| --- | --- | --- |
| `data.cache_dir` | 缓存目录，相对项目根目录 | `../kg_search/cache` |
| `data.min_year` / `max_year` | 年份过滤 | 1990 / 2025 |
| `concepts.top_k_per_paper` | 每篇最多保留几个概念 | 10 |
| `concepts.min_level` | 概念层级下限，0 和 1 是泛概念 | 2 |
| `concepts.min_score` | 概念分数下限 | 0.0 |
| `windows.prev` | 前窗口的显式年份列表 | `[2015, 2016, 2017]` |
| `windows.curr` | 后窗口的显式年份列表 | `[2018, 2019, 2020]` |
| `rising.min_curr_count` | 后窗口最小论文数，过滤一次性概念 | 5 |
| `rising.top_k` | 输出多少个上升概念 | 30 |

`windows` 是显式年份列表，不是 `[start, end]` 区间。这是 `P-018` 记录过的坑。

## 测试

```bash
uv run python -m unittest discover -s tests -v
```

`uv run python -m unittest discover -s tests -v` 预期 32 个测试全部通过。直接用系统 Python 跑时，4 个 dashboard 和 2 个 map 测试会 skip，因为 pandas 和 networkx 只在 uv 环境里。测试覆盖：

- Acemap 解析、层级过滤、top-k 截断、缺年份拒绝。
- 领域过滤、topic 字段提取、无 topics 论文的保留策略。
- 概念停用词、所有概念被停用后丢弃论文。
- share 归一化：语料翻倍不会让概念看起来变热。
- 历史为 0 的概念标记为 `new`，不产生天文数字。
- 最小计数过滤。
- 完整生命周期：出生、爆发、峰值、衰退、死亡。
- 休眠与复活，短序列跳过。
- 来源字段和 Wikidata 提取。
- Pearson、Jaccard、合成替代对。
- precision@k、NDCG、趋势特征不读未来年份。
- 时间线补年、概念按总量排序、事件统计。
- K-means 分簇、silhouette、flash 特征。
- 早期特征不读未来年份、softmax 能学、macro-F1。
- Louvain 两个块、桥接节点 betweenness 最高。
- 替代复核 precision 只算已标注行，未标注不计入分母。

## 如何扩展

加一个新数据源：在 `src/concept_life/ingest.py` 写一个 `load_*` 函数，返回 `Paper` 列表，不要改下游模块。新数据源的字段映射写进 `docs/DECISIONS.md`。

加一个新分析器：在 `src/concept_life/` 新建模块，输入 `papers.jsonl` 或 `concept_series.csv`，输出一个独立文件。不要在一个模块里同时做统计、排名和画图。

加一个新想法：先在 `docs/IDEAS.md` 建一个 `I-NNN`，写清楚 DM 任务、数据、成本、评估、风险；认领时把它挪进 `docs/PLAN.md`，在 `docs/WORKLOG.md` 记一条，再动手。

加一个新界面：`app.py` 只读 `data/processed/` 和 `runs/` 的标准产物，不直接读原始响应。演示必须离线可跑。

## 已知限制

- M0 的缓存来自先导项目的 96 个查询，去重后 1187 篇，按 level>=2 过滤后 1054 篇。年份集中在 2019 到 2021，只能用来验证管线，不能当作全量语料。
- M1 的语料是 42,460 篇论文、10,957 个概念，来自 67,896 条原始记录。年份 1990 到 2025，但 2024 年只有 1,481 篇，2025 年只有 265 篇，Acemap 索引滞后，近两年不能用来判断死亡或趋势，见 `D-010`。
- 领域过滤是论文级的，概念级歧义仍在。`Pattern recognition (psychology)`、`Image (mathematics)`、`Feature (linguistics)`、`Voltage`、`Benchmark (surveying)` 这类标签靠停用词只能清掉一部分，真正的解法是别名合并或概念级领域分类，见 `P-025`、`I-010`、`I-014`。
- 没有 `topics` 的论文默认保留，本次有 206 篇，数量写在 `runs/m1/report/summary.json` 的 `missing_fields`。
- 约 32% 的记录没有摘要。生命周期分析不需要摘要，但后续做语义相似度时需要另找数据。
- Acemap 只返回 `referenced_works_count`，没有引用列表。citation 脉络需要 OpenAlex 或 Semantic Scholar，见 `I-005`。
- Acemap 的 `meta.count` 上限是 10000，不能当作语料真实总量，见 `P-020`。
- “死亡”指在语料中连续两年没有活跃论文，不是现实中消失。本次只有 3 个死亡事件，海报和报告要用“在语料中消失”这种措辞，见 `D-012`。
- 生命周期事件是规则驱动的，泛概念仍然会产生事件，比如 `Implementation`、`Citation`、`Path (computing)`。案例和海报只用黄金案例和人工挑过的概念，见 `P-029`。
- 早期年份论文少，`min_year_total=100` 只让峰值和爆发在语料足够大的年份计算，见 `P-027`。
- 替代检测是候选生成，不是自动替代。共现相似度偏向互补概念，RNN→Transformer 被漏掉，需要 citation 或文本信号，见 `P-031`、`I-005`。
- 替代 precision 依赖人工标注，标签是主观判断，未标注和“不确定”不计入分母。top-10 没标完时，不要把部分标注的 precision 当成完整精确率，见 `P-041`、`D-021`。
- 本次 20 对里 11 对由人初判，9 对由 AI 补判，5 对在讨论后改判；最终 20 对由人工确认。采用“焦点转移”标准，precision@10 0.60、@20 0.45；换成严格同功能标准会明显下降，见 `D-022`、`P-044`、`P-045`。
- 趋势预测的绝对精度不高，模型 precision@10 0.200，高于 growth 和 random 但远不到可靠预测。标签定义会改变结论，绝对增长下 frequency 基线很强，见 `D-014`。
- 趋势特征一度用全语料共现图，泄漏未来信息；现在每个窗口只用 T 年以前的图，见 `P-030`、`D-016`。
- 生命周期聚类只用形状特征，类型名是描述性的，不是金标。没有出现“常青型”，复活型只有 37 个且事件有噪声，见 `D-020`、`P-038`。
- 早期预测的标签是 M5 聚类类型，不是现实成败。时间切分里类别分布漂移严重，复活型测试只有 4 个，按类指标不稳定，见 `D-024`、`P-047`、`P-048`。
- 研究地图的桥接概念多为泛概念，betweenness 偏向 hub；地图只画 top 300 节点和每个节点最强 6 条边；社区是静态全语料，不做时间演化，见 `P-052`、`D-025`。
- demo 已实现，见 M4 到 M8；海报和两分钟讲稿还没做。

## 文档索引

| 文档 | 什么时候读 |
| --- | --- |
| `AGENTS.md` | 每次会话开始，先读这个 |
| `CLAUDE.md` | Claude Code 自动读，指向 `AGENTS.md` |
| `docs/PLAN.md` | 当前阶段、下一个任务、验收标准 |
| `docs/WORKLOG.md` | 最近发生了什么、结果如何、下一步 |
| `docs/PITFALLS.md` | 动手前看一遍，避免重复踩坑 |
| `docs/DECISIONS.md` | 想知道为什么这样设计 |
| `docs/IDEAS.md` | 想找扩展、备选方向、或换题 |
| `docs/DATA_SOURCES.md` | 想接 OpenAlex、Semantic Scholar、DBLP、arXiv 时 |
| `docs/AI_USAGE.md` | 写课程 AI 使用说明时 |

## 提交规范

```text
<type>(<scope>): <summary> [W-YYYYMMDD-NN]
```

`type` 用 `feat`、`fix`、`docs`、`refactor`、`test`、`chore`。`scope` 用 `data`、`graph`、`mine`、`predict`、`app`、`docs`。一个 commit 只做一件事。`data/`、`runs/`、缓存不进 git。

## 数据来源

- Acemap work search API：`https://acemap.info/api/v1/work/search`。
- 先导项目缓存：`../kg_search/cache/`。
- 可选引用数据：OpenAlex 或 Semantic Scholar，用于 `I-005` 的概念脉络。
