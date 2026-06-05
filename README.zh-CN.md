# AI4Math 优化 Skills

[English](README.md) | 简体中文

AI4Math 优化 Skills 是一个独立的、面向 coding agent 的优化建模与求解项目。它的目标是把数学优化任务转成安全、可检查、可复现的 workflow：理解问题、匹配建模 archetype、形成可 review 的数学模型、选择求解器生态、生成执行代码、请求审批、运行 solver、解析证据，并诊断失败。

这个项目呈现的是完整 Skill 形态，不是一个窄 demo。现在它只有一个统一入口：`optimization-skill`。archetype 匹配、建模检查点、solver 路由、代码生成、执行治理和证据解析，都是同一个 agent workflow 的内部阶段。当前脚本已经支持可选的 OptSkills archetype 搜索，以及结构化 spec 到 SDPT3/CDOpt 的路由、代码生成和日志解析；文档则定义更完整的建模层与 solver 扩展面。

## 核心想法

人类可以给出自然语言目标、论文片段、LaTeX 公式、代码仓库、`.mat` 数据文件，或已经结构化的问题描述。coding agent 使用这个 Skill 来：

1. 识别优化问题 archetype 和建模形式。
2. 借助导入的 OptSkills references 写出可 review 的建模检查点。
3. 把确认后的模型转成结构化 spec。
4. 路由到合适的 solver 后端。
5. 生成求解入口代码，同时不直接改写源项目。
6. 写运行计划，并在执行或改环境前请求批准。
7. 只运行已经批准的命令。
8. 解析 solver 输出、数值状态、证书和失败原因。
9. 报告证据，并提出修复方案或替代 solver 路由。

## 能力地图

| 层级 | 范围 | 当前产物 |
| --- | --- | --- |
| 问题理解 | 自然语言、LaTeX、论文片段、README 命令、本地数据文件、已有源码 | `optimization-skill`, `references/modeling_pipeline.md` |
| 建模转换 | OptSkills archetype 匹配，以及 LP、QP、SOCP、SDP、SQLP、非线性规划、流形优化、源码定义模型 | `references/optskills`, modeling checkpoints, `problem_schema.md` |
| 求解器路由 | SDPT3、CDOpt、已有仓库 solver，以及 CVX/CVXPY/YALMIP/JuMP/Pyomo/MOSEK/SciPy 扩展点 | `references/solver_catalog.md`, `scripts/solver_router.py` |
| 代码生成 | MATLAB/Octave wrapper、Python adapter、日志和结果输出契约 | `references/code_generation_patterns.md`, `scripts/codegen.py` |
| 执行治理 | 运行 solver、安装依赖、编译 MEX、改源码、生成建模 adapter 前的人类审批 | `SKILL.md`, plan artifact contract |
| 结果解析 | solver 状态、目标值、不可行性、数值不稳定、依赖缺失、维度/数据错误 | `scripts/result_parser.py` |
| 报告 | 运行摘要、solver 证据、失败诊断、下一步 solver 选择 | `references/evaluation_reporting.md` |

## Solver 覆盖

当前最具体的后端是：

- **SDPT3**：用于已经确认的半定规划、二阶锥规划、线性锥规划，以及 SQLP 风格的 MATLAB/Octave 问题。辅助脚本可以路由 SQLP-compatible spec，并生成 MATLAB/Octave wrapper：加载 `blk`、`At`、`C`、`b`，设置 `sqlparameters`，调用指定 SDPT3 入口，并保存 solver 证据。
- **CDOpt**：用于已经确认的 Riemannian / 流形约束优化，尤其是 constraint dissolving 思路下的求解流程。辅助脚本可以路由常见流形问题，并生成 Python wrapper：构造 CDOpt manifold，建立 `cdopt.core.problem`，调用 SciPy `optimize.minimize`，并写出 JSON summary。

当前生成式 CDOpt wrapper 支持 `torch`、`numpy`/`np` 和 `jax` 后端的 sphere、oblique、Stiefel、Grassmann、generalized Stiefel、hyperbolic、symplectic Stiefel 等流形族。它要求 objective 以可 import 的 module/function 形式提供，并且问题 spec 已经过 review。只有自然语言或 LaTeX 的问题，仍然会先停在建模检查点，不直接生成可执行代码。

Skill 的结构预留了更大的优化求解器枢纽：

- 建模层：CVX、YALMIP、CVXPY、JuMP、Pyomo。
- 锥规划和 SDP solver：SDPT3、SeDuMi、MOSEK、SCS、Clarabel。
- 光滑和非线性 solver：SciPy optimize、IPOPT 风格路线、仓库自带方法。
- 流形优化：CDOpt、Manopt/Pymanopt 风格路线、正交约束模型。

