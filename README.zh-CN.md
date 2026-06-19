# CDOpt Optimization

[English](README.md) | 简体中文

`cdopt-optimization` 是一个面向
[CDOpt](https://github.com/cdopt) 与流形约束优化的证据驱动型 agent
工作流层。它把通用编码智能体提升为具备 CDOpt 语境的计算数学协作者：能够建立并评审
优化模型、检查数值栈、参考并改编官方示例、运行受控验证，并只基于持久化证据汇报结果。

它的目标不是让 agent “跑一个优化器” 就结束，而是让 agent 以更接近研究协作的方式工作：
先建模，再审批执行，保留证据，并把数值实验与数值结论清楚分开。

## 这个 Skill 做什么

这个独立 Skill 帮助 coding agent 谨慎处理 CDOpt 和流形约束优化任务。当任务涉及 manifold model、
CDOpt example/backend、solver validation run，或需要在执行代码前审查模型假设的对比实验时，直接使用它。

它可以单独用于 CDOpt-focused modeling、runner generation、smoke test、comparison plan 和有证据支持的 solver summary。

## 安装 / 加载

在你的 coding-agent 环境里 clone 或打开这个 skill 仓库，然后让 coding agent 读取：

```text
AGENTS.md
SKILL.md
cdopt-optimization/SKILL.md
```

如果目标 agent 支持本地 Skill discovery，可以把 `cdopt-optimization/` 安装或软链接到它的
Skill 路径，然后按需 reload 或 restart。Codex、Claude、Gemini 和 OpenCode 的薄
adapter 分别见 `.codex/INSTALL.md`、`CLAUDE.md`、`GEMINI.md` 和
`.opencode/INSTALL.md`。

远端安装 prompt：

```text
请把 https://github.com/VeryMath/AI4Math-Optimization 中的 `cdopt-optimization` 安装到你的 skill 系统里。

如果本地已经有这个 skill 仓库，就直接使用；否则克隆该仓库。检测你的环境在哪里存放 skill，把 cdopt-optimization 文件夹安装或软链接到那里，按需更新注册表或配置，必要时重载或重启，并验证 $cdopt-optimization 可被发现。
```

## 快速开始

```text
Use $cdopt-optimization.

我有一个流形约束优化任务。请先建立 modeling_checkpoint.md，确认变量、流形类型、
shape、objective、constraints、backend 和 solver route。不要安装依赖或运行 solver，
直到我回复 approve。
```

## 如何交互使用

推荐使用 checkpoint 循环：

```text
CDOpt 任务 -> 模型 review -> 计划 -> approve / revise / reject / skip
          -> 获批运行或对比 -> 证据总结 -> 下一轮 checkpoint
```

`approve` 表示执行下一步，`revise` 表示先修改模型或计划，`reject` 表示停止当前路线，
`skip` 表示跳过当前阶段。安装、求解器运行、对比实验扩展、源码修改和最终结论前都应先问用户。

## 为什么需要 CDOpt Optimization

流形优化任务很容易“差一点就对”。代码可能能跑通，但流形维度不对、后端不匹配、梯度与模型
不一致，或者多种方法在不同随机种子和停止准则下被拿来比较。`cdopt-optimization` 为编码智能体提供
一套紧凑的流程约束，用来降低这些风险。

它提供：

- **建模纪律**：变量、定义域、流形、目标函数、约束、维度、后端选择和求解路线先评审再写代码。
- **执行闸门**：安装依赖、运行求解器、执行冒烟测试、扩展对比实验、更改环境和接受最终数学结论前
  都需要明确审批。
- **证据化汇报**：从 JSON、日志和运行摘要中汇报，而不是依赖临时控制台片段或对话记忆。
- **官方示例覆盖**：围绕 CDOpt 官方示例提供本地问题卡、实现模板、问题-代码对和小规模 CPU runner。
- **可复现支架**：确定性合成数据 runner、smoke-test 路由、comparison plan 和 summary artifact
  让实验过程可检查、可复盘。

如果任务并不真正属于 CDOpt、黎曼优化或流形约束建模范畴，本 Skill 会明确说明，并把 agent
引向更通用的优化工作流，而不是强行套用 CDOpt。

## 证据优先的工作流

`cdopt-optimization` 会在每次任务开始时先创建一个独立工作区：`outputs/{run_id}/`。本次任务的
建模 checkpoint、生成代码、日志、JSON 结果、对比表和最终摘要都放在这个目录下，避免证据散落在仓库各处。

```text
outputs/{run_id}/
├── modeling_checkpoint.md
├── plan.md
├── generated/
├── logs/
├── results/
└── RUN_SUMMARY.md
```

在这个工作区内，agent 行为组织成三层 review：

| 层级 | 产物 | 作用 |
| --- | --- | --- |
| 模型 review | `modeling_checkpoint.md` | 在可执行代码之前确认流形类型、维度、目标函数、约束、后端、求解路线和歧义点。 |
| 执行 review | 审批闸门 | 防止未经确认的安装、求解器运行、环境修改、对比矩阵扩展或数值结论。 |
| 结果 review | `solver_summary.json`、`RUN_SUMMARY.md`、`COMPARISON_SUMMARY.md` | 基于保存的状态、目标值、可行性、驻点性代理、耗时、版本和局限性汇报。 |

在方法选择或论文/报告式证据场景中，同一个工作区会增加对比实验闸门：

```text
outputs/{run_id}/
├── modeling_checkpoint.md
├── comparison_plan.md
├── generated/
├── logs/
├── results/
│   ├── method_a.json
│   ├── method_b.json
│   └── comparison_table.csv
└── COMPARISON_SUMMARY.md
```

多方法对比不是默认路径。单方法验证和冒烟测试保持轻量。

## 核心能力

- **依赖验证**：安全检查 CDOpt 及关键数值依赖是否可导入、从哪里加载，以及本地 smoke-test
  套件是否存在。
- **冒烟测试**：获批后路由到本地 CDOpt manifold notebook 套件，或运行小规模 CPU-only 验证。
- **问题建模**：把自然语言、LaTeX、论文片段、源代码或本地 Problem Description 卡片转化为可评审的
  CDOpt 模型。
- **代码改编**：先学习官方 CDOpt 示例，再在模型评审通过后进行有边界的改编。
- **失败诊断**：显式提示依赖错误、API 不匹配、后端/device/dtype 问题、不可行性、驻点性警告和求解器
  终止状态。
- **对比汇报**：通过获批的 `comparison_plan.md` 和方法级证据，支持 solver、backend 或 baseline 对比。

## 官方示例覆盖

官方 [CDOpt 示例](https://cdopt.github.io/examples/) 被分层覆盖：常用、小规模且适合自动验证的部分
提供完整 workflow；资源更重或场景更特殊的部分保留为模板级参考。

| 官方大类 | 本仓库提供的内容 | 深度 |
| --- | --- | --- |
| **Optimization via SciPy** | 每个示例都有 Problem Description 卡片、官方问题-代码对、实现模板和极小 CPU runner 生成器 | 完整工作流 |
| **PyTorch 神经网络训练** | LeNet、单层 RNN、双向 LSTM 的卡片；约束层和序列模型模板；极小 CPU runner 生成器 | LeNet/RNN/LSTM 有卡片和 runner，大型示例为模板级 |
| **JAX/FLAX 神经网络训练** | LeNet 正交核卡片和 JAX/Flax 约束层模板 | 建模卡片 + 模板 |

支持的示例家族包括：Stiefel/Torch/SciPy 字典学习、Stiefel/JAX/JIT 字典学习、带手写导数的
NumPy Stiefel 示例、Oblique 最近相关矩阵估计、Sphere 上的 Bose-Einstein 凝聚、辛 Stiefel
特征值问题，以及 `Conv2d_cdopt`、`Linear_cdopt`、`RNN_cdopt`、`Conv_cdopt`、`Dense_cdopt`
等 CDOpt 神经网络约束层。

分布式 PyTorch 示例需要单独的运行计划、资源评估与审批，不属于冒烟测试。

## 开始一次 CDOpt 会话

安装完成后，新开一个对话，粘贴：

```text
Use $cdopt-optimization.
```

Skill 首先只会询问交互语言：

```text
Would you like to work in Chinese or English?
```

选定语言后，直接发送实际的 CDOpt 任务。自然语言、LaTeX、论文片段、源代码、本地
Problem Description 卡片、依赖检查请求或 comparison plan 请求都可以作为入口。

## 仓库结构

```text
cdopt-optimization/
├── SKILL.md                              # Skill 指令
├── agents/openai.yaml                    # 智能体接口元数据
├── references/
│   ├── INDEX.md                          # 渐进式披露的导航
│   ├── example_prompts.md                # 可直接粘贴的 $cdopt-optimization 提示词
│   ├── cdopt_official_examples.md        # 实现模板
│   ├── few_shots/cdopt_official_pairs.md # 官方“问题-代码”对
│   └── problem-descriptions/             # 本地 Problem Description 卡片
└── scripts/
    ├── check_cdopt_environment.py         # 安全的依赖 / 路径探测
    ├── write_stiefel_dictionary_runner.py # 极小的 SciPy 优化类 runner
    ├── write_constrained_layer_runner.py  # 极小的 PyTorch 约束层 runner
    └── write_constrained_rnn_runner.py    # 极小的 PyTorch RNN/LSTM runner
```

## 维护者快速上手

```bash
# 安全的依赖探测：不安装、不运行求解器
python3 cdopt-optimization/scripts/check_cdopt_environment.py --json

# 生成极小的 Stiefel 字典学习 runner
python3 cdopt-optimization/scripts/write_stiefel_dictionary_runner.py \
  --output-dir .local/cdopt-runs/dictionary_learning_torch_scipy

# 生成极小的 PyTorch 约束层训练 runner
python3 cdopt-optimization/scripts/write_constrained_layer_runner.py \
  --output-dir .local/cdopt-runs/constrained_layer_torch

# 生成极小的 PyTorch RNN/LSTM 训练 runner
python3 cdopt-optimization/scripts/write_constrained_rnn_runner.py \
  --output-dir .local/cdopt-runs/constrained_rnn_torch
```

可选的安装后流形冒烟测试路径，按以下顺序解析：`CDOPT_SMOKE_TEST` 环境变量、
`check_cdopt_environment.py` 报告中的 `smoke_test.path` 字段，或默认值
`~/cdopt_manifold_tests/run_all_notebooks.py`。

## 致谢

- [CDOpt](https://github.com/cdopt) 及其官方示例（<https://cdopt.github.io/examples/>），
  为本仓库提供了问题陈述、代码对和实现模式来源。

参考问题陈述和代码片段仅作为建模与改编的溯源材料保留。请先学习，再把实现选择绑定到
经过评审的模型，不要逐字复制官方示例代码。

## 许可证

基于 [MIT License](LICENSE) 发布。
