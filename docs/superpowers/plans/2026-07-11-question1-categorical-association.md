# 问题一分类变量关联分析 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 `纹饰`、`类型`、`颜色`、`表面风化` 建立可复用、可测试的两两分类关联统计与可视化，并通过简洁专用 Notebook 展示结果。

**Architecture:** `analysis/categorical.py` 只负责数据准备、卡方检验、偏差校正 Cramér’s V 和矩阵整理；`visualization/categorical.py` 只负责从结构化结果生成 Matplotlib 图形。Notebook 不定义函数，仅加载数据、调用模块并展示统计表与图形。

**Tech Stack:** Python 3.11, uv, pandas, SciPy, Matplotlib, Seaborn, pytest, Jupyter

---

### Task 1: 添加统计与绘图依赖

**Files:**
- Modify: `pyproject.toml`
- Modify: `uv.lock`

- [ ] **Step 1: 使用 uv 添加依赖**

Run: `uv add scipy matplotlib seaborn`

Expected: `pyproject.toml` 包含三个依赖，`uv.lock` 更新且环境同步成功。

- [ ] **Step 2: 验证导入**

Run: `uv run python -c "import matplotlib, scipy, seaborn; print(matplotlib.__version__, scipy.__version__, seaborn.__version__)"`

Expected: exit 0 并输出三个版本号。

- [ ] **Step 3: 提交依赖**

```bash
git add pyproject.toml uv.lock
git commit -m "build(analysis): add statistical plotting dependencies"
```

### Task 2: 以 TDD 实现分类关联统计

**Files:**
- Create: `src/cumcm2022c/analysis/__init__.py`
- Create: `src/cumcm2022c/analysis/categorical.py`
- Create: `tests/analysis/test_categorical.py`

- [ ] **Step 1: 写数据准备与 Cramér’s V 失败测试**

```python
import pandas as pd
import pytest

from cumcm2022c.analysis.categorical import (
    cramers_v_bias_corrected,
    prepare_categorical_data,
)


def test_prepare_categorical_data_marks_missing_without_mutating_input() -> None:
    frame = pd.DataFrame({"颜色": ["蓝", None], "类型": ["高钾", "铅钡"]})
    result = prepare_categorical_data(frame, ["颜色", "类型"])
    assert result.to_dict(orient="records") == [
        {"颜色": "蓝", "类型": "高钾"},
        {"颜色": "未知", "类型": "铅钡"},
    ]
    assert pd.isna(frame.loc[1, "颜色"])


def test_cramers_v_is_one_for_identical_balanced_binary_variables() -> None:
    table = pd.DataFrame([[20, 0], [0, 20]])
    assert cramers_v_bias_corrected(table) == pytest.approx(1.0)


def test_cramers_v_is_zero_for_independent_balanced_variables() -> None:
    table = pd.DataFrame([[10, 10], [10, 10]])
    assert cramers_v_bias_corrected(table) == pytest.approx(0.0)
```

- [ ] **Step 2: 运行测试并确认红灯**

Run: `uv run pytest tests/analysis/test_categorical.py -v`

Expected: FAIL，指出 `cumcm2022c.analysis.categorical` 不存在。

- [ ] **Step 3: 实现数据准备与偏差校正 Cramér’s V**

```python
from collections.abc import Sequence

import pandas as pd
from scipy.stats import chi2_contingency


def prepare_categorical_data(
    frame: pd.DataFrame,
    columns: Sequence[str],
    missing_label: str = "未知",
) -> pd.DataFrame:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing categorical columns: {', '.join(missing)}")
    result = frame.loc[:, list(columns)].copy()
    return result.fillna(missing_label).astype("string")


def cramers_v_bias_corrected(contingency: pd.DataFrame) -> float:
    observed = contingency.to_numpy()
    n = int(observed.sum())
    if n <= 1 or min(observed.shape) <= 1:
        return 0.0
    chi2 = float(chi2_contingency(observed, correction=False)[0])
    rows, columns = observed.shape
    phi2 = chi2 / n
    phi2_corrected = max(0.0, phi2 - ((columns - 1) * (rows - 1)) / (n - 1))
    rows_corrected = rows - ((rows - 1) ** 2) / (n - 1)
    columns_corrected = columns - ((columns - 1) ** 2) / (n - 1)
    denominator = min(rows_corrected - 1, columns_corrected - 1)
    return 0.0 if denominator <= 0 else float((phi2_corrected / denominator) ** 0.5)
```

- [ ] **Step 4: 运行测试并确认绿灯**

Run: `uv run pytest tests/analysis/test_categorical.py -v`

Expected: 3 tests PASS。