## 项目结构

- `skills/optimization-skill/SKILL.md`：统一 Skill 指令，用于问题输入、建模、solver 路由、执行治理和证据报告。
- `skills/optimization-skill/agents/openai.yaml`：面向 Skill-aware agent 的 UI 元数据。
- `skills/optimization-skill/references/INDEX.md`：reference 路由索引。
- `skills/optimization-skill/references/optskills/`：完整导入的 OptSkills released libraries，按上游 MIT license 作为 references 打包。
- `skills/optimization-skill/references/problem_schema.md`：标准优化问题 spec。
- `skills/optimization-skill/references/modeling_pipeline.md`：自然语言、LaTeX、源码到模型，以及 OptSkills archetype 工作流。
- `skills/optimization-skill/references/solver_catalog.md`：solver 和建模后端选择规则。
- `skills/optimization-skill/references/code_generation_patterns.md`：生成 adapter 的约定。
- `skills/optimization-skill/references/evaluation_reporting.md`：结果解释和报告规则。
- `skills/optimization-skill/scripts/search_archetypes.py`：在导入的 OptSkills archetype 索引和 Markdown 文件中做可选关键词搜索。
- `skills/optimization-skill/scripts/solver_router.py`：把结构化 spec 路由到求解器后端。
- `skills/optimization-skill/scripts/codegen.py`：生成 SDPT3 MATLAB 或 CDOpt Python 入口。
- `skills/optimization-skill/scripts/result_parser.py`：把 solver 日志解析成紧凑摘要。
- `tests/`：维护校验，覆盖路由、代码生成和日志解析。
- `pyproject.toml`：这个独立项目的 Python 测试和打包元数据。

## Agent 使用流程

1. 把 `skills/optimization-skill/SKILL.md` 作为唯一对外优化入口。
2. 新的交互会话先确认交互语言，然后让用户直接发送具体优化问题。
3. 用 `rg`、`index.json`、文件名、定向阅读和 agent 自己的判断来浏览导入的 OptSkills references。下面这个脚本只是用于缩小大候选集的可选辅助：

```bash
python skills/optimization-skill/scripts/search_archetypes.py --query "minimum cost sets covering all requirements" --limit 5
```

4. 阅读并比较候选 archetype 文件，然后建立建模检查点；执行前先请人类确认数学模型。
5. 按 `skills/optimization-skill/references/problem_schema.md` 规范化确认后的问题。
6. 路由 solver：

```bash
conda run -n ai4math python skills/optimization-skill/scripts/solver_router.py --spec problem.yaml
```

7. 当路由支持代码生成时，生成求解入口：

```bash
conda run -n ai4math python skills/optimization-skill/scripts/codegen.py --spec problem.yaml --out outputs/run_001/generated
```

8. 把生成的入口和精确命令写入 review plan。
9. 在运行 solver、安装依赖、编译 MEX、修改 MATLAB/Python 环境或编辑源码之前，先请求批准。
10. 批准并运行后，解析日志：

```bash
conda run -n ai4math python skills/optimization-skill/scripts/result_parser.py --log outputs/run_001/logs/run.log --out outputs/run_001/results/solver_summary.json
```

11. 报告目标值、可行性、证书、残差、solver 状态、运行时间和失败证据。

## 示例问题描述

```yaml
schema_version: 1
problem_id: demo_sdp
input_type: structured_spec
problem_class: conic_sqlp
objective:
  sense: minimize
data:
  mat_file: data/demo_sdp.mat
solver_preferences:
  backend: auto
  timeout_seconds: 300
sdpt3:
  data_variables:
    blk: blk
    At: At
    C: C
    b: b
  options:
    printlevel: 2
review:
  modeling_status: confirmed
  execution_approval_required: true
```

## 安全边界

- 未经人工批准，不运行生成的求解代码。
- 未经人工批准，不安装 SDPT3、CDOpt、CVX、YALMIP、MATLAB 工具箱、Python solver 包或后端依赖。
- 未经人工批准，不编译 MEX 文件。
- 从自然语言或 LaTeX 得到的模型，必须先转成结构化 spec 并经过 review，不能直接执行。
- 不隐藏数值不确定性；不可行性、弱证书、残差停滞、模糊 solver 状态都要明确报告。

## 验证

在这个文件夹下运行：

```bash
python /Users/conanxu/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/optimization-skill
conda run -n ai4math pytest
```

当前验证结果：这个 Skill 通过格式校验，并且 Python 测试套件通过。
