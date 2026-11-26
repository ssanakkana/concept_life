# 工作日志

每条记录一个编号，格式 `W-YYYYMMDD-NN`。结果必须贴命令的真实输出，不能写“应该可以”。commit 后在记录末尾补 hash。

## 模板

```markdown
## W-YYYYMMDD-NN · 日期 · 会话 NN

**目标**：
**做了什么**：
**命令**：
**结果**：
**踩坑**：
**下一步**：
**AI 交互**：
- 工具/模型：
- 关键提示：
- 输出采纳/拒绝：
```

## 索引

| 编号 | 日期 | 主题 | 状态 |
| --- | --- | --- | --- |
| W-20261126-01 | 2026-11-26 | 仓库脚手架与 M0 | 完成，61a0282 |
| W-20261126-02 | 2026-11-26 | 想法池与严格 README | 完成，61a0282 |
| W-20261126-03 | 2026-11-26 | M1 抓取器、领域过滤、质量报告 | 完成，6d89786 |
| W-20261126-04 | 2026-11-26 | M2 生命周期事件与黄金案例 | 完成，976f2cd |
| W-20261126-05 | 2026-11-26 | M3 替代候选与趋势预测 | 完成，a568409 |
| W-20261126-06 | 2026-11-26 | M4 Streamlit demo 与 uv 环境 | 完成，33e9755 |
| W-20261126-07 | 2026-11-26 | M5 生命周期聚类与 demo 页面 | 完成，9a12cbb |
| W-20261126-08 | 2026-11-26 | M6 替代复核页与 precision 评估 | 完成，1942441 |
| W-20261126-09 | 2026-11-26 | 替代候选 20 对标注与 precision 结果 | 完成，fa7ce82 |
| W-20261126-10 | 2026-11-26 | 焦点转移标准合并与重算 | 完成，589e5a1 |

## W-20261126-01 · 2026-11-26 · 会话 01

**目标**：建立 AI 协作规范，搭好最小框架，跑通从缓存到概念时间线的 M0。

**做了什么**：

- 建立 `concept_life` 目录，写入 `AGENTS.md`、`README.md`、计划、坑、决策、AI 使用说明。
- 实现 `schema.py`、`ingest.py`、`series.py`、`rising.py`。
- 实现 `scripts/m0_from_cache.py`，读取 `../kg_search/cache`，输出论文表、概念时间线、上升概念榜。
- 写 `tests/test_schema.py` 和 `tests/test_temporal.py`。

**命令**：

```bash
python scripts/m0_from_cache.py
python -m unittest discover -s tests -v
```

**结果**：

```text
papers: 1054
concepts: 2471
years: {'min': 1990, 'max': 2024}
papers_by_window: prev 2015-2017 = 175, curr 2018-2020 = 339
tests: 7 passed
```

top rising 前五：

```text
1. Artificial neural network      delta_share=+0.065470  growth=1.60  count=59
2. Health care                    delta_share=+0.035398  growth=new   count=12
3. Task (project management)      delta_share=+0.027847  growth=1.70  count=23
4. The Internet                   delta_share=+0.026549  growth=new   count=9
5. Process (computing)            delta_share=+0.024155  growth=2.41  count=14
```

产物：`papers.jsonl` 780KB，`concept_series.csv` 257KB，`top_rising.csv` 2.5KB。

**踩坑**：

- 先导缓存去重后 1187 篇，按 level>=2 过滤后剩 1054 篇。被丢掉的 133 篇只有泛概念，不能用来做生命周期分析。缓存只覆盖 96 个查询，年份集中在 2019 到 2021，不是全量语料。
- 上升榜被跨领域和歧义概念污染：`Health care`、`The Internet`、`Key (lock)`、`Focus (optics)`、`Domain (mathematical analysis)` 都进了前十。原因是 Acemap 把不同领域的同名词映射成同一个概念，且先导查询集会把医学、物理的论文带进来。M1 要加领域过滤、歧义概念停用词表和更高的最小计数。
- `growth` 在历史计数为 0 时会炸成 3e10 这种数字。已修：新增 `is_new`，历史为 0 时 `growth=None`，CSV 写 `new`。
- 配置里 `[2015, 2017]` 原本被当成“2015 和 2017 两年”，不是区间。已修：配置改成显式年份列表 `[2015, 2016, 2017]`。
- Acemap 的 `abstract` 有约 32% 缺失，但生命周期分析不需要摘要。
- Acemap 返回 `referenced_works_count`，没有 `referenced_works`，citation 脉络需要另找数据源。

