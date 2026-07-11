# C 题仿真项目数据基础 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立由 uv 管理、同时支持 Python 脚本和 Notebook 的可复现数据项目，并将三张 Excel 工作表确定性转换为可校验的 CSV。

**Architecture:** 二进制原件只用于一次性转换；题面 UTF-8 文本、三张 CSV 与转换清单保存在 `data/raw` 并纳入版本控制。`cumcm2022c.data` 包负责转换、统一读取和业务校验，Notebook 只调用包接口进行探索或仿真实验，后续数学模型进入独立的 `simulation` 包。

**Tech Stack:** Python 3.11+, uv, pandas, openpyxl, pandera, pytest, ruff, JupyterLab

---

### Task 1: 初始化 uv 项目与仓库目录

**Files:**
- Create: `pyproject.toml`
- Create: `.python-version`
- Create: `.gitignore`
- Create: `src/cumcm2022c/__init__.py`
- Create: `src/cumcm2022c/data/__init__.py`
- Create: `src/cumcm2022c/simulation/__init__.py`
- Create: `src/cumcm2022c/visualization/__init__.py`
- Create: `data/processed/.gitkeep`
- Create: `reports/figures/.gitkeep`
- Create: `reports/tables/.gitkeep`

- [ ] **Step 1: 使用 uv 创建包项目**

Run: `uv init --lib --name cumcm2022c --python 3.11`

Expected: 生成 `pyproject.toml`、`.python-version` 和 `src/cumcm2022c`。

- [ ] **Step 2: 添加运行与开发依赖**

Run: `uv add pandas openpyxl pandera jupyterlab ipykernel`

Run: `uv add --dev pytest ruff`

Expected: `pyproject.toml` 更新并生成 `uv.lock`。

- [ ] **Step 3: 配置 pyproject 工具段**