- [ ] **Step 5: 写两两统计与矩阵失败测试**

```python
from cumcm2022c.analysis.categorical import (
    association_matrix,
    pairwise_categorical_associations,
)


def test_pairwise_associations_cover_six_pairs_and_flag_sparse_tables() -> None:
    frame = pd.DataFrame(
        {
            "纹饰": ["A", "A", "B", "B", "C", "C"],
            "类型": ["高钾", "铅钡", "高钾", "铅钡", "高钾", "铅钡"],
            "颜色": ["c1", "c2", "c3", "c4", "c5", "c6"],
            "表面风化": ["无风化", "风化", "无风化", "风化", "无风化", "风化"],
        }
    )
    columns = ["纹饰", "类型", "颜色", "表面风化"]
    result = pairwise_categorical_associations(frame, columns)
    assert len(result) == 6
    assert set(result.columns) == {
        "variable_1", "variable_2", "n", "chi2", "dof", "p_value",
        "cramers_v", "min_expected", "low_expected_ratio", "chi_square_reliable",
    }
    color_rows = result[
        (result["variable_1"] == "颜色") | (result["variable_2"] == "颜色")
    ]
    assert not color_rows["chi_square_reliable"].any()


def test_association_matrix_is_symmetric_with_expected_diagonal() -> None:
    frame = pd.DataFrame(
        {"a": ["x", "x", "y", "y"], "b": ["u", "u", "v", "v"], "c": ["m"] * 4}
    )
    results = pairwise_categorical_associations(frame, ["a", "b", "c"])
    matrix = association_matrix(results, ["a", "b", "c"], "cramers_v")
    assert matrix.equals(matrix.T)
    assert matrix.values.diagonal().tolist() == [1.0, 1.0, 1.0]
```

- [ ] **Step 6: 实现两两统计与矩阵整理**

实现 `pairwise_categorical_associations`，使用 `itertools.combinations` 遍历六组变量对；对常量变量产生的退化列联表返回 `chi2=0`、`dof=0`、`p_value=1`、`cramers_v=0`。可靠性条件为 `min_expected >= 1` 且 `low_expected_ratio <= 0.2`。

实现 `association_matrix`，按结果表双向填充；`cramers_v` 对角线为 1、`p_value` 对角线为 0、`chi_square_reliable` 对角线为 `True`。

- [ ] **Step 7: 运行统计测试并提交**

Run: `uv run pytest tests/analysis/test_categorical.py -v`

Expected: 5 tests PASS。

```bash
git add src/cumcm2022c/analysis tests/analysis/test_categorical.py
git commit -m "feat(analysis): add categorical association statistics"
```

### Task 3: 以 TDD 实现可复用图形

**Files:**
- Create: `src/cumcm2022c/visualization/categorical.py`
- Create: `tests/visualization/test_categorical.py`

- [ ] **Step 1: 写绘图失败测试**

```python
import matplotlib
import pandas as pd

matplotlib.use("Agg")

from cumcm2022c.visualization.categorical import (
    plot_association_heatmaps,
    plot_category_counts,
    plot_weathering_proportions,
)


def test_categorical_plots_return_expected_axes_without_mutating_data() -> None:
    frame = pd.DataFrame(
        {
            "纹饰": ["A", "B", "A", "B"],
            "类型": ["高钾", "高钾", "铅钡", "铅钡"],
            "颜色": ["蓝", "未知", "蓝", "绿"],
            "表面风化": ["无风化", "风化", "风化", "无风化"],
        }
    )
    original = frame.copy(deep=True)
    columns = frame.columns.tolist()
    identity = pd.DataFrame(1.0, index=columns, columns=columns)
    reliable = pd.DataFrame(True, index=columns, columns=columns)

    count_figure, count_axes = plot_category_counts(frame, columns)
    heat_figure, heat_axes = plot_association_heatmaps(identity, identity, reliable)
    weather_figure, weather_axes = plot_weathering_proportions(
        frame, ["纹饰", "类型", "颜色"]
    )

    assert len(count_axes.flat) == 4
    assert len(heat_axes.flat) == 2
    assert len(weather_axes.flat) == 3
    pd.testing.assert_frame_equal(frame, original)
    for figure in (count_figure, heat_figure, weather_figure):
        figure.canvas.draw()
```

- [ ] **Step 2: 运行测试并确认红灯**

Run: `uv run pytest tests/visualization/test_categorical.py -v`

Expected: FAIL，指出可视化模块不存在。

- [ ] **Step 3: 实现最小可视化函数**