**下一步**：

- 把上面三个新坑写进 `docs/PITFALLS.md`。
- M1：验证 Acemap 的 `size=100` 和深翻页，抓 4 万到 6 万篇；加领域过滤和歧义概念停用词表。
- 用全量语料重跑 M0，确认上升榜变得可解释。

**AI 交互**：

- 工具/模型：Claude Code。
- 关键提示：用户要求“AI 每次想法、做了什么、结果都记录在文档中，让后面的新 AI 知道做了什么、哪些是坑，和 commit 相辅相成”；要求“先从最简单的做起”，先做概念生命周期和未来焦点预测，做成可扩展框架。
- 输出采纳/拒绝：采纳“文档驱动 + 最小闭环 + 模块化产物”的方案；暂不做 RAG、不做个性化推荐、不引入 citation 数据源。

**Commit**：61a0282

## W-20261126-02 · 2026-11-26 · 会话 01（续）

**目标**：把扩展路线图沉淀成想法池，把 README 改成严格的结构与复现文档。

**做了什么**：

- 新建 `docs/IDEAS.md`，记录 15 个扩展想法（I-001 到 I-015）、两个备选方向（A 图质量重建、C 图谱对齐）和不建议做的方向。
- 重写 `README.md`，补当前状态、环境、完整目录树、文件职责、数据流、M0 复现步骤、产物格式、配置字段、测试、扩展方法、已知限制、文档索引、提交规范。
- 在 `AGENTS.md`、`CLAUDE.md`、`docs/PLAN.md` 加入 IDEAS 的读入和认领规则。

**命令**：

```bash
python -m unittest discover -s tests -v
python scripts/m0_from_cache.py
```

**结果**：

- 7 个测试通过。
- M0 复现数字不变：1054 篇论文，2471 个概念，年份 1990 到 2024。
- README 中的预期输出与实际输出一致。

**踩坑**：

- 无新增代码坑。README 初稿把 `data/` 和 `runs/` 写成“git 里是空的”，实际是被 `.gitignore` 完全忽略，已改成“运行产物，目录按需创建”。

**下一步**：

- 提交 commit：`docs: add idea backlog and strict reproduction README [W-20261126-02]`。
- M1：验证 Acemap `size=100` 和深翻页，抓 4 万到 6 万篇，加领域过滤。

**AI 交互**：

- 工具/模型：Claude Code。
- 关键提示：用户要求把扩展路线图记录到 TODO 或 IDEA 中，方便后来人做；README 要严格记录仓库结构以及如何复现。
- 输出采纳/拒绝：采纳“IDEAS 与 PLAN 分离、README 作为唯一结构说明”的方案；没有新增功能代码，只做文档。

**Commit**：61a0282

## W-20261126-03 · 2026-11-26 · 会话 01（续）

**目标**：推进 M1：验证 Acemap 接口，写抓取器、领域过滤、概念停用词、数据质量报告。

**做了什么**：

- 验证 `size=100`、page 2/10/50、窄查询 `total_pages` 都正常。
- 新增 `configs/queries.json`：170 个查询，分 `seeds`、`classic`、`recent` 三类。
- 新增 `scripts/crawl.py`：原始响应缓存、断点续抓、JSONL manifest、重试、离线模式、`--max-queries` 冒烟。
- 新增 `scripts/data_report.py`：年份直方图、字段分布、概念层级分布、缺失统计。
- `schema.py` 增加 `fields`，从 `topics` 提取 domain/field/subfield。
- `ingest.py` 增加 `matches_domain` 和 `stoplist`。
- 新增 `configs/m1.json`：缓存目录、CS 领域过滤、停用词、`min_curr_count=10`。
- 新增 `tests/test_ingest.py`，测试从 9 个增加到 11 个。

