# AGENTS.md — AI 协作工作规范

这个仓库由 AI 承担主要实现工作，人类负责定方向、验收和展示。为了让下一个接手的 AI 不需要重新猜上下文，所有工作必须留下文字痕迹。commit 记录“代码变了什么”，本文件、工作日志和坑列表记录“为什么变、试过什么、哪里会踩坑”。

## 0. 每次会话开始，按顺序读

1. `docs/PLAN.md`：当前阶段、下一个任务、验收标准。
2. `docs/WORKLOG.md`：最后三条记录，了解最近发生了什么。
3. `docs/PITFALLS.md`：已知的坑，动手前先看一遍。
4. `docs/DECISIONS.md`：影响架构和数据协议的决定。
5. `docs/IDEAS.md`：扩展想法池。找扩展、换方向、或者 PLAN 做完了，再读这个。

读完再动手。不要凭记忆假设仓库状态。

## 1. 项目一句话

研究学术概念的完整生命周期：如何出现、如何增长、何时爆发、何时衰退、是否复活、是否被其他概念替代，并预测下一阶段的上升概念。

## 2. 当前阶段

见 `docs/PLAN.md` 的勾选状态。一次只做一个任务，不跨阶段并行。

## 3. 目录地图

- `src/concept_life/`：核心代码。
- `scripts/`：命令行入口。
- `configs/`：参数配置。
- `data/raw/`：原始响应，只增不改，git 忽略。
- `data/processed/`：清洗后的数据，可重建，git 忽略。
- `runs/`：每次运行的配置、指标、图，git 忽略。
- `docs/`：工作日志、决策、坑、计划、AI 使用记录。
- `tests/`：数据协议和时间切分的测试。

## 4. 常用命令

```bash
# M0：用 kg_search 的缓存跑通论文到概念时间线，不需要网络
python scripts/m0_from_cache.py

# 测试
python -m unittest discover -s tests -v
```

后续阶段的命令写进 `README.md`，不要散落在聊天记录里。

## 5. 每个任务的工作循环

1. 在 `docs/PLAN.md` 认领一个任务，写下一个可验证的完成标准。
2. 先写最小可运行版本，跑通再优化。不要一上来写完整框架。
3. 运行命令，把真实输出贴进 `docs/WORKLOG.md`。
4. 如果改了数据协议、评测协议或架构，写 `docs/DECISIONS.md`。
5. 如果踩了坑，写 `docs/PITFALLS.md`。
6. 提交 commit，message 带 worklog 编号。
7. 更新 `docs/PLAN.md` 的勾选状态和 `docs/WORKLOG.md` 的下一步。

## 6. 记录规范

### WORKLOG

每条记录一个编号，格式 `W-YYYYMMDD-NN`。必须包含：目标、做了什么、运行的命令、真实结果、踩坑、下一步、AI 交互摘要。模板见 `docs/WORKLOG.md` 顶部。结果必须是命令的真实输出，不能写“应该可以”。

### DECISIONS

每条 `D-NNN`，包含：背景、决定、备选方案、后果。任何影响数据 schema、评测口径、目录结构的决定都要写。

### PITFALLS

每条 `P-NNN`，包含：现象、原因、解决办法、相关文件。踩过一次的坑不要再踩第二次。新坑先记录，再修。

### AI_USAGE

每次会话结束前，把关键提示词、输出、采纳或拒绝的理由补进 `docs/AI_USAGE.md`。这门课要求提交 AI 使用说明，占 10 分，不要事后补编。

### IDEAS

新想法先写进 `docs/IDEAS.md`，给它一个 `I-NNN`，写清楚 DM 任务、数据、成本、评估、风险。不要有了想法就直接写代码。认领时把状态改成 `doing`，在 `docs/PLAN.md` 加任务，再动手。

## 7. Commit 规范

格式：

```text
<type>(<scope>): <summary> [W-YYYYMMDD-NN]
```

`type` 用 `feat`、`fix`、`docs`、`refactor`、`test`、`chore`。`scope` 用 `data`、`graph`、`mine`、`predict`、`app`、`docs`。

一个 commit 只做一件事。数据文件、缓存、`runs/` 不进 git。commit 后在 worklog 里补上 hash。

## 8. 数据与评测纪律

1. 原始响应只增不改。需要改解析，改代码，不删缓存。
2. 所有计数用“占当年论文总数的比例”，不用原始计数。语料在增长，原始计数会把“语料变大”误判成“概念变热”。
3. 概念节点用 Acemap 的 concept id，不用 display_name。display_name 会随时间变。
4. 只用 level 2 以上的概念，或者每篇取 score 最高的前 10 个。level 0 和 1 是“计算机科学”这种泛概念，会淹没一切。
5. 预测任务严格按时间切分。训练只能用 T 年以前的数据，不能随机切分。
6. “死亡”定义为“在语料中连续 N 年没有出现”，不是“世界上消失了”。海报和报告要用“在语料中消失”这种措辞。
7. 任何评测口径的修改都要写 DECISIONS。看过结果再改切分，就是 p-hacking。
8. 每次运行写 `runs/<run_id>/config.json` 和 `summary.json`，run_id 用 `YYYYMMDD-HHMMSS-<slug>`。M0 可以简化为 `runs/m0/`。

## 9. 禁止事项

- 不在没有运行命令的情况下声称完成。
- 不删除 `data/raw/` 或 `../kg_search/cache/`。
- 不提交大于 10MB 的文件。
- 不在一个 commit 里混入多个不相关的改动。
- 不把 `cited_by_count` 当成历史时间序列。它是当前值，不是当年的引用数。
- 不把共现当成因果关系，不把“候选替代”说成“替代”。
- 不引入新数据源而不写 DECISIONS。

## 10. 完成定义

一个任务算完成，需要同时满足：代码能跑；输出有真实数字；worklog 有记录；相关测试通过；PLAN 勾选；commit 已提交。缺一项都不算完成。
