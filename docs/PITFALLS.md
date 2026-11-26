# 坑列表

新坑先记录，再修。每条包含现象、原因、解决办法、相关文件。

| ID | 现象 | 原因 | 解决办法 | 相关文件 |
| --- | --- | --- | --- | --- |
| P-001 | 同一个概念在不同论文里名字不同，直接按名字聚合会碎成多个节点 | Acemap 的 `display_name` 会随时间、来源变化 | 用 concept `id` 做主键，`display_name` 只做展示；展示名取出现次数最多的那个 | `schema.py` |
| P-002 | 概念“死亡”判断不可靠，很多概念只是近几年没被缓存覆盖 | Acemap 索引有滞后，先导缓存 2024 年只有 16 篇，2023 年 59 篇 | “死亡”定义为语料中连续 N 年缺失，并在海报上写“在语料中消失”，不写“世界上消失” | `mine.py` |
| P-003 | 原始计数会把“语料变大”误判成“概念变热” | 每年论文总数在增长，2015 到 2020 增长了近一倍 | 所有频率用“占当年论文总数的比例”，上升分数用 share 差值和 share 增长率 | `series.py`、`rising.py` |
| P-004 | 泛概念淹没具体概念，top 榜全是“计算机科学”“人工智能” | Acemap 概念有 level 0 到 5，level 0 和 1 是极宽的上位概念 | 只用 level 2 以上，或者每篇取 score 最高的前 10 个 | `configs/default.json` |
| P-005 | 先导缓存的年份分布严重偏向 2019 到 2021 | 查询集是 58 个 CS 种子，且 Acemap 按相关性排序 | M1 重新抓取时加入近年热点词和经典概念，抓完先画年份直方图 | `scripts/crawl.py` |
| P-006 | 摘要缺失，向量检索或摘要级分析覆盖不全 | Acemap 缓存里约 32% 的记录没有 `abstract` | 生命周期分析只用标题、概念、年份；需要摘要时另找 OpenAlex | `ingest.py` |
| P-007 | citation 脉络做不了 | Acemap 只返回 `referenced_works_count`，没有 `referenced_works` 列表 | 需要引用边时用 OpenAlex 或 Semantic Scholar 按 DOI 补；不引入就不做 | `docs/DECISIONS.md` |
| P-008 | `cited_by_count` 被当成历史引用数 | 它是 API 返回的当前累计引用，不是当年的引用 | 不用它做时间序列；需要历史引用时用 OpenAlex 的 `cited_by_year` 或逐年快照 | `schema.py` |
| P-009 | Louvain 每次跑出来的社区不一样 | 算法有随机性 | 固定 `seed`，或者跑多次取模块度均值和方差；海报上写清楚 | `graph.py` |
| P-010 | 链路预测或趋势预测的指标虚高 | 随机切分把未来信息泄漏进训练集 | 严格按时间切分，训练只用 T 年以前，测试用 T 到 T+2 年；写测试防止回归 | `predict.py`、`tests/` |
| P-011 | 缓存文件名冲突，不同查询互相覆盖 | 先导项目用 slug 拼缓存文件名，空格和特殊字符可能撞车 | 缓存键用“查询原文哈希 + 页码 + size + order”，不要只用 slug | `scripts/crawl.py` |
| P-012 | 同一篇论文被多个查询返回，重复计数 | Acemap 不同关键词会返回同一篇论文 | 按 work `id` 去重；有 DOI 时再按 DOI 去重一次 | `ingest.py` |
| P-013 | 概念第一次出现被误判为“发明” | 语料只是抽样，概念可能更早存在但没被收录 | 措辞用“在语料中首次出现”，不写“首次提出” | `mine.py` |
| P-014 | 替代关系被写成因果关系 | 时间上的此消彼长不等于替代 | 输出叫“候选替代对”，附相关性、共现、社区相似度证据；海报写“candidate replacement” | `mine.py` |
| P-015 | 演示现场网络不稳定，实时调 API 失败 | 教室 Wi-Fi 不可控 | demo 只读预计算产物；所有数据本地化；准备录屏备份 | `app.py` |
| P-016 | `growth` 出现 3e10 这种数字 | 历史窗口计数为 0，分母用了 1e-12 | 历史为 0 时标记 `is_new`，`growth=None`，CSV 写 `new`；排序仍以 `delta_share` 为主 | `rising.py` |
| P-017 | 上升榜出现 `Health care`、`Key (lock)`、`Focus (optics)`、`Domain (mathematical analysis)` | Acemap 把跨领域同名词映射到同一概念；先导查询集带进医学、物理论文；小计数噪声 | M1 加领域过滤（按 `topics` 的 field/domain），加歧义概念停用词表，提高 `min_curr_count` | `ingest.py`、`configs/default.json` |
| P-018 | `[2015, 2017]` 只统计了 2015 和 2017 两年 | 配置是年份列表，不是区间 | 配置改成显式年份列表 `[2015, 2016, 2017]`；文档写清楚 | `configs/default.json` |
| P-019 | 1187 篇缓存过滤 level>=2 后只剩 1054 篇 | 部分论文只有 level 0/1 的泛概念 | 接受损失，但要在 worklog 记录；M1 扩大语料补回来 | `ingest.py` |