**命令**：

```bash
python scripts/crawl.py --max-queries 5 --pages 1 --out data/raw/acemap_smoke --manifest data/raw/acemap_smoke_manifest.jsonl --summary data/raw/acemap_smoke_summary.json
python scripts/m0_from_cache.py --config configs/m1.json --cache data/raw/acemap_smoke --out data/processed_smoke --runs runs/m1_smoke
python scripts/data_report.py --papers data/processed_smoke/papers.jsonl --config configs/m1.json --out runs/m1_smoke/report
python -m unittest discover -s tests -v
```

**结果**：

冒烟阶段：

- 5 个查询乘 1 页，500 条原始记录，12 秒，0 失败。
- 冒烟 M0：308 篇论文，731 个概念，年份 1992 到 2025。CS 字段覆盖 303/308，5 篇没有 topics，按 `keep_unknown_domain=true` 保留。

全量阶段：

- 抓取：679 次请求，67,896 条原始记录，0 失败，679 个文件，601MB，耗时 1,400 秒（约 23 分钟）。
- 去重和 CS 过滤后：42,460 篇论文，10,957 个概念，283,434 个概念实例，平均每篇 6.68 个概念。
- 去重率：42,460 / 67,896 = 62.5%。
- CS 覆盖：42,249 / 42,460 = 99.5%。206 篇没有 topics，按未知保留。
- 缺失 DOI：1,097 篇，占 2.6%。
- 年份范围：1990 到 2025。峰值 2021 年 7,106 篇，2022 年 7,024 篇，2023 年 5,091 篇，2024 年 1,481 篇，2025 年 265 篇。
- 窗口论文数：前窗口 2015-2017 共 4,236 篇，后窗口 2018-2020 共 12,851 篇。
- 11 个测试通过。

top rising 前十：

```text
1. Artificial neural network      delta_share=+0.0388  growth=1.49  count=1512
2. Pattern recognition (psychology) delta_share=+0.0382 growth=1.41 count=1701
3. Graph                          delta_share=+0.0340  growth=1.86  count=943
4. Deep learning                  delta_share=+0.0235  growth=1.36  count=1149
5. Image (mathematics)            delta_share=+0.0190  growth=1.47  count=760
6. Adversarial system             delta_share=+0.0165  growth=2.67  count=340
7. Transfer of learning           delta_share=+0.0141  growth=2.99  count=272
8. Feature (linguistics)          delta_share=+0.0127  growth=1.38  count=591
9. Embedding                      delta_share=+0.0126  growth=1.67  count=405
10. Transformer                   delta_share=+0.0125  growth=9.83  count=179
```

**踩坑**：

- 领域过滤只能过滤论文，不能过滤概念。`Pattern recognition (psychology)`、`Image (mathematics)`、`Feature (linguistics)`、`Voltage`、`Benchmark (surveying)`、`Leverage (statistics)`、`Robustness (evolution)`、`Adversarial system` 仍然会出现。停用词只能清掉最明显的几个，真正的解法是别名合并或概念级领域分类，见 `I-010` 和 `I-014`。
- Acemap 的 `meta.count` 上限是 10000，不能把它当作语料真实总量。抓取按 `total_pages` 和 `results` 长度停。
- 2024 和 2025 明显不完整，2024 只有 1,481 篇，2025 只有 265 篇。不能把这两年的缺失当作概念死亡或下降，生命周期分析主区间设为 1995-2023，见 `D-010`。
- 原始响应 601MB，全部在 `data/raw/`，已 gitignore，不进仓库。

**下一步**：

- 更新 README 的 M1 数字和已知限制。
- 提交 M1 commit。
- 进入 M2：先建黄金案例集，再做出生、爆发、峰值、衰退、复活、死亡的事件规则；分析区间按 `D-010` 用 1995-2023。

**AI 交互**：

