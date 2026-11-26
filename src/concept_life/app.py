"""Concept Life Streamlit demo.

Run:
    uv run streamlit run src/concept_life/app.py

The demo is read-only. It loads the standard artifacts from M0-M3 and never
calls an API, so it works offline during the poster session.
"""
from __future__ import annotations

import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from concept_life.dashboard import (  # noqa: E402
    RUNS_DIR,
    check_artifacts,
    concept_events,
    concept_options,
    event_counts,
    load_clusters,
    load_events,
    load_predictions,
    load_replacements,
    load_review,
    load_rising,
    load_series,
    load_summaries,
    review_precision,
    timeline,
)

st.set_page_config(page_title="Concept Life", page_icon="🌱", layout="wide")


@st.cache_data(show_spinner=False)
def cached_series() -> pd.DataFrame:
    return load_series()


@st.cache_data(show_spinner=False)
def cached_events() -> pd.DataFrame:
    return load_events()


def require_artifacts() -> None:
    missing = check_artifacts()
    if not missing:
        return
    st.error("缺少数据文件，先按顺序跑一遍下面的命令：")
    st.code(
        "\n".join(
            [
                "uv run python scripts/crawl.py --pages 4 --size 100",
                "uv run python scripts/m0_from_cache.py --config configs/m1.json --runs runs/m1",
                "uv run python scripts/data_report.py --papers data/processed/papers.jsonl --config configs/m1.json",
                "uv run python scripts/m2_events.py --config configs/m2.json",
                "uv run python scripts/m3_replacements.py",
                "uv run python scripts/m3_trend.py",
                "uv run python scripts/m5_clusters.py",
            ]
        ),
        language="bash",
    )
    st.caption("缺失文件：" + "，".join(str(path) for path in missing))
    st.stop()


def page_overview(summaries: dict, events: pd.DataFrame) -> None:
    m1 = summaries["m1"]
    m2 = summaries["m2"]
    replacement = summaries["replacement"]

    st.title("Concept Life")
    st.caption("学术概念的生命周期：从兴起到替代，再到下一个焦点。")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("论文", f"{m1['papers']:,}")
    col2.metric("概念", f"{m1['concepts_unique']:,}")
    col3.metric("生命周期事件", f"{m2['events']:,}")
    col4.metric("替代候选", f"{replacement['pairs']}")

    st.divider()
    left, right = st.columns([2, 1])
    with left:
        st.subheader("逐年论文数")
        histogram = pd.read_csv(
            RUNS_DIR / "m1" / "report" / "year_histogram.csv",
            encoding="utf-8-sig",
        )
        st.bar_chart(histogram.set_index("year"), height=300)
        st.caption("2024 和 2025 索引不完整，分析区间只用到 2023。")
    with right:
        st.subheader("事件分布")
        counts = event_counts(events)
        st.bar_chart(counts.set_index("type"), height=300)

    st.subheader("数据质量")
    coverage = (m1["papers"] - m1["missing_fields"]) / max(1, m1["papers"])
    st.write(f"CS 覆盖率：{coverage:.1%}，{m1['missing_fields']} 篇没有 topics。")
    st.write(f"缺失 DOI：{m1['missing_doi']:,} 篇。")
    st.write(
        f"前窗口 2015-2017：{sum(m1['papers_by_window']['prev'].values()):,} 篇；"
        f"后窗口 2018-2020：{sum(m1['papers_by_window']['curr'].values()):,} 篇。"
    )


