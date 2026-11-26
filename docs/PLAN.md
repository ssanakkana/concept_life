# 计划

扩展想法在 `docs/IDEAS.md`。认领一个想法时，把它的 `I-NNN` 写进本文件，并在 `docs/WORKLOG.md` 开一条记录。

## 原则

先从最简单的闭环开始。M0 用现有缓存跑通，不抓网。每一步都有可验证的产出，做完再进下一步。一次只推进一个里程碑，不跨阶段并行。

## M0 最小闭环：从缓存到概念时间线

用 `../kg_search/cache` 的论文缓存，产出论文表、概念时间线和上升概念榜。不依赖网络和第三方库。

验收：

- 脚本离线运行，10 秒内完成。
- `papers.jsonl`、`concept_series.csv`、`top_rising.csv` 都存在。
- worklog 记录论文数、概念数、top rising 前五。
- `python -m unittest discover -s tests -v` 通过。

任务：

- [x] 写 schema 和 Acemap 解析
- [x] 写逐年计数和 share 归一化
- [x] 写 rising 表
- [x] 跑通并记录
- [ ] 提交 commit

M0 结果：1054 篇论文，2471 个概念，7 个测试通过。上升榜仍有跨领域和歧义概念噪声，留到 M1 处理。

## M1 全量语料：抓取与概念时间线

目标：用 Acemap API 抓 4 万到 6 万篇论文，建全量概念时间线。

验收：

- 原始响应落盘，断点可续。
- 年份直方图输出，每年论文数可见。
- 概念时间线覆盖至少 1 万个 level 2 以上的概念。
- 记录抓取耗时、失败率、去重率。

任务：

- [x] `scripts/crawl.py`
- [x] 年份分布检查，`scripts/data_report.py`
- [x] 概念归一化，id 为键，name 为标签
- [x] 领域过滤与概念停用词
- [x] 全量抓取完成并重跑 M0
- [x] 记录全量数字，更新 README

M1 结果：67,896 条原始记录，去重和 CS 过滤后 42,460 篇论文、10,957 个概念。CS 覆盖 99.5%。2024 和 2025 不完整，生命周期分析主区间设为 1995-2023，见 `D-010`。

## M2 生命周期事件：出生、爆发、峰值、衰退、复活、死亡

目标：给每个概念打上生命周期事件，输出 `events.jsonl`。

验收：

- 至少 3 个案例（如 transformer、diffusion model、graph neural network）的事件年份符合常识。
- 事件规则写在 `docs/DECISIONS.md`。
- 事件表可被 demo 直接读取。

任务：

- [x] 事件规则
- [x] 事件检测
- [x] 建 9 个黄金案例（SVM、RNN、CNN、Deep learning、GAN、Transformer、Federated learning、Knowledge graph、Blockchain），人工标注大致事件年份，作为回归测试和海报素材
- [x] 案例检查，30/30 通过
- [ ] 事件可视化，留到 M4

M2 结果：1,793 个概念有事件，共 3,003 个事件。出生 1,793，爆发 508，峰值 367，衰退 234，休眠 49，复活 49，死亡 3。死亡很少，因为 42k 语料里概念很少完全消失，见 `D-012`。

## M3 替代检测与趋势预测

目标：检测候选替代对，预测下一阶段的上升概念。

验收：

- 替代检测给出 top-10 候选对，附相关性和相似度证据。
- 趋势预测按时间切分，报告 precision@k 和 NDCG@k，附基线。
- 失败案例写进 worklog。

任务：

- [x] 替代检测，输出候选对和人工复核表
- [x] 趋势特征
- [x] 时间切分评估，每个窗口只用 T 年以前的图
- [x] 基线对比，frequency、growth、random

M3 结果：替代检测给出 30 个候选对，Machine translation→Transformer 和 Distributed learning→Federated learning 合理，但共现相似度偏向互补概念，需要人工复核。趋势预测在三窗口回测中模型 precision@10 0.200，growth 基线 0.100，random 0.033；绝对精度不高，概念标签噪声是主要误差源。

## M4 演示与展示

目标：Streamlit demo、A1 海报、两分钟讲稿。

验收：

- demo 离线可跑，年份滑块、概念卡片、上升榜、替代箭头都能用。
- 海报六块内容齐全。
- 两分钟讲稿练过三遍。
- AI 使用说明整理完成。

任务：

- [x] demo，七个页面，uv 环境，AppTest 冒烟 0 异常
- [ ] 海报
- [ ] 讲稿
- [ ] AI 使用说明
- [ ] 提交材料

M4 demo 结果：`uv sync` 创建 `.venv`，`uv run streamlit run src/concept_life/app.py` 启动。七个页面是总览、概念时间线、生命周期类型、上升与替代、替代复核、趋势回测、数据与方法。`uv run python scripts/smoke_demo.py` 全部 0 异常。海报和两分钟讲稿还没做。

## M5 生命周期聚类（扩展）

目标：按曲线形状聚类，输出类型表和 demo 页面。

验收：

- K-means 的 k 由 silhouette 选择。
- 类型名有规则，不靠 cluster index。
- demo 的生命周期类型页可用。
- 测试覆盖 K-means、silhouette、flash 特征。

任务：

- [x] 特征：span、peak position、decline speed、recent/peak、volatility、事件 flag
- [x] K-means + silhouette，k=3 到 6
- [x] 标签规则
- [x] demo 页面
- [x] 测试

M5 结果：k=5，silhouette 0.285（k=3 0.248，k=4 0.260，k=6 0.235），1,791 个概念。昙花一现 781，新兴型 465，衰退型 331，爆发后衰退 177，复活型 37。M5 完成时 26 个测试、demo 六页；M6 加了替代复核页，现在是七页、27 个测试。

## M6 替代复核页（扩展）

目标：在 demo 里逐对标注候选替代，保存到 CSV，并计算 precision@10 和 precision@20。

验收：

- 页面显示旧概念和新概念的两条时间线，以及 Jaccard、相关系数、峰值年。
- 可以选“是 / 否 / 不确定”并写备注。
- 保存后 CSV 更新，指标刷新。
- 单独的评估脚本能从 CSV 算 precision@k。

任务：

- [x] 页面和保存
- [x] `load_review` 和 `review_precision`
- [x] `scripts/evaluate_replacements.py`
- [x] 测试

M6 结果：demo 七页 0 异常，27 个测试通过。20 对全部标完，采用“焦点转移”标准，9 对有效：Cryptocurrency→Blockchain、Machine translation→Language model、Machine translation→Transformer、Cryptocurrency→Smart contract、Distributed learning→Federated learning、Query language→SQL、Utility computing→Edge computing、Residual neural network→Pruning、Static analysis→Malware。precision@10 = 0.600，precision@20 = 0.450。11 对由人初判，9 对由 AI 补判，5 对在讨论后改判，最终人工确认全部 20 对，见 `D-022`。