- 工具/模型：Claude Code。
- 关键提示：用户要求“现在是否有 milestone？如果有的话请先推进第一部分”；上一轮已确认 M0 完成、M1 是下一个里程碑。
- 输出采纳/拒绝：采纳“先验证 API、再冒烟、再全量后台抓取”的顺序；没有直接上全量，避免接口问题浪费 30 分钟。

**Commit**：6d89786

## W-20261126-04 · 2026-11-26 · 会话 01（续）

**目标**：推进 M2：给 42,460 篇语料里的概念打生命周期事件，用黄金案例检查规则是否和常识一致。

**做了什么**：

- 新增 `src/concept_life/mine.py`：基于 share 的六类事件，出生、爆发、峰值、衰退、休眠、复活、死亡。
- 新增 `scripts/m2_events.py`：读 `concept_series.csv`，输出 `events.jsonl`、`concept_events.csv`、`runs/m2/summary.json`。
- 新增 `configs/m2.json`：分析区间 1995-2023，阈值和停用规则。
- 新增 `configs/golden_cases.json` 和 `scripts/check_golden_cases.py`：9 个概念、30 条年份检查。
- 新增 `tests/test_mine.py`：完整生命周期、休眠复活、短序列跳过，测试从 11 个增加到 15 个。
- `schema.py` 增加 `Paper.source` 和 `Concept.wikidata`，为以后接 OpenAlex 做跨源对齐。
- 新增 `docs/DATA_SOURCES.md`：接 Acemap 以外数据源的五个步骤、OpenAlex 字段映射、跨源合并规则和常见坑。

**命令**：

```bash
python scripts/m2_events.py --config configs/m2.json
python scripts/check_golden_cases.py
python -m unittest discover -s tests -v
```

**结果**：

- 10,957 个概念里 1,793 个有事件，共 3,003 个事件。
- 事件分布：出生 1,793，爆发 508，峰值 367，衰退 234，休眠 49，复活 49，死亡 3。
- 黄金案例 30/30 通过，覆盖 SVM、RNN、CNN、Deep learning、GAN、Transformer、Federated learning、Knowledge graph、Blockchain。
- 15 个测试通过。
- 3 个死亡案例：Ledger（2020）、Distributed ledger（2022）、Service-level agreement（2022）。

**踩坑**：

- 42k 语料里“真正消失”的概念极少，只有 3 个。大多数概念是衰退或休眠，不是死亡。海报上要写“在语料中消失”，不要写“概念死了”。
- 1990 到 1999 年每年只有 37 到 79 篇论文，小概念的 share 会被放大。加了 `min_year_total=100`，峰值和爆发只在当年语料至少 100 篇时才计算。
- 平缓序列上的 z-score 会把微小变化判成爆发。加了 `burst_min_delta=0.002` 和 `burst_min_rel=0.2`，要求绝对占比和相对增幅都够大。
- 泛概念仍然会产生事件，比如 `Implementation`、`Citation`、`Path (computing)`。这是概念级噪声，停用词和别名合并只能缓解，见 `P-029`。

**下一步**：

- 更新 README 的 M2 复现步骤、目录树和已知限制。
- 提交 M2 commit。
- M3：候选替代检测和趋势预测。替代检测用负相关加语义相似度，趋势预测用时间切分和 precision@k。

**AI 交互**：

- 工具/模型：Claude Code。
- 关键提示：用户同意继续推进 M2，并问“如果后面想提取 Acemap 以外的内容应该怎么做”。
- 输出采纳/拒绝：采纳“先写黄金案例再调规则”的顺序；采纳 `min_year_total`、`burst_min_delta`、`burst_min_rel` 三个数据质量修正；没有引入 citation 数据源，citation 脉络留到 `I-005`。

**Commit**：976f2cd

## W-20261126-05 · 2026-11-26 · 会话 01（续）

**目标**：推进 M3：候选替代检测和趋势预测。

**做了什么**：

