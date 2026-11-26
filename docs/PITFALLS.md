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
| P-020 | 把 Acemap 的 `meta.count` 当成语料真实总量 | 接口把 `count` 截断在 10000 | 不拿 `count` 当总量；按 `total_pages` 和每页 `results` 长度决定何时停 | `crawl.py` |
| P-021 | 领域过滤后仍有 `Field (mathematics)` 这种跨领域概念 | 过滤是论文级的，一篇 CS 论文可以带数学概念 | 用概念停用词做 band-aid；真正的解法是概念级领域分类或别名合并，见 `I-010`、`I-014` | `ingest.py`、`configs/m1.json` |
| P-022 | 部分论文没有 `topics`，不知道属于哪个领域 | Acemap 的元数据不完整 | 默认保留，记录 `missing_fields` 数量；如果噪声太大再改成丢弃 | `ingest.py`、`data_report.py` |
| P-023 | 停用词可能把一篇论文的所有概念都过滤掉 | 有些论文只带一个歧义概念 | 概念全被过滤时丢弃该论文，并在报告里记录；不要留下空概念论文 | `ingest.py` |
| P-024 | 2024 和 2025 论文数断崖式下降，2024 只有 1,481 篇，2025 只有 265 篇 | Acemap 索引滞后，近两年不完整 | 生命周期分析主区间设为 1995-2023，近两年不参与死亡和趋势判断，见 `D-010` | `configs/m1.json`、`mine.py` |
| P-025 | top rising 里仍有 `Pattern recognition (psychology)`、`Image (mathematics)`、`Feature (linguistics)`、`Voltage`、`Benchmark (surveying)` | Acemap/OpenAlex 的概念标签有歧义，论文级领域过滤管不到概念级标签 | 停用词只能清掉最明显的几个；真正的解法是别名合并或概念级领域分类，见 `I-010`、`I-014` | `configs/m1.json`、`ingest.py` |
| P-026 | 42k 语料里只有 3 个死亡事件，和“概念会死”的直觉不符 | 语料足够大，泛概念标签每年都能找到几篇论文；完全连续两年零出现很难 | 不要把 death 当成主结论；海报用“在语料中消失”，并同时展示 decline 和 dormancy。见 `D-012` | `mine.py`、`configs/m2.json` |
| P-027 | 早期年份的小概念出现假峰值，比如 `Implementation` 在 1995 年 share 7.6% | 1990 到 1999 每年只有 37 到 79 篇论文，5 篇就能撑起高占比 | 峰值和爆发只在当年语料至少 `min_year_total=100` 篇时计算 | `mine.py`、`configs/m2.json` |
| P-028 | 平缓序列上的 z-score 把微小变化判成爆发 | z-score 只看相对波动，不看绝对增幅；小方差序列容易虚高 | 加 `burst_min_delta=0.002` 和 `burst_min_rel=0.2`，要求绝对占比和相对增幅都够大 | `mine.py`、`configs/m2.json` |
| P-029 | 泛概念仍然产生事件，比如 `Implementation`、`Citation`、`Path (computing)` | 概念级标签噪声，停用词只能清掉最明显的几个 | 事件表保留，但案例和海报只用黄金案例和人工挑过的概念；长期解法是别名合并和概念级领域分类 | `mine.py`、`I-010` |
| P-030 | 趋势预测精度虚高到 precision@10 0.467 | degree 和邻居特征用了全语料共现图，未来的边泄漏进特征 | 每个窗口只用 T 年以前的论文建共现图，修后 precision@10 降到 0.200 | `scripts/m3_trend.py`、`D-016` |
| P-031 | 替代检测的 top 对很多是互补概念，不是替代概念，RNN→Transformer 反而被漏掉 | 共现相似度衡量“经常一起出现”，替代关系往往是“同一生态位、互斥出现” | 把输出叫候选对，加人工复核表；真正的替代需要 citation 或文本信号，见 `I-005` | `replace.py`、`D-015` |
| P-032 | 绝对增长标签下 frequency 基线很强，模型没有增量 | 绝对份额增长偏向已经很大的概念 | 改成相对增长标签，并加最小未来份额和 T 年份额门槛；同时报告绝对模式作为对比，见 `D-014` | `predict.py`、`configs/m3.json` |
| P-033 | random 和 frequency 基线在某些窗口是 0.000，看起来像 bug | 每窗只有 20 个正例，候选有几百个，随机 top-10 命中 0 个是正常的 | 报告每窗候选数、正例数和均值，不要只看单窗 0.000 就下结论 | `predict.py`、`runs/m3/trend_metrics.json` |
| P-034 | Streamlit 1.67 警告 `use_container_width` 将在 2025-12-31 后移除 | 新版 API 改成 `width="stretch"` 或 `width="content"` | 全部换成 `width="stretch"`，不再用 `use_container_width` | `app.py` |
| P-035 | 只检查 `_stcore/health` 返回 ok，页面仍可能有异常 | health 只说明服务器起来了，不执行页面代码 | 用 `streamlit.testing.v1.AppTest` 真正跑五个页面，断言 exception 为空 | `scripts/smoke_demo.py` |
| P-036 | pandas 读带 BOM 的 CSV，第一列变成 `﻿concept_id` | CSV 用了 `utf-8-sig` 写入 | 读的时候也写 `encoding="utf-8-sig"` | `dashboard.py` |
| P-037 | 生命周期聚类按年代或论文数分簇，不像形状 | 把绝对年份、total_count 放进特征，K-means 会按大小和时代切 | 聚类只用形状特征；total_count 只用于展示和排序 | `cluster.py`、`configs/m5.json` |
| P-038 | “衰退型”里有很多成熟概念，看起来像领域死了 | 语料在增长，成熟概念的 share 也会自然下降 | 类型名是语料内份额形状，不是领域健康度；海报要写清楚 | `scripts/m5_clusters.py`、`D-020` |
| P-039 | 直接按 cluster index 叫“类型 0”“类型 1” | K-means 的编号是随机的，换 seed 就变 | 用 centroid 规则命名，并保证名字唯一 | `cluster.py` |
| P-040 | 聚类集合 1,837 个概念，事件集合 1,793 个 | total 把 1995 年以前的论文也算进去了 | total 只在分析区间内计数，和 M2 对齐 | `cluster.py` |
| P-041 | 替代复核页的 precision 只在已标注行上算，top-10 没标完时会偏高或偏低 | 未标注和“不确定”不计入分母 | 页面显示“已标注 X/10”；海报上写清楚分母，不要把它当成完整 top-10 精确率 | `dashboard.py`、`app.py` |
| P-042 | 保存复核后 `replacement_review.csv` 的列变多 | 页面把完整候选字段写回 CSV | `load_review` 只按 rank 取 valid 和 notes；不要改 rank 或重排文件 | `dashboard.py`、`scripts/evaluate_replacements.py` |
| P-043 | 人工标签被当成客观金标 | 替代关系本身有歧义，不同人判断会不同 | 海报写标注人数和口径；有条件让两个人独立标，算一致率 | `replacement_review.csv`、`D-021` |
| P-044 | 9 对最初由 AI 补判，5 对在讨论后改判为 1，却被写成“两个人独立标注” | 用户只能判断 11 对，剩下 9 对由 AI 看曲线和备注判断，讨论后人工确认 | 报告写“1 人 + AI 辅助复核，20 对全部人工确认”，不要包装成双人独立金标 | `data/labels/replacement_review.csv`、`D-022` |
| P-045 | precision 在不同替代标准下差很多 | 焦点转移标准把 Machine translation→Language model、Residual neural network→Pruning 算 1；严格同功能标准会算 0 | 海报写清楚“焦点转移”标准和标注人；要和别的系统比，先用同一标准重标 | `D-022`、`data/labels/replacement_metrics.json` |
| P-046 | 早期预测用了未来年份，指标虚高 | 特征窗口如果写成从 birth 到 2023，就把未来泄漏了 | 特征只取 birth 到 birth+2；`tests/test_early.py` 验证未来数据不改变特征 | `early.py`、`tests/test_early.py` |
| P-047 | 按出生年份切分时，训练集和测试集类别分布差异很大 | M5 标签在晚出生概念上偏向新兴型/昙花一现，观察窗口短 | 同时报告同分布 5 折和时间切分；时间切分写清多数类基线和按类指标 | `D-023`、`runs/m7/early_metrics.json` |
| P-048 | 复活型按类 F1 很低，看起来像模型坏了 | 时间切分里复活型测试只有 4 个 | 按类指标要写 support；复活型不要单独下结论 | `runs/m7/early_metrics.json` |
| P-049 | 只报同分布 5 折，不报时间切分 | 同分布 5 折 accuracy 0.656，时间切分 0.666，但两者含义不同 | 两种都报；时间切分是压力测试，不是普通泛化 | `D-023`、`scripts/m7_early.py` |