在 `pyproject.toml` 中加入：

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
```

- [ ] **Step 4: 建立目录和忽略规则**

`.gitignore` 必须忽略：

```gitignore
.venv/
.pytest_cache/
.ruff_cache/
__pycache__/
*.py[cod]
.ipynb_checkpoints/
data/interim/*
!data/interim/.gitkeep
data/processed/*
!data/processed/.gitkeep
reports/figures/*
!reports/figures/.gitkeep
reports/tables/*
!reports/tables/.gitkeep
tmp/
```

- [ ] **Step 5: 建立目录并验证环境**

Run: `mkdir -p data/raw data/interim data/processed reports/figures reports/tables notebooks scripts tests/data tests/fixtures`

Run: `uv sync`

Expected: 环境同步成功；二进制原件暂留仓库根目录，直到 Task 4 完成转换校验。

- [ ] **Step 6: 提交基础骨架**

```bash
git add pyproject.toml uv.lock .python-version .gitignore src data/processed reports
git commit -m "build(repo): initialize uv project structure"
```

### Task 2: 以 TDD 实现确定性 Excel 转换

**Files:**
- Create: `tests/data/test_convert.py`
- Create: `src/cumcm2022c/data/convert.py`

- [ ] **Step 1: 写转换成功的失败测试**

```python
from pathlib import Path

import pandas as pd

from cumcm2022c.data.convert import convert_workbook


def test_convert_workbook_writes_csvs_and_stable_manifest(tmp_path: Path) -> None:
    source = tmp_path / "source.xlsx"
    output = tmp_path / "out"
    with pd.ExcelWriter(source, engine="openpyxl") as writer:
        pd.DataFrame({"编号": [1], "颜色": ["蓝"]}).to_excel(
            writer, sheet_name="表单1", index=False
        )
        pd.DataFrame({"采样点": ["01"], "二氧化硅(SiO2)": [90.0]}).to_excel(
            writer, sheet_name="表单2", index=False
        )
        pd.DataFrame({"文物编号": ["A1"], "二氧化硅(SiO2)": [None]}).to_excel(
            writer, sheet_name="表单3", index=False
        )

    first = convert_workbook(source, output)
    second = convert_workbook(source, output)

    assert sorted(path.name for path in output.glob("*.csv")) == [
        "form_1.csv", "form_2.csv", "form_3.csv"
    ]
    assert first == second
    assert first["source"]["sha256"]
    assert [sheet["name"] for sheet in first["sheets"]] == ["表单1", "表单2", "表单3"]
    assert "generated_at" not in first
```

- [ ] **Step 2: 运行测试并确认因模块缺失而失败**

Run: `uv run pytest tests/data/test_convert.py -v`

Expected: FAIL，指出 `cumcm2022c.data.convert` 不存在。

- [ ] **Step 3: 实现最小转换器**

`convert_workbook(source: Path, output_dir: Path) -> dict[str, object]` 必须：校验三张表、按 `form_1.csv` 至 `form_3.csv` 输出 `utf-8-sig` CSV、计算源文件和 CSV 的 SHA-256，并用 `ensure_ascii=False, sort_keys=True, indent=2` 写出 `manifest.json`。

- [ ] **Step 4: 运行测试并确认通过**

Run: `uv run pytest tests/data/test_convert.py -v`

Expected: PASS。

- [ ] **Step 5: 添加缺失工作表测试并确认红灯**

```python
def test_convert_workbook_rejects_missing_sheet(tmp_path: Path) -> None:
    source = tmp_path / "source.xlsx"
    with pd.ExcelWriter(source, engine="openpyxl") as writer:
        pd.DataFrame({"编号": [1]}).to_excel(writer, sheet_name="表单1", index=False)

    with pytest.raises(ValueError, match="表单2.*表单3"):
        convert_workbook(source, tmp_path / "out")
```

Run: `uv run pytest tests/data/test_convert.py::test_convert_workbook_rejects_missing_sheet -v`

Expected: FAIL，转换器尚未产生包含缺失表名的错误。

- [ ] **Step 6: 实现缺失表校验并确认绿灯**

Run: `uv run pytest tests/data/test_convert.py -v`

Expected: 全部 PASS。

- [ ] **Step 7: 提交转换器**

```bash
git add src/cumcm2022c/data/convert.py tests/data/test_convert.py
git commit -m "feat(data): add deterministic workbook conversion"
```

### Task 3: 以 TDD 实现统一读取与成分校验

**Files:**
- Create: `tests/data/test_load.py`
- Create: `tests/data/test_validate.py`
- Create: `src/cumcm2022c/data/load.py`
- Create: `src/cumcm2022c/data/validate.py`

- [ ] **Step 1: 写读取器失败测试**

```python
def test_load_table_reads_known_form(tmp_path: Path) -> None:
    pd.DataFrame({"编号": [1]}).to_csv(tmp_path / "form_1.csv", index=False, encoding="utf-8-sig")
    result = load_table("form_1", tmp_path)
    assert result.to_dict(orient="records") == [{"编号": 1}]


def test_load_table_rejects_unknown_form(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="form_1, form_2, form_3"):
        load_table("unknown", tmp_path)
```

- [ ] **Step 2: 运行读取测试并确认红灯**

Run: `uv run pytest tests/data/test_load.py -v`

Expected: FAIL，指出 `load_table` 不存在。

- [ ] **Step 3: 实现并验证读取器**

实现 `load_table(name: Literal["form_1", "form_2", "form_3"], data_dir: Path) -> pd.DataFrame`，然后运行：

Run: `uv run pytest tests/data/test_load.py -v`

Expected: 全部 PASS。

- [ ] **Step 4: 写成分和边界失败测试**

```python
def test_validate_composition_sum_includes_boundaries() -> None:
    frame = pd.DataFrame({"SiO2": [85.0, 105.0, 84.99, 105.01], "PbO": [None] * 4})
    result = validate_composition_sums(frame, ["SiO2", "PbO"])
    assert result["composition_sum"].tolist() == [85.0, 105.0, 84.99, 105.01]
    assert result["is_valid_composition"].tolist() == [True, True, False, False]
    assert frame["PbO"].isna().all()
```

- [ ] **Step 5: 运行校验测试并确认红灯**

Run: `uv run pytest tests/data/test_validate.py -v`

Expected: FAIL，指出 `validate_composition_sums` 不存在。

- [ ] **Step 6: 实现并验证成分校验**

实现 `validate_composition_sums(frame, component_columns, lower=85.0, upper=105.0)`，返回带 `composition_sum` 与 `is_valid_composition` 的副本，不修改输入。

Run: `uv run pytest tests/data/test_validate.py -v`

Expected: PASS。

- [ ] **Step 7: 提交读取和校验模块**

```bash
git add src/cumcm2022c/data/load.py src/cumcm2022c/data/validate.py tests/data/test_load.py tests/data/test_validate.py
git commit -m "feat(data): add table loading and composition validation"
```

提交前再添加 `validate_table_structure(frame, identifier_columns, component_columns)` 的测试与实现：重复或空表头、缺失标识、不可转为数值的成分均返回结构化问题列表；使用 Pandera 的惰性校验收集同一张表中的全部问题，不删除或改写输入行。测试必须分别断言问题代码 `duplicate_column`、`missing_identifier` 和 `non_numeric_component`。

### Task 4: 增加数据准备 CLI 并处理真实附件

**Files:**
- Create: `tests/test_prepare_data.py`
- Create: `scripts/prepare_data.py`
- Create: `data/raw/problem.txt`
- Create: `data/raw/form_1.csv`
- Create: `data/raw/form_2.csv`
- Create: `data/raw/form_3.csv`
- Create: `data/raw/manifest.json`

- [ ] **Step 1: 写 CLI 失败测试**

```python
def test_prepare_data_help_runs() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/prepare_data.py", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--source" in result.stdout
    assert "--output" in result.stdout
```

- [ ] **Step 2: 运行测试并确认红灯**

Run: `uv run pytest tests/test_prepare_data.py -v`

Expected: FAIL，因为脚本不存在。

- [ ] **Step 3: 实现 argparse 入口并确认绿灯**

脚本要求显式指定 `--source` 和 `--output`，并打印每张表的输出文件、行列数与哈希。

Run: `uv run pytest tests/test_prepare_data.py -v`

Expected: PASS。

- [ ] **Step 4: 转换真实附件并核对稳定性**

Run: `uv run python scripts/prepare_data.py --source 附件.xlsx --output data/raw`

Run: `sha256sum data/raw/form_*.csv data/raw/manifest.json`

重复运行同一命令和 `sha256sum`。使用 `pdftotext -layout C题.pdf data/raw/problem.txt` 生成 UTF-8 题面文本，确认文本包含“问题 1”至“问题 4”。确认 CSV 可由 pandas 读取、题面文本可由 UTF-8 解码后，删除根目录的 `附件.xlsx`、`C题.pdf`。

Expected: 两次列出的四个哈希完全一致；清单记录表单 1、2、3。

- [ ] **Step 5: 提交 CLI**

```bash
git add scripts/prepare_data.py tests/test_prepare_data.py data/raw
git commit -m "feat(data): add preparation command"
```

### Task 5: 增加 Notebook 与使用说明

**Files:**
- Create: `notebooks/00_data_inspection.ipynb`
- Create: `notebooks/01_model_simulation.ipynb`
- Create: `README.md`

- [ ] **Step 1: 创建数据勘察 Notebook**

Notebook 导入 `load_table` 和 `validate_composition_sums`，读取三个表并展示形状、字段、缺失计数和表单 2/3 的成分和有效性摘要，不写入数据文件。

- [ ] **Step 2: 创建仿真占位 Notebook**

Notebook 说明模型代码必须进入 `src/cumcm2022c/simulation`，并提供导入区、参数区、执行区和结果展示区；不实现任何题目模型。

- [ ] **Step 3: 编写 README**

README 必须包含：项目目的、目录说明、`uv sync`、数据准备、测试、ruff 检查和 `uv run jupyter lab` 命令，以及原始/中间/处理数据的语义。

- [ ] **Step 4: 验证 Notebook JSON 和导入**

Run: `uv run python -m json.tool notebooks/00_data_inspection.ipynb`

Run: `uv run python -m json.tool notebooks/01_model_simulation.ipynb`

Run: `uv run python -c "from cumcm2022c.data.load import load_table; from cumcm2022c.data.validate import validate_composition_sums"`

Expected: exit 0。

- [ ] **Step 5: 提交文档与 Notebook**

```bash
git add README.md notebooks
git commit -m "docs(repo): add analysis and simulation workflow"
```

### Task 6: 全面验证与收尾

**Files:**
- Modify: plan checklist only if necessary

- [ ] **Step 1: 格式化并检查**

Run: `uv run ruff format .`

Run: `uv run ruff check .`

Expected: 无错误。

- [ ] **Step 2: 运行完整测试**

Run: `uv run pytest -v`

Expected: 所有测试 PASS，无 warning。

- [ ] **Step 3: 从干净的中间数据目录重建数据**

Run: `uv run python scripts/prepare_data.py`

Expected: 生成三个 CSV 与一个清单，退出状态为 0。

- [ ] **Step 4: 检查仓库状态和提交历史**

Run: `git status --short --branch`

Run: `git log --oneline --decorate -8`

Expected: `main` 分支；仅被 `.gitignore` 排除的生成数据不出现在状态中；提交均符合 Conventional Commits。

- [ ] **Step 5: 提交格式化或遗漏的非生成文件**

若 Step 1 产生受控文件改动：

```bash
git add pyproject.toml src tests scripts README.md notebooks
git commit -m "style(repo): normalize project formatting"
```
