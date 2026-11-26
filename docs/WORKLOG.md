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