- 新增 `src/concept_life/replace.py`：共现支持度、Jaccard、Pearson、候选替代检测。
- 新增 `src/concept_life/predict.py`：趋势特征、相对/绝对标签、逻辑回归、precision@k、NDCG、三窗口回测。
- 新增 `scripts/m3_replacements.py`、`scripts/m3_trend.py`、`configs/m3.json`。
- 新增 `tests/test_replace.py`、`tests/test_predict.py`，测试从 15 个增加到 20 个。
- 修复趋势预测的时间泄漏：每个窗口只用 T 年以前的共现图建 degree 和邻居。
- `requirements.txt` 增加 numpy。

**命令**：

```bash
python scripts/m3_replacements.py
python scripts/m3_trend.py
python -m unittest discover -s tests -v
```

**结果**：

替代检测：

- 234 个衰退概念，523 个上升概念，52,349 个共现对，30 个候选对。
- 前十：Cryptocurrency→Blockchain、Pascal (unit)→Segmentation、Java→Source code、Machine translation→Language model、Machine translation→Transformer、Workload→Load balancing、Cryptocurrency→Smart contract、Mobile edge computing→Enhanced Data Rates for GSM Evolution、Distributed learning→Federated learning、Query language→SQL。
- 人工 spot check：Machine translation→Transformer 和 Distributed learning→Federated learning 合理；Pascal、Workload、Java 是标签噪声。已知的 RNN→Transformer 没有被检出，因为两者直接共现太少。
- `runs/m3/replacement_review.csv` 留了 `valid_1_0` 空列，等人填。

趋势预测：

- 窗口 2016、2018、2020，每窗 441 到 502 个候选，20 个正例。
- 平均指标：模型 precision@10 0.200、precision@20 0.150、nDCG@20 0.208；growth 基线 0.100、0.133、0.107；random 0.033、0.067、0.085；frequency 0.000、0.017、0.011。
- 2020 窗口的模型 top 20 里有 Code generation、Joint (building)、Closed captioning 等命中，也有大量概念标签噪声。
- 模型在 precision 上高于 growth 和 random，但绝对值不高，逐窗口方差大。

**踩坑**：

- 趋势特征一度用全语料共现图算 degree 和邻居，泄漏了未来信息，precision@10 虚高到 0.467。改成每个窗口只用 T 年以前的图后，降到 0.200。这是 `D-016`。
- 替代检测的共现相似度偏向互补概念，不是替代概念。RNN→Transformer 因为直接共现少被漏掉。真正做替代需要 citation 或文本信号，见 `I-005`。
- 标签定义决定结论：绝对增长下 frequency 基线很强；相对增长加最小未来份额后，模型才有 lift。这是 `D-014`。
- 概念级标签噪声仍是主要错误源，`P-025` 没有根治。

**下一步**：

- 更新 README、PLAN、PITFALLS、DECISIONS。
- 提交 M3 commit。
- M4：Streamlit demo、A1 海报、两分钟讲稿。
- 如果时间富余，用 citation 或文本信号改进替代检测。

**AI 交互**：

- 工具/模型：Claude Code。
- 关键提示：用户要求先推 M1 和 M2，再推进 M3。
- 输出采纳/拒绝：采纳“替代候选加人工复核”和“相对增长标签加时间感知图”的方案；没有引入新数据源；承认替代检测的负结果，不把它包装成自动替代。

**Commit**：a568409

## W-20261126-06 · 2026-11-26 · 会话 01（续）

**目标**：推进 M4：用 uv 管理环境，做 Streamlit demo 骨架，跑通五个页面。

**做了什么**：

- 新增 `pyproject.toml` 和 `uv.lock`，用 `uv sync` 创建 `.venv`，安装 streamlit、pandas、altair、numpy、requests。
- 新增 `src/concept_life/dashboard.py`：只读数据加载和 DataFrame 变换。
- 新增 `src/concept_life/app.py`：五个页面，总览、概念时间线、上升与替代、趋势回测、数据与方法。
- 新增 `scripts/smoke_demo.py`：用 `streamlit.testing.v1.AppTest` 执行五个页面。
- 新增 `tests/test_dashboard.py`：时间线补年、概念排序、事件统计，测试从 20 个增加到 23 个。
- `requirements.txt` 改为 pip 兼容清单，uv 成为主环境。
- `use_container_width` 全部换成 `width="stretch"`，消除 Streamlit 1.67 的弃用警告。

