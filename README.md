# 2022 CUMCM C：古代玻璃成分分析仿真

本仓库用于复现 2022 年全国大学生数学建模竞赛 C 题。当前阶段提供可复现的数据读取、转换和校验基础；具体数学模型将在建模方案确定后实现于 `src/cumcm2022c/simulation/`。

## 环境

项目使用 [uv](https://docs.astral.sh/uv/) 管理 Python、依赖和命令：

```bash
uv sync
```

不要使用 `pip` 直接修改环境。依赖变更使用 `uv add <package>`。

## 数据

`data/raw/` 保存已验证且纳入版本控制的机器可读源数据：

- `problem.txt`：由题目 PDF 转换的 UTF-8 文本；
- `form_1.csv`：58 行、5 列的文物基本信息；
- `form_2.csv`：69 行、15 列的已分类样品成分；
- `form_3.csv`：8 行、16 列的待分类样品成分；
- `manifest.json`：原始 XLSX 及三个 CSV 的 SHA-256、行列数和映射关系。

仓库不保留 PDF 或 XLSX 二进制原件。CSV 使用 UTF-8 with BOM，空单元格保持缺失，不自动解释为 0。`data/interim/` 用于临时转换，`data/processed/` 用于未来的清洗结果和模型输入，两者的生成内容默认不提交。

如需转换另一份同结构工作簿：

```bash
uv run python scripts/prepare_data.py --source /path/to/附件.xlsx --output /path/to/output
```

## Python 接口

```python
from cumcm2022c.data.load import load_table
from cumcm2022c.data.validate import validate_composition_sums

basic = load_table("form_1")
classified = load_table("form_2")
unknown = load_table("form_3")
```

关键数据处理和仿真代码必须位于 `src/cumcm2022c/`，Notebook 仅负责探索、参数配置和结果展示。

## Notebook

```bash
uv run jupyter lab
```

- `notebooks/00_data_inspection.ipynb`：查看表结构、缺失值和成分总和有效性；
- `notebooks/01_model_simulation.ipynb`：等待数学模型后使用的实验骨架。
- `notebooks/10_question1_weathering.ipynb`：问题一分类变量的 Cramér's V、卡方诊断和风化比例图。

## 质量检查

```bash
uv run pytest -v
uv run ruff format --check .
uv run ruff check .
```

题目规定化学成分总和处于闭区间 `[85, 105]` 时数据有效。基础校验只报告问题，不删除样本、不填补缺失值，也不修改原始比例。
