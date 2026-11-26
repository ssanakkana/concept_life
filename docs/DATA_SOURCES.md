# 添加 Acemap 以外的数据源

这份文档回答一个问题：以后想接 OpenAlex、Semantic Scholar、DBLP、arXiv 或别的数据源，应该怎么接，才不用改下游的分析和 demo。

## 核心原则

下游只认 `Paper` 和 `Concept` 两个数据契约，不认任何 API 的原始字段。所有数据源都在 `src/concept_life/sources/` 里做适配，输出同样的 `Paper` 列表。`series.py`、`rising.py`、`mine.py`、`predict.py`、`app.py` 一行都不用改。

现在已经有的字段：

```python
Paper(id, title, year, doi, cited_by_count, concepts, fields, source)
Concept(id, name, level, score, wikidata)
```

`source` 记录这篇论文来自哪个数据源。`wikidata` 是跨源对齐概念的最佳键。`doi` 是跨源对齐论文的最佳键。

## 接一个新源的五个步骤

### 第一步：抓取，只落原始响应

在 `scripts/` 下写一个 `crawl_<source>.py`，把原始响应写到 `data/raw/<source>/`，同时写一个 JSONL manifest。抓取器不做解析、不做过滤、不做去重。这样原始数据可以只增不改，解析逻辑改了可以重跑，不用重新抓。

每个源的分页方式不同：

- Acemap：`page` 加 `size`，`meta.total_pages`，`size=100` 上限，`meta.count` 在 10000 处截断。
- OpenAlex：`per-page` 最大 200，`cursor=*` 加 `meta.next_cursor`，支持 `filter=publication_year:1990-2023`。
- Semantic Scholar：`/graph/v1/paper/search` 或 `/paper/search/bulk`，有速率限制，建议带 API key。
- DBLP：XML/JSON 分页，只有元数据，没有摘要。
- arXiv：`export.arxiv.org/api/query`，Atom XML，有全文。

### 第二步：解析成 Paper

在 `src/concept_life/sources/<source>.py` 写一个 `parse_<source>(record) -> Paper | None`。解析器只做字段映射和基本清洗，返回 `None` 表示这条记录不能用。

以 OpenAlex 为例，字段映射是：

| Paper 字段 | OpenAlex 字段 | 注意 |
| --- | --- | --- |
| `id` | `id` | 去掉 `https://openalex.org/` 前缀 |
| `title` | `title` 或 `display_name` | 可能为空 |
| `year` | `publication_year` | 必须是 int |
| `doi` | `doi` | 去掉 `https://doi.org/` 前缀 |
| `cited_by_count` | `cited_by_count` | 当前累计值，不是历史值 |
| `concepts` | `topics` 或 `concepts` | OpenAlex 2024 年把 concepts 换成 topics，先用一条记录确认 |
| `fields` | `topics[].domain/field/subfield` | 用于领域过滤 |
| `source` | 固定写 `"openalex"` | |
| `wikidata` | `concepts[].wikidata` | topics 可能没有，需要检查 |

OpenAlex 的摘要不是纯文本，而是 `abstract_inverted_index`，需要按位置重建。生命周期分析不需要摘要，但做语义相似度时需要。

### 第三步：写一个 load 函数

```python
def load_openalex(cache_dir: Path) -> list[Paper]:
    papers = []
    for path in sorted(cache_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for work in data.get("results") or []:
            paper = parse_openalex_work(work)
            if paper is not None:
                papers.append(paper)
    return papers
```

`load` 函数只负责读缓存、解析、返回 `Paper` 列表。去重、领域过滤、停用词这些通用步骤放在 `ingest.py`，所有源共用。

### 第四步：跨源合并

先把每个源单独跑一遍，看各自的年份分布、概念分布、覆盖率。确认单源没问题，再合并。合并规则按优先级来：

1. 论文去重：先按 DOI，再按规范化标题加年份，最后按 `(source, id)`。
2. 概念合并：先按 Wikidata，再按规范化名称加别名表，最后按源内 concept id。
3. 字段合并：取并集。
4. 引用数：取最大值，并记录来源。
5. 保留 `source`，不要合并后丢失来源。评估时要能按来源切片。

不要一上来就把 Acemap 和 OpenAlex 混在一起跑生命周期。两个源的概念体系和年份语义不同，混在一起会把“数据源差异”误判成“概念演化”。