**命令**：

```bash
uv sync
uv run streamlit run src/concept_life/app.py
uv run python scripts/smoke_demo.py
uv run python -m unittest discover -s tests -v
```

**结果**：

- uv 0.8.14，Python 3.13.15，streamlit 1.67.0，pandas 3.1.1，numpy 2.4.6。
- 五个页面全部 0 异常。
- 23 个测试通过；直接用系统 Python 跑时，3 个 dashboard 测试 skip，因为 pandas 只在 uv 环境里。
- demo 只读预计算产物，不调用 API，断网可用。

**踩坑**：

- Streamlit 1.67 提示 `use_container_width` 将在 2025-12-31 后移除，改用 `width="stretch"`。
- 只检查 `http://localhost:8501/_stcore/health` 不能证明页面能跑，必须用 `AppTest` 真正执行页面代码。
- pandas 读带 BOM 的 CSV 时，`encoding="utf-8-sig"` 才不会把第一列读成 `﻿...`。

**下一步**：

- 做 A1 海报和两分钟讲稿。
- 把 demo 的截图或 GIF 放进 Canvas 讨论帖。
- 提交 M4 commit。

**AI 交互**：

- 工具/模型：Claude Code。
- 关键提示：用户同意推进 M4，并问能不能用 uv 管理本地虚拟环境。
- 输出采纳/拒绝：采纳 uv + `pyproject.toml` + `uv.lock` 作为主环境；demo 先做五页骨架，不做实时 API 和图数据库。

**Commit**：33e9755

## W-20261126-07 · 2026-11-26 · 会话 01（续）

**目标**：实现 I-003 生命周期聚类，并接到 demo 的“生命周期类型”页。

**做了什么**：

- 新增 `configs/m5.json`：分析区间、active 阈值、k 搜索范围、seed。
- 新增 `src/concept_life/cluster.py`：形状特征、numpy K-means、silhouette、k 选择、规则标签。
- 新增 `scripts/m5_clusters.py`：读序列、总量、事件，写 `lifecycle_clusters.csv` 和 `runs/m5/clusters_summary.json`。
- 新增 `tests/test_cluster.py`：K-means 两个簇、silhouette、flash 特征。
- `dashboard.py` 和 `app.py` 增加“生命周期类型”页：五类柱状图、peak position × decline speed 散点、按类型看 top 30。
- `AGENTS.md` 增加规则：实现 IDEA 后必须把 `docs/IDEAS.md` 状态改成 done 并写产出路径。
- `docs/IDEAS.md` 把 I-003 标成 done。

**命令**：

```bash
uv run python scripts/m5_clusters.py
uv run python -m unittest discover -s tests -v
uv run python scripts/smoke_demo.py
```

**结果**：

- k=5，silhouette 0.285；k=3 是 0.248，k=4 是 0.260，k=6 是 0.235。
- 1,791 个概念入聚类。
- 五类：昙花一现 781，新兴型 465，衰退型 331，爆发后衰退 177，复活型 37。
- 26 个测试通过，demo 六页 0 异常。
- 典型例子：昙花一现有 Construct (python library)、Visualization；新兴型有 Gene、Embedding、Transformer；衰退型有 Concurrency、Cache；爆发后衰退有 ANN、Deep learning；复活型有 Random forest、Differential privacy。

**踩坑**：

- 第一版 total 把 1995 年以前的论文也算进去，聚类集合 1,837 比事件集合 1,793 多。改成只在分析区间内计数后对齐到 1,791。
- 没有出现“常青型”。在增长语料里，长期概念的 share 也会自然下降，所以“衰退型”是语料内份额下降，不是领域死亡。
- 复活型只有 37 个，且复活事件本身有噪声，标签只能当描述。
- K-means 的 cluster index 是任意的，必须用 centroid 规则命名，不能直接按编号叫“类型 0”。

