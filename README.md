# Concept Life

学术概念的生命周期挖掘：兴起、发展、爆发、衰退、复活、被替代，以及下一阶段的上升概念预测。

这个仓库是 AI3602 期末项目的代码框架。先导项目在 `../kg_search/`，本仓库复用它的 Acemap 缓存，但从一个更小、更可扩展的问题重新开始：一个概念在语料里是怎么活过一生的。

## 当前状态

| 阶段 | 内容 | 状态 |
| --- | --- | --- |
| M0 | 从先导缓存到论文表、概念时间线、上升概念榜 | 已实现 |
| M1 | Acemap 全量抓取、领域过滤、数据质量报告 | 已实现，42,460 篇论文，10,957 个概念 |
| M2 | 生命周期事件：出生、爆发、峰值、衰退、复活、死亡 | 未实现 |
| M3 | 候选替代检测、趋势预测 | 未实现 |
| M4 | Streamlit demo、海报、讲稿 | 未实现 |

扩展想法和备选方向在 `docs/IDEAS.md`。当前仓库已实现 M0 和 M1 的代码，M2 到 M4 还没有，不要假设它们存在。

## 环境

- Python 3.10 及以上。代码用了 `int | None` 这种类型标注。
- M0 只用 Python 标准库，不需要 `pip install`。
- M1 抓取需要 `requests`，已经写在 `requirements.txt` 里。
- M2 之后的 `networkx`、`streamlit`、`matplotlib`、`pandas` 仍按需安装，当前是注释状态。

## 仓库结构

```text
concept_life/
├── AGENTS.md                 # AI 协作规范，唯一事实来源
├── CLAUDE.md                 # Claude Code 的入口，指向 AGENTS.md
├── README.md                 # 本文件：结构、复现、产物格式
├── requirements.txt          # 依赖，M0 不需要
├── .gitignore                # 忽略数据、运行产物、缓存
├── configs/
│   ├── default.json          # M0 配置：缓存路径、年份、窗口、阈值
│   ├── m1.json               # M1 配置：全量缓存、CS 领域过滤、停用词
│   └── queries.json          # 170 个抓取查询，分 seeds/classic/recent
├── docs/
│   ├── PLAN.md               # M0 到 M4 的阶段、任务、验收标准
│   ├── WORKLOG.md            # 每次工作做了什么、结果、坑、下一步
│   ├── PITFALLS.md           # 已知的坑，动手前先看
│   ├── DECISIONS.md          # 影响架构和评测口径的决定
│   ├── IDEAS.md              # 扩展想法池，带 ID、成本、评估、风险
│   └── AI_USAGE.md           # 课程提交用的 AI 使用说明
├── scripts/
│   ├── m0_from_cache.py      # M0 命令行入口
│   ├── crawl.py              # M1 Acemap 抓取，缓存、断点续抓、manifest
│   └── data_report.py        # M1 数据质量报告：年份、字段、层级、缺失
├── src/
│   └── concept_life/
│       ├── __init__.py       # 包版本
│       ├── config.py         # 默认配置和 JSON 覆盖
│       ├── schema.py         # Paper / Concept 数据契约和 Acemap 解析
│       ├── ingest.py         # 读缓存、去重、写 JSONL
│       ├── series.py         # 逐年计数、展示名
│       └── rising.py         # share 归一化的上升榜
├── tests/
│   ├── test_schema.py        # 解析、层级过滤、top-k、领域过滤
│   ├── test_ingest.py        # 停用词、空概念论文丢弃
│   └── test_temporal.py      # share 归一化、new 概念、最小计数
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
| `queries.json` | 170 个抓取查询，分 `seeds`、`classic`、`recent` | 不保证每个查询都有结果 |
| `m1.json` | M1 覆盖配置：全量缓存、CS 过滤、停用词 | 不改变 `default.json` 的 M0 行为 |

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
python scripts/m0_from_cache.py
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
python scripts/m0_from_cache.py
```

```powershell
# PowerShell
Remove-Item -Recurse -Force data\processed, runs\m0
python scripts/m0_from_cache.py
```

M0 不发起网络请求。断网也能跑。

## M1 全量抓取

M1 会真正访问 Acemap，需要 `requests`。先安装依赖：

```bash
pip install -r requirements.txt
```

抓取 170 个查询，每个查询 4 页，每页 100 条：

```bash
python scripts/crawl.py --pages 4 --size 100
```

产物：

- `data/raw/acemap/`：原始响应文件，文件名是查询哈希加页码。
- `data/raw/acemap_manifest.jsonl`：每次请求的状态、结果数、错误。
- `data/raw/crawl_summary.json`：查询数、请求数、缓存命中、失败数、耗时。

断点续抓：直接重跑同一条命令，已有文件会跳过。只想检查缓存覆盖：

```bash
python scripts/crawl.py --offline --pages 4 --size 100
```

抓完用 M1 配置重跑 M0，再做质量报告：

```bash
python scripts/m0_from_cache.py --config configs/m1.json --runs runs/m1
python scripts/data_report.py --papers data/processed/papers.jsonl --config configs/m1.json
```

`configs/m1.json` 做三件事：把缓存目录指向 `data/raw/acemap`，只保留 `topics` 里含 `computer science` 的论文，丢掉 `Field (mathematics)`、`Key (lock)` 这类歧义概念。没有 `topics` 的论文默认保留，数量会写进报告。

报告产物在 `runs/m1/report/`：

- `year_histogram.csv` 和 `year_histogram.txt`：逐年论文数。
- `field_counts.csv`：领域和子领域分布。
- `level_counts.csv`：概念层级分布。
- `summary.json`：论文数、概念数、缺失 DOI、缺失 topics、前后窗口论文数。

本次全量结果：679 次请求，67,896 条原始记录，0 失败，601MB。去重和 CS 过滤后 42,460 篇论文，10,957 个概念，283,434 个概念实例，平均每篇 6.68 个。CS 覆盖 99.5%，206 篇没有 topics。年份 1990 到 2025，2021 年峰值 7,106 篇，2024 年 1,481 篇，2025 年 265 篇。近两年不完整，生命周期分析主区间设为 1995-2023，见 `D-010`。如果某年论文太少，先扩查询集，不要直接做生命周期事件。

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
python -m unittest discover -s tests -v
```

预期 11 个测试全部通过。测试覆盖：

- Acemap 解析、层级过滤、top-k 截断、缺年份拒绝。
- 领域过滤、topic 字段提取、无 topics 论文的保留策略。
- 概念停用词、所有概念被停用后丢弃论文。
- share 归一化：语料翻倍不会让概念看起来变热。
- 历史为 0 的概念标记为 `new`，不产生天文数字。
- 最小计数过滤。

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
- “死亡”指在语料中连续 N 年没有出现，不是现实中消失。海报和报告要用“在语料中消失”这种措辞。
- 当前没有 demo。M4 才做，接口已经按“只读标准产物”设计。

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