### 第五步：加测试和决策记录

每个新源加一个 fixture 测试：一条真实记录，断言 `Paper` 的字段、概念、年份、DOI、Wikidata。跨源合并加一个测试：同一篇论文在两个源里应该合成一条，概念按 Wikidata 合并。

任何跨源合并规则的改动写进 `docs/DECISIONS.md`，包括为什么用 DOI 优先、为什么用 Wikidata 而不是名字。

## 三个源的具体建议

### OpenAlex

最适合作为第二源。免费、无需 key、支持年份过滤、支持 cursor 深翻页、有 `referenced_works`。缺点是概念体系在 2024 年从 concepts 换成了 topics，字段名和层级会变，接之前先用一条记录确认。

抓取示例：

```text
https://api.openalex.org/works?filter=publication_year:1995-2023,type:article&per-page=200&cursor=*&mailto=you@example.com
```

`mailto` 是礼貌池参数，不是认证。`select=id,title,publication_year,doi,cited_by_count,concepts,topics` 可以减小响应体积。

### Semantic Scholar

适合补引用和摘要。`/graph/v1/paper/search` 有速率限制，免费额度大约每秒一请求；有 API key 会快很多。`fields` 参数可以一次要回标题、年份、摘要、引用数、参考文献标题。适合做 citation 脉络，不适合做全量抓取。

### DBLP 和 arXiv

DBLP 适合补会议和期刊元数据，没有摘要和概念。arXiv 适合补全文和最新预印本，但需要自己做概念抽取。两者都不适合单独做生命周期分析，适合作为补充源。

## 常见坑

- 论文 ID 不同源不通用。Acemap 的 `id` 和 OpenAlex 的 `id` 是两套体系，必须用 DOI 或标题加年份做桥。
- 概念 ID 不同源不通用。Acemap 的 concept id 是它自己的编码，OpenAlex 是 `C...`，必须用 Wikidata 或名称做桥。
- 年份语义不同。有的是在线发表年，有的是期刊年，有的是会议年。混用前先看分布。
- 预印本和正式版是两条记录。合并时按标题加年份去重，保留引用数更高的那条，或者两条都留但标记版本。
- `cited_by_count` 是当前值，不是历史值。不能拿它做时间序列，见 `P-008`。
- 不同源的领域分类不同。Acemap 有 `topics.domain/field/subfield`，OpenAlex 有 `topics`，DBLP 没有。领域过滤要按源写适配，不能共用一个字符串。
- 跨源合并后，生命周期事件可能变化。先单源跑基线，再合并跑对比，不要只报合并后的结果。

## 代码骨架

以后新建 `src/concept_life/sources/` 时，可以按这个结构：

```text
src/concept_life/sources/
├── __init__.py
├── base.py          # DataSource 协议和通用 merge 工具
├── acemap.py        # 把现有 ingest.py 的 Acemap 逻辑挪进来
├── openalex.py      # parse_openalex_work + load_openalex
└── semantic.py      # 可选
```

```python
# base.py
from pathlib import Path
from typing import Protocol
from ..schema import Paper


class DataSource(Protocol):
    name: str

    def load(self, cache_dir: Path) -> list[Paper]:
        ...
```

`ingest.py` 以后可以变成一个调度器：

```python
def load_all(sources: list[DataSource], cache_root: Path) -> list[Paper]:
    papers = []
    for source in sources:
        papers.extend(source.load(cache_root / source.name))
    return papers
```

在真正重构之前，先把新源写成独立的 `load_<source>` 函数，和现有 `load_cache` 并列。等第二个源跑通，再抽 `sources/` 包。不要为了架构好看，先把能跑的代码拆散。

## 什么时候值得接新源

- 需要 2024 和 2025 的数据。Acemap 索引滞后，OpenAlex 能补近两年。
- 需要引用边。Acemap 只有 `referenced_works_count`，OpenAlex 和 Semantic Scholar 有 `referenced_works`。
- 需要摘要做语义相似度。Acemap 约 32% 缺摘要，OpenAlex 覆盖更好。
- 需要跨源验证一个概念的生命周期是不是数据源 artifact。

如果只是做 1995 到 2023 的概念生命周期，Acemap 的 42,460 篇已经够用，不必为了“多源”而多源。先把单源故事讲完整，再考虑第二源。