**下一步**：

- 提交 M5 commit 并推送。
- 可选：替代候选人工标注页，给 `valid_1_0` 一个可视化入口。
- 最后统一做海报和两分钟讲稿。

**AI 交互**：

- 工具/模型：Claude Code。
- 关键提示：用户要求“某个 IDEA 如果在项目中实现了记得标注”，并指定先做生命周期聚类。
- 输出采纳/拒绝：采纳“形状特征、K-means、silhouette 选 k、规则命名”的方案；没有把 total_count 或绝对年份放进聚类特征，避免按大小或年代分簇。

**Commit**：9a12cbb

## W-20261126-08 · 2026-11-26 · 会话 01（续）

**目标**：做替代候选人工复核页，让队友在 demo 里标 1/0/不确定，并算 precision@10/20。

**做了什么**：

- `dashboard.py` 增加 `load_review` 和 `review_precision`：按 rank 合并 `replacements.csv` 和人工标签，只对已标注行算精确率。
- `app.py` 增加“替代复核”页：候选选择、上一对/下一对、两条时间线、Jaccard 和相关系数、是/否/不确定、备注、保存。
- 人工标签存到 `data/labels/replacement_review.csv`，进 git；`runs/m3/replacement_review.csv` 只作为初始模板。
- 新增 `scripts/evaluate_replacements.py`：从标签文件算 precision@10 和 precision@20，写 `runs/m3/replacement_metrics.json`。
- `tests/test_dashboard.py` 增加未标注行不计入分母的测试，测试从 26 个增加到 27 个。
- `scripts/smoke_demo.py` 覆盖七个页面。

**命令**：

```bash
uv run python -m unittest discover -s tests -v
uv run python scripts/smoke_demo.py
uv run python scripts/evaluate_replacements.py
```

**结果**：

- 27 个测试通过。
- demo 七页 0 异常。
- 当前标签 0/20，等队友逐对标；`evaluate_replacements.py` 能正常输出“no labels”。

**踩坑**：

- 页面的 precision 只在已标注行上算。如果 top-10 只标了 3 个，precision 是 3 个里的比例，不是 top-10 的精确率。页面上写了“已标注 X/10”。
- 页面保存时会把完整的候选字段写回标签文件，schema 比模板宽。`load_review` 只取 rank、valid、notes，所以不影响。
- 标签是人工判断，不是模型输出；海报上要写清楚标注人数和口径。
- 标签一开始写在 `runs/` 里，但 `runs/` 被 git 忽略，队友标完留不下来。已迁到 `data/labels/replacement_review.csv`，空表也提交，模板留在 `runs/m3/`。

**下一步**：

- 让队友花十分钟把 20 对标完，跑 `evaluate_replacements.py`。
- 最后统一做海报和两分钟讲稿。

**AI 交互**：

- 工具/模型：Claude Code。
- 关键提示：用户问“替代候选人工标注页是什么意思”，解释后说“不错挺好的，继续推进”。
- 输出采纳/拒绝：采纳“demo 内标注 + CSV 保存 + 单独评估脚本”的方案；没有引入新的标注平台或数据库。

**Commit**：1942441

**后续修复**：d96e47e 把人工标签从 `runs/m3/replacement_review.csv` 迁到 `data/labels/replacement_review.csv`，让标签进 git。

## W-20261126-09 · 2026-11-26 · 会话 01（续）

**目标**：完成替代候选的人工标注，算出 precision@10 和 precision@20。

**做了什么**：

- 用户先标了 11 对，写了备注，包括 3 个“可能是 / 应该是”的 1。
- AI 看了剩下的 9 对的时间线和备注，按“宽泛接替”标准补标：
  - 1 表示新概念在同一研究生态位里接替旧概念的关注度，包括具体化、平台化或焦点转移。
  - 0 表示互补、父子组件、或概念标签噪声。
- 20 对全部标完，标签存 `data/labels/replacement_review.csv`，指标存 `data/labels/replacement_metrics.json`。

**命令**：