def page_timeline(series: pd.DataFrame, events: pd.DataFrame) -> None:
    st.title("概念时间线")
    st.caption("折线是概念在当年论文中的占比，虚线是生命周期事件。")

    options = concept_options(series, limit=300)
    if not options:
        st.warning("没有概念数据。")
        return
    names = [name for _, name in options]
    default_index = names.index("Transformer") if "Transformer" in names else 0
    selected = st.selectbox(
        "选择一个概念",
        options,
        index=default_index,
        format_func=lambda item: item[1],
    )
    concept_id, _name = selected
    frame = timeline(series, concept_id)
    concept_event_rows = concept_events(events, concept_id)

    total = int(frame["count"].sum())
    if total == 0:
        st.info("这个概念在 1995-2023 没有论文。")
        return
    peak = frame.loc[frame["share"].idxmax()]
    col1, col2, col3 = st.columns(3)
    col1.metric("累计论文", f"{total:,}")
    col2.metric("峰值年份", int(peak["year"]))
    col3.metric("峰值占比", f"{peak['share']:.2%}")

    base = alt.Chart(frame).encode(x=alt.X("year:Q", title="年份"))
    line = base.mark_line(point=True, color="#2c5a86").encode(
        y=alt.Y("share:Q", title="占当年论文比例", axis=alt.Axis(format="%")),
        tooltip=[
            alt.Tooltip("year:Q", title="年份"),
            alt.Tooltip("share:Q", title="占比", format=".4%"),
            alt.Tooltip("count:Q", title="论文数"),
        ],
    )
    chart = line
    if not concept_event_rows.empty:
        rules = alt.Chart(concept_event_rows).mark_rule(
            strokeDash=[4, 4], color="#b58a45", opacity=0.65
        ).encode(
            x=alt.X("year:Q"),
            tooltip=[
                alt.Tooltip("type:N", title="事件"),
                alt.Tooltip("year:Q", title="年份"),
                alt.Tooltip("score:Q", title="分数"),
            ],
        )
        chart = line + rules
    st.altair_chart(chart, width="stretch")

    if concept_event_rows.empty:
        st.info("没有生命周期事件。可能总论文数少于 20，或峰值论文数少于 5。")
        return
    st.subheader("事件表")
    st.dataframe(
        concept_event_rows[["type", "year", "score"]],
        hide_index=True,
        width="stretch",
    )
    with st.expander("事件证据"):
        st.json(concept_event_rows.to_dict(orient="records"))


def page_lifecycle() -> None:
    st.title("生命周期类型")
    st.caption(
        "按曲线形状聚类，不是按论文数或年份。K-means + silhouette，k=5。"
    )
    clusters = load_clusters()

    counts = (
        clusters["label"]
        .value_counts()
        .rename_axis("label")
        .reset_index(name="concepts")
    )
    left, right = st.columns([1, 2])
    with left:
        st.subheader("五类概念")
        st.bar_chart(counts.set_index("label"), height=280)
    with right:
        st.subheader("形状分布")
        scatter = alt.Chart(clusters).mark_circle(opacity=0.55).encode(
            x=alt.X(
                "peak_position:Q",
                title="峰值位置（0=早期，1=晚期）",
                scale=alt.Scale(domain=[0, 1]),
            ),
            y=alt.Y(
                "decline_speed:Q",
                title="峰值到末期的下降幅度",
                scale=alt.Scale(domain=[0, 1]),
            ),
            color=alt.Color("label:N", title="类型"),
            size=alt.Size(
                "total_count:Q",
                title="累计论文",
                scale=alt.Scale(type="sqrt", range=[10, 350]),
            ),
            tooltip=[
                "name",
                "label",
                "total_count",
                "peak_year",
                "span",
                "decline_speed",
            ],
        )
        st.altair_chart(scatter, width="stretch")

    st.divider()
    labels = sorted(clusters["label"].unique())
    selected = st.selectbox("看一个类型", labels)
    subset = clusters[clusters["label"] == selected].sort_values(
        "total_count", ascending=False
    )
    st.write(f"{selected}：{len(subset)} 个概念")
    st.dataframe(
        subset[
            [
                "name",
                "total_count",
                "first_year",
                "peak_year",
                "span",
                "decline_speed",
                "recent_to_peak",
            ]
        ].head(30),
        hide_index=True,
        width="stretch",
    )
    st.caption(
        "类型名是描述性的，不是金标。复活型样本只有 37 个，且复活事件本身有噪声。"
    )