使用 `matplotlib.pyplot.subplots` 和 Seaborn 实现三组图。`plot_category_counts` 使用 2×2 网格；`plot_association_heatmaps` 使用 1×2 网格并将不可靠 p 值注释追加 `†`；`plot_weathering_proportions` 使用 1×3 网格并将列顺序固定为 `无风化`、`风化`。所有函数返回 `(figure, axes)`，不调用 `show()`。

`configure_chinese_fonts` 从 `Microsoft YaHei`、`SimHei`、`Noto Sans CJK SC`、`WenQuanYi Micro Hei`、`Arial Unicode MS` 中选择首个已安装字体，设置 `font.sans-serif` 与 `axes.unicode_minus=False`，找不到时返回 `None` 并发出 `RuntimeWarning`。

- [ ] **Step 4: 运行测试并提交**

Run: `uv run pytest tests/visualization/test_categorical.py -v`

Expected: PASS，图形可在 Agg 后端绘制。

```bash
git add src/cumcm2022c/visualization/categorical.py tests/visualization/test_categorical.py
git commit -m "feat(visualization): add categorical association plots"
```

### Task 4: 创建简洁的问题一 Notebook

**Files:**
- Create: `notebooks/10_question1_weathering.ipynb`
- Modify: `README.md`

- [ ] **Step 1: 创建无函数定义的 Notebook**

Notebook 包含七个单元格：标题与方法说明；导入及路径；数据准备；类别频数图；六组结果表；两张热力图；三张风化比例图。代码单元只调用以下接口：

```python
from cumcm2022c.analysis.categorical import (
    association_matrix,
    pairwise_categorical_associations,
    prepare_categorical_data,
)
from cumcm2022c.data.load import load_table
from cumcm2022c.visualization.categorical import (
    configure_chinese_fonts,
    plot_association_heatmaps,
    plot_category_counts,
    plot_weathering_proportions,
)
```

分析变量固定为 `CATEGORICAL_COLUMNS = ["纹饰", "类型", "颜色", "表面风化"]`，预测变量固定为前三项。Notebook 中不得出现 `def `。

- [ ] **Step 2: 更新 README**

在 Notebook 列表中增加 `10_question1_weathering.ipynb`，说明其输出 Cramér’s V、卡方诊断和风化比例图。

- [ ] **Step 3: 静态验证 Notebook**

Run: `uv run python -m json.tool notebooks/10_question1_weathering.ipynb`

Expected: exit 0。

Run: `rg -n 'def ' notebooks/10_question1_weathering.ipynb`

Expected: exit 1，无匹配。

- [ ] **Step 4: 从头执行 Notebook**

Run: `uv run jupyter nbconvert --execute --to notebook --inplace notebooks/10_question1_weathering.ipynb`

Expected: exit 0，所有代码单元具有执行计数，输出包含结果表和三组图形。

- [ ] **Step 5: 提交 Notebook 与文档**

```bash
git add notebooks/10_question1_weathering.ipynb README.md
git commit -m "docs(analysis): add question one association notebook"
```

### Task 5: 全面验证、合并与同步

**Files:**
- Modify: only files changed by formatting when necessary

- [ ] **Step 1: 格式和静态检查**

Run: `uv run ruff format .`

Run: `uv run ruff check .`

Expected: 无错误。

- [ ] **Step 2: 完整测试**

Run: `uv run pytest -v`

Expected: 原有 8 项测试与新增测试全部 PASS。

- [ ] **Step 3: 验证真实统计结果**

Run: `uv run python -c "import pandas as pd; from cumcm2022c.analysis.categorical import pairwise_categorical_associations, prepare_categorical_data; f=pd.read_csv('data/raw/form_1.csv', encoding='utf-8-sig'); c=['纹饰','类型','颜色','表面风化']; r=pairwise_categorical_associations(prepare_categorical_data(f,c),c); assert len(r)==6; assert len(prepare_categorical_data(f,c))==58; print(r.to_string(index=False))"`

Expected: 输出六行统计结果且断言通过。

- [ ] **Step 4: 检查改动边界**

Run: `git status --short --branch`

Expected: 功能工作树干净；主工作区中用户运行产生的 `00_data_inspection.ipynb` 输出仍保持未提交状态。

- [ ] **Step 5: 按 finishing-a-development-branch 流程整合并复验**

将功能分支快进合并至 `main`，在主工作区重新运行 `uv run pytest -v`、`uv run ruff check .` 与 `uv run ruff format --check .`。不得暂存或覆盖用户修改的 `notebooks/00_data_inspection.ipynb`。

- [ ] **Step 6: 同步远程并核对提交**

Run: `git push origin main`

Run: `git fetch --prune origin`

Run: `git rev-parse HEAD origin/main`

Expected: 本地 `HEAD` 与 `origin/main` 输出相同提交哈希。