```bash
uv run python scripts/evaluate_replacements.py --out data/labels/replacement_metrics.json
```

**结果**：

- 20/20 已标注。
- 4 对被判为有效：Cryptocurrency→Blockchain（1）、Distributed learning→Federated learning（9）、Query language→SQL（10）、Utility computing→Edge computing（11）。
- precision@10 = 0.300（top-10 里 3 个有效），precision@20 = 0.200（20 个里 4 个有效）。
- AI 补标的 9 对里只有 Cryptocurrency→Blockchain 判 1，其余 8 对判 0：Pascal→Segmentation、Java→Source code、Cryptocurrency→Smart contract、Word (group theory)→Language model、Search engine→SQL、Genetic algorithm→Selection、Static analysis→Malware、Replication (statistics)→Latency (audio)。

**踩坑**：

- 替换的标准会直接改变 precision。用“宽泛接替”标准，precision@10 是 0.30；用“严格同功能替换”标准，Cryptocurrency→Blockchain、Query language→SQL 这些都要改判 0，precision 会降到 0.10 左右。海报必须写清楚标准，见 `D-022`。
- 9 对是 AI 补标的，不是人类金标。用户标了 11 对，AI 标了 9 对；报告里要写“1 人 + AI 第二判断”，不能写成“两个人独立标注”。
- 概念标签噪声仍然存在，Pascal (unit)、Word (group theory)、Replication (statistics) 这些对是标签错误，不是替代。

**下一步**：

- 更新 README、PLAN、IDEAS、DECISIONS、PITFALLS 的结果。
- 提交标签和指标，推送仓库。
- 最后做海报和两分钟讲稿。

**AI 交互**：

- 工具/模型：Claude Code。
- 关键提示：用户说“能评估我的我都评估了，剩下的我无法判断，你也可以看看我写的注释，然后自己做一下判断”。
- 输出采纳/拒绝：采纳“宽泛接替”标准补标 9 对；没有改用户已标的 11 对；在文档里明确 9 对是 AI 第二判断，不是人类金标。

**Commit**：fa7ce82

## W-20261126-10 · 2026-11-26 · 会话 01（续）

**目标**：按用户确认的“焦点转移”标准合并替代标签，重算 precision。

**做了什么**：

- 用户同意 5 个改判：rank 4、5、7、13、18 改为 1。
- 把 proposal 合并进 `data/labels/replacement_review.csv`，保留用户原备注，补全 20 对理由。
- 重算 `data/labels/replacement_metrics.json`。
- 更新 README、PLAN、IDEAS、DECISIONS、PITFALLS。

**命令**：

```bash
uv run python scripts/evaluate_replacements.py --out data/labels/replacement_metrics.json
uv run python -m unittest discover -s tests -v
uv run python scripts/smoke_demo.py
```

**结果**：

- 9/20 有效：rank 1 Cryptocurrency→Blockchain、4 Machine translation→Language model、5 Machine translation→Transformer、7 Cryptocurrency→Smart contract、9 Distributed learning→Federated learning、10 Query language→SQL、11 Utility computing→Edge computing、13 Residual neural network→Pruning、18 Static analysis→Malware。
- precision@10 = 0.600，precision@20 = 0.450。
- 27 个测试通过，demo 七页 0 异常。

**踩坑**：

- 标准从“严格/宽泛混合”改成“焦点转移”，precision 从 0.30/0.20 到 0.60/0.45。不是模型变好，是口径变了；海报必须写清楚标准。
- 9 对最初由 AI 补判，5 对讨论后改判，最终人工确认；报告写“1 人 + AI 辅助复核”，不是双人独立标注。
- 焦点转移标准偏宽，严格同功能替换会低很多；不要和别的系统直接比。

**下一步**：

- 提交并推送。
- 最后做海报和两分钟讲稿。

**AI 交互**：

- 关键提示：用户说“同意，我都同意。可以解释就行。”
- 输出采纳/拒绝：采纳全部 5 个改判；保留用户原备注；在文档里写清标准变化和标注人。

**Commit**：589e5a1
