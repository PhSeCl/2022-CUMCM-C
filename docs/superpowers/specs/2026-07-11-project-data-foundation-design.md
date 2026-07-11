# C 题仿真项目数据基础设计

## 目标

将当前题目材料初始化为一个可复现的 Python 数据与仿真项目。项目同时支持脚本化批处理和 Jupyter Notebook 探索，并为后续接收建模手给出的数学模型预留清晰、可测试的仿真实现边界。

本阶段只建设仓库、数据转换、读取和基础校验能力，不实现题目中的统计分析、分类、预测或关联模型。

## 设计原则

- 原始材料不可变：PDF 和 XLSX 只作为输入，不由程序覆盖。
- 计算逻辑模块化：数据处理和后续仿真必须位于 Python 包中，Notebook 不承载唯一实现。
- 结果可复现：同一份原始工作簿重复转换应产生内容一致的 CSV。
- 数据语义保真：Excel 空白单元格保持缺失，不自动解释为数值 0。
- 分层存储：原始、转换中间数据、建模数据和报告产物相互隔离。
- 小步扩展：当前不预设尚未收到的数学模型接口细节。

## 技术栈

- Python 3.11 或更高版本
- `uv` 管理环境、依赖和命令
- `pandas` 与 `openpyxl` 读取 Excel、输出 CSV
- `pandera` 定义并执行表级数据约束
- `jupyterlab` 与 `ipykernel` 支持探索性分析
- `pytest` 进行自动化测试
- `ruff` 负责格式化和静态检查

不引入专用工作流编排框架；本项目的数据规模和流水线复杂度不足以支持该额外成本。

## 仓库结构

```text
2022-CUMCM-C/
├── data/
│   ├── raw/                 # C题.pdf、附件.xlsx
│   ├── interim/             # 每张工作表无损拆分出的 CSV
│   └── processed/           # 后续清洗和模型输入
├── notebooks/
│   ├── 00_data_inspection.ipynb
│   └── 01_model_simulation.ipynb
├── scripts/
│   └── prepare_data.py
├── src/cumcm2022c/
│   ├── data/
│   │   ├── convert.py
│   │   ├── load.py
│   │   └── validate.py
│   ├── simulation/
│   └── visualization/
├── tests/
│   ├── data/
│   └── fixtures/
├── reports/
│   ├── figures/
│   └── tables/
├── docs/
├── pyproject.toml
├── README.md
└── .gitignore
```

空目录使用 `.gitkeep` 保留。生成的中间数据、处理后数据和报告产物不进入 Git；原始题目材料进入 Git，以固定本次竞赛复现所使用的数据版本。

## 数据转换

`scripts/prepare_data.py` 是用户入口，内部调用 `cumcm2022c.data.convert`：

1. 读取 `data/raw/附件.xlsx`。
2. 校验工作簿包含且仅处理 `表单1`、`表单2`、`表单3`。
3. 将各工作表分别写为 UTF-8 with BOM CSV，确保 Excel 与常用中文数据工具可直接打开。
4. 保留原始列名、行顺序、列顺序和空白单元格语义。
5. 写出 `data/interim/manifest.json`，记录源文件 SHA-256、各表名称、行列数、CSV 文件名和 CSV SHA-256。

输出文件使用稳定的 ASCII 名称：

- `form_1.csv`
- `form_2.csv`
- `form_3.csv`
- `manifest.json`

清单不写入运行时间，避免相同输入仅因时间戳而产生不同内容。文件修改时间不属于可复现性判断依据。

## 读取接口

`cumcm2022c.data.load` 提供按逻辑表名读取数据的统一入口。调用者不直接拼接文件路径。读取器负责：

- 将 `form_1`、`form_2`、`form_3` 映射至对应 CSV；
- 使用明确的 UTF-8 编码；
- 对未知表名给出包含允许值的错误；
- 保留缺失值，避免静默填充。

Notebook 和后续仿真模块只通过该入口消费中间数据。

## 基础校验

`cumcm2022c.data.validate` 将结构问题与题目业务规则分开报告：

- 工作表与 CSV 是否存在；
- 表头是否重复或缺失；
- 文物编号或采样点标识是否缺失；
- 化学成分列是否可解析为数值；
- 每行化学成分比例和是否处于题目规定的 `[85, 105]` 有效区间。

校验不会删除无效行，也不会自动修复数据。它返回结构化结果，由脚本打印摘要；后续处理阶段再明确决定如何过滤。

## Notebook 边界

`00_data_inspection.ipynb` 演示统一读取接口并展示三个表的形状、字段、缺失情况和成分和有效性摘要。

`01_model_simulation.ipynb` 仅提供后续实验入口与说明，不预置数学模型。收到建模方案后，模型实现写入 `src/cumcm2022c/simulation/`，Notebook 只导入、配置、运行并展示结果。

## 错误处理

- 缺少源文件、工作表名称不符或输出目录不可写时，数据准备命令以非零状态退出并给出明确路径。
- 已有输出允许被同源数据确定性覆盖；若源文件哈希变化，清单随之更新。
- 不捕获并隐藏解析异常；面向用户的脚本在保留原因的前提下输出简洁错误信息。

## 测试策略

- 使用小型临时 XLSX fixture 测试工作表拆分、中文字段、缺失值和稳定清单。
- 测试缺失工作表时转换失败且错误信息包含表名。
- 测试读取器只接受规定的逻辑表名。
- 测试成分和边界值 85 与 105 有效，边界外无效，缺失成分按求和时忽略但不改写原数据。
- 对真实附件运行数据准备命令，核对三个输出表的行列数与清单哈希。

## 验收标准

- 仓库使用 `main` 分支并具有符合 Conventional Commits 的提交历史。
- `uv sync` 可建立完整环境。
- `uv run python scripts/prepare_data.py` 可从原始 XLSX 生成三个 CSV 和清单。
- 连续运行两次后，所有生成文件的内容哈希保持一致。
- `uv run pytest` 全部通过。
- `uv run ruff check .` 与 `uv run ruff format --check .` 通过。
- README 说明环境初始化、数据准备、测试和 Notebook 启动命令。

## 非目标

- 不在本阶段选择或实现四个问题的数学模型。
- 不填补缺失化学成分，不标准化成分比例，不删除总和无效的数据。
- 不产出比赛论文、最终图表或结论。
- 不建立数据库、Web 界面或通用工作流平台。