def page_review(series: pd.DataFrame) -> None:
    st.title("替代复核")
    st.caption(
        "算法只生成候选，是否真的替代由人判断。标注结果写回 "
        "runs/m3/replacement_review.csv。"
    )
    review = load_review()
    if review.empty:
        st.info("没有候选。先跑 scripts/m3_replacements.py。")
        return

    ranks = [int(value) for value in review["rank"]]
    if "review_rank" not in st.session_state or st.session_state.review_rank not in ranks:
        st.session_state.review_rank = ranks[0]

    def previous_pair() -> None:
        index = ranks.index(int(st.session_state.review_rank))
        st.session_state.review_rank = ranks[max(0, index - 1)]

    def next_pair() -> None:
        index = ranks.index(int(st.session_state.review_rank))
        st.session_state.review_rank = ranks[min(len(ranks) - 1, index + 1)]

    col1, col2, _ = st.columns([1, 1, 4])
    col1.button("上一对", on_click=previous_pair)
    col2.button("下一对", on_click=next_pair)

    rank = st.selectbox("选择候选", ranks, key="review_rank")
    row = review[review["rank"] == rank].iloc[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("旧概念峰值", int(row["old_peak_year"]))
    col2.metric("新概念上升年", int(row["new_year"]))
    col3.metric("Jaccard", f"{row['jaccard']:.3f}")
    col4.metric("相关系数", f"{row['correlation']:.3f}")
    st.markdown(f"**{row['old_name']} → {row['new_name']}**")

    old = timeline(series, row["old_id"])
    old["concept"] = row["old_name"]
    new = timeline(series, row["new_id"])
    new["concept"] = row["new_name"]
    combined = pd.concat(
        [old[["year", "share", "concept"]], new[["year", "share", "concept"]]]
    )
    chart = alt.Chart(combined).mark_line(point=True).encode(
        x=alt.X("year:Q", title="年份"),
        y=alt.Y("share:Q", title="占当年论文比例", axis=alt.Axis(format="%")),
        color=alt.Color("concept:N", title="概念"),
        tooltip=[
            alt.Tooltip("concept:N", title="概念"),
            alt.Tooltip("year:Q", title="年份"),
            alt.Tooltip("share:Q", title="占比", format=".4%"),
        ],
    )
    st.altair_chart(chart, width="stretch")

    label_key = f"review_label_{rank}"
    notes_key = f"review_notes_{rank}"
    if label_key not in st.session_state:
        current = row["valid_1_0"]
        st.session_state[label_key] = (
            -1 if current is None or pd.isna(current) else int(current)
        )
    if notes_key not in st.session_state:
        st.session_state[notes_key] = str(row["notes"])

    choice = st.radio(
        "这是替代吗？",
        options=[1, 0, -1],
        format_func=lambda value: {1: "是", 0: "否", -1: "不确定"}[value],
        key=label_key,
        horizontal=True,
    )
    st.text_area("备注", key=notes_key)

    if st.button("保存这一对", type="primary"):
        value = st.session_state[label_key]
        review.loc[review["rank"] == rank, "valid_1_0"] = (
            "" if value == -1 else value
        )
        review.loc[review["rank"] == rank, "notes"] = st.session_state[notes_key]
        review.to_csv(
            RUNS_DIR / "m3" / "replacement_review.csv",
            index=False,
            encoding="utf-8-sig",
        )
        st.success("已保存")
        st.rerun()

    st.divider()
    labeled = int(review["valid_1_0"].notna().sum())
    st.subheader("标注进度与指标")
    st.write(f"已标注 {labeled}/{len(review)}")
    for k in (10, 20):
        metrics = review_precision(review, k)
        if metrics["precision"] is None:
            st.write(f"precision@{k}：还没有标注")
        else:
            st.write(
                f"precision@{k}：{metrics['precision']:.2f}，"
                f"已标注 {metrics['labeled']}/{metrics['total']}"
            )
    st.caption("未标注或“不确定”不计入 precision 分母。建议把 top-10 全部标完再看指标。")

    st.subheader("全部候选")
    st.dataframe(
        review[
            [
                "rank",
                "old_name",
                "new_name",
                "jaccard",
                "correlation",
                "valid_1_0",
                "notes",
            ]
        ],
        hide_index=True,
        width="stretch",
    )


def page_rising() -> None:
    st.title("上升与替代")
    st.subheader("上升概念")
    st.caption("按前后窗口的 share 差值排序，见 configs/m1.json 的窗口。")
    rising = load_rising().head(30)
    st.dataframe(
        rising[["rank", "name", "delta_share", "growth", "curr_count"]],
        hide_index=True,
        width="stretch",
        column_config={
            "delta_share": st.column_config.NumberColumn(format="%.4f"),
            "growth": st.column_config.NumberColumn(format="%.2f"),
        },
    )

    st.divider()
    st.subheader("候选替代")
    st.warning(
        "这些是候选对，不是自动替代结论。共现相似度偏向互补概念，"
        "RNN→Transformer 这种真替代会被漏掉，需要人工复核。"
    )
    replacements = load_replacements().head(20)
    st.dataframe(
        replacements[
            [
                "rank",
                "old_name",
                "new_name",
                "old_peak_year",
                "new_year",
                "jaccard",
                "correlation",
                "score",
            ]
        ],
        hide_index=True,
        width="stretch",
    )
    review_path = RUNS_DIR / "m3" / "replacement_review.csv"
    if review_path.exists():
        st.subheader("人工复核表")
        st.dataframe(
            pd.read_csv(review_path, encoding="utf-8-sig"),
            hide_index=True,
            width="stretch",
        )


def page_trend(summaries: dict) -> None:
    st.title("趋势回测")
    st.caption(
        "给定 T 年特征，预测 T+1 到 T+2 的相对份额增长 top-k。"
        "每个窗口只用 T 年以前的共现图，避免未来泄漏。"
    )
    metrics = summaries["m3"]
    rows = []
    for method in ["model", "frequency", "growth", "random"]:
        row = {"method": method}
        row.update(metrics["mean"][method])
        rows.append(row)
    st.subheader("三窗口平均指标")
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.caption("窗口 2016、2018、2020；leave-one-window-out；标签是相对增长，未来份额至少 0.5%。")

    st.divider()
    st.subheader("2020 窗口的预测")
    predictions = load_predictions()
    st.dataframe(
        predictions,
        hide_index=True,
        width="stretch",
        column_config={
            "score": st.column_config.NumberColumn(format="%.3f"),
            "actual_future_growth": st.column_config.NumberColumn(format="%.3f"),
        },
    )
    st.caption("actual_future_growth 为 -1 表示未来份额低于 0.5%，不在标签里。")


def page_data() -> None:
    st.title("数据与方法")
    st.markdown(
        """
### 数据

- 来源：Acemap work search API，170 个查询，每个查询 4 页，每页 100 条。
- 规模：67,896 条原始记录，去重和 CS 过滤后 42,460 篇论文、10,957 个概念。
- 年份：1990 到 2025。2024 和 2025 索引不完整，生命周期分析只用 1995 到 2023。
- 概念：Acemap concept id 为主键，display name 只做展示。

### 方法

1. 逐年统计每个概念的论文数和占当年论文总数的比例。
2. 用 share 的 z-score、峰值、衰退和 gap 规则检测生命周期事件。
3. 用共现 Jaccard、负相关和末期反超生成候选替代对。
4. 用相对增长标签、时间感知共现图和逻辑回归做趋势回测。

### 已知限制

- 概念标签有噪声，`Pattern recognition (psychology)`、`Image (mathematics)` 这类标签会进入结果。
- 死亡只表示在语料中连续两年没有活跃论文，本次只有 3 个死亡事件。
- 替代检测是候选生成，不是自动替代，需要 citation 或文本信号。
- 趋势预测的 precision@10 是 0.200，高于基线但远不到可靠预测。
- 2024 和 2025 不能用来判断死亡或趋势。
        """
    )
    st.caption("详细文档见 README.md、docs/PLAN.md、docs/PITFALLS.md 和 docs/DECISIONS.md。")


def main() -> None:
    require_artifacts()
    summaries = load_summaries()
    series = cached_series()
    events = cached_events()

    page = st.sidebar.radio(
        "页面",
        [
            "总览",
            "概念时间线",
            "生命周期类型",
            "上升与替代",
            "替代复核",
            "趋势回测",
            "数据与方法",
        ],
    )
    st.sidebar.divider()
    st.sidebar.caption(f"论文 {summaries['m1']['papers']:,} 篇")
    st.sidebar.caption(f"概念 {summaries['m1']['concepts_unique']:,} 个")
    st.sidebar.caption("分析区间 1995-2023")
    st.sidebar.caption("数据只读，不调用 API")

    if page == "总览":
        page_overview(summaries, events)
    elif page == "概念时间线":
        page_timeline(series, events)
    elif page == "生命周期类型":
        page_lifecycle()
    elif page == "上升与替代":
        page_rising()
    elif page == "替代复核":
        page_review(series)
    elif page == "趋势回测":
        page_trend(summaries)
    else:
        page_data()


if __name__ == "__main__":
    main()
