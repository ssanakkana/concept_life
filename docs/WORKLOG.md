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

**AI 交互**：

- 工具/模型：Claude Code。
- 关键提示：用户要求“现在是否有 milestone？如果有的话请先推进第一部分”；上一轮已确认 M0 完成、M1 是下一个里程碑。
- 输出采纳/拒绝：采纳“先验证 API、再冒烟、再全量后台抓取”的顺序；没有直接上全量，避免接口问题浪费 30 分钟。
