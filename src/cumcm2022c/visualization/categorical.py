"""Reusable visualizations for categorical association analysis."""

from __future__ import annotations

import warnings
from collections.abc import Sequence

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib import font_manager
from matplotlib.ticker import PercentFormatter

FONT_CANDIDATES = [
    "Microsoft YaHei",
    "SimHei",
    "Noto Sans CJK SC",
    "Noto Sans CJK JP",
    "WenQuanYi Micro Hei",
    "Arial Unicode MS",
]
WEATHERING_ORDER = ["无风化", "风化"]
WEATHERING_COLORS = ["#4C78A8", "#E45756"]


def configure_chinese_fonts() -> str | None:
    """Configure the first available Chinese-capable Matplotlib font."""

    available = {font.name for font in font_manager.fontManager.ttflist}
    for candidate in FONT_CANDIDATES:
        if candidate in available:
            plt.rcParams["font.sans-serif"] = [candidate, "DejaVu Sans"]
            plt.rcParams["axes.unicode_minus"] = False
            return candidate
    warnings.warn(
        "No supported Chinese font was found; plot labels may show missing glyphs.",
        RuntimeWarning,
        stacklevel=2,
    )
    return None


def plot_category_counts(frame: pd.DataFrame, columns: Sequence[str]):
    """Plot category frequencies in a compact two-by-two layout."""

    configure_chinese_fonts()
    if len(columns) != 4:
        raise ValueError("Category count layout requires exactly four columns")
    figure, axes = plt.subplots(2, 2, figsize=(13, 8), constrained_layout=True)
    for axis, column in zip(axes.flat, columns, strict=True):
        counts = frame[column].value_counts(dropna=False)
        labels = counts.index.astype(str)
        bars = axis.bar(labels, counts.to_numpy(), color="#4C78A8")
        axis.bar_label(bars, padding=2, fontsize=9)
        axis.set_title(f"{column}类别频数")
        axis.set_xlabel(column)
        axis.set_ylabel("样本数")
        axis.tick_params(axis="x", rotation=35)
    return figure, axes


def plot_association_heatmaps(
    cramers_v_matrix: pd.DataFrame,
    p_value_matrix: pd.DataFrame,
    reliability_matrix: pd.DataFrame,
):
    """Plot association-strength and significance matrices side by side."""

    configure_chinese_fonts()
    if not cramers_v_matrix.index.equals(p_value_matrix.index):
        raise ValueError("Association matrices must use identical indexes")
    if not cramers_v_matrix.index.equals(reliability_matrix.index):
        raise ValueError("Reliability matrix must use the same index")

    figure, axes = plt.subplots(1, 2, figsize=(13, 5.5), constrained_layout=True)
    sns.heatmap(
        cramers_v_matrix.astype(float),
        annot=True,
        fmt=".3f",
        vmin=0,
        vmax=1,
        cmap="YlGnBu",
        square=True,
        ax=axes[0],
        cbar_kws={"label": "Cramér's V"},
    )
    axes[0].set_title("偏差校正 Cramér's V")

    annotations = p_value_matrix.astype(float).copy().astype(object)
    for row in p_value_matrix.index:
        for column in p_value_matrix.columns:
            value = float(p_value_matrix.loc[row, column])
            suffix = "†" if row != column and not reliability_matrix.loc[row, column] else ""
            annotations.loc[row, column] = f"{value:.3g}{suffix}"
    sns.heatmap(
        p_value_matrix.astype(float),
        annot=annotations,
        fmt="",
        vmin=0,
        vmax=1,
        cmap="mako_r",
        square=True,
        ax=axes[1],
        cbar_kws={"label": "p 值"},
    )
    axes[1].set_title("Pearson 卡方检验 p 值（†：近似条件不足）")
    return figure, axes


def plot_weathering_proportions(
    frame: pd.DataFrame,
    predictors: Sequence[str],
    target: str = "表面风化",
):
    """Plot within-category weathering proportions for three predictors."""

    configure_chinese_fonts()
    if len(predictors) != 3:
        raise ValueError("Weathering layout requires exactly three predictors")
    figure, axes = plt.subplots(1, 3, figsize=(17, 5.5), constrained_layout=True)
    for axis, predictor in zip(axes.flat, predictors, strict=True):
        counts = pd.crosstab(frame[predictor], frame[target], dropna=False).reindex(
            columns=WEATHERING_ORDER, fill_value=0
        )
        proportions = counts.div(counts.sum(axis=1), axis=0)
        proportions.plot(
            kind="bar",
            stacked=True,
            color=WEATHERING_COLORS,
            width=0.8,
            ax=axis,
        )
        sample_sizes = counts.sum(axis=1).astype(int)
        axis.set_xticklabels(
            [f"{category}\n(n={sample_sizes.loc[category]})" for category in counts.index],
            rotation=35,
            ha="right",
        )
        axis.set_ylim(0, 1)
        axis.yaxis.set_major_formatter(PercentFormatter(1.0))
        axis.set_title(f"{predictor}与表面风化")
        axis.set_xlabel(predictor)
        axis.set_ylabel("类别内部比例")
        axis.legend(title=target, loc="upper right")
    return figure, axes
