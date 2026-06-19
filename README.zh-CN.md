# 优化建模 Skill

[English](README.md) | 简体中文

`optimization-modeling` 是给 coding agent 使用的通用优化建模 Skill。它帮助 agent 读取具体优化问题，建立经过 review 的数学模型，分类问题类型，选择 solver 路由，在合适时生成或改写求解代码，解析证据，并诊断失败原因。

推荐的使用方式很简单：让你的 coding agent 自己安装这个 Skill，然后让它用这个 Skill 处理你的优化问题。环境路径、复制、软链接、配置和重载都尽量交给 agent 做。

## 这个 Skill 做什么

这个独立 Skill 帮助 coding agent 在执行前把优化问题转成经过 review 的数学模型。当输入是自然语言、
LaTeX、论文片段、数据、源码、solver error，或一个需要分类、选择 solver route、生成有边界代码并解释证据的现有模型时，直接使用它。

它可以单独作为通用优化建模和 solver routing 的入口。

## 安装 / 加载

### 一句话安装

把下面这句话发给你的 coding agent：

```text
请帮我安装 `optimization-modeling` skill，链接是：https://github.com/VeryMath/AI4Math-Optimization.git，分支：kn-Xu。请读取 `.agent.md`，安装其中声明的 Skill entrypoint，验证 `$optimization-modeling` 可用，并告诉我是否需要重启 agent。
```

如果你已经有这个 skill 仓库的本地文件夹，把链接换成本地路径即可。clone、link、配置、reload/restart 检查和验证都交给 coding agent 处理。

## 快速开始

```text
使用 $optimization-modeling。

我有一个优化问题。请先读取问题，建立 modeling_checkpoint.md，列出变量、目标函数、
约束、维度、数据、歧义点和候选 solver route。不要运行 solver，直到我回复 approve。
```

## 如何交互使用

推荐使用 checkpoint 循环：

```text
优化问题 -> 建模 checkpoint -> solver 路由 -> approve / revise / reject / skip
        -> 获批运行 -> 证据总结 -> 下一轮 checkpoint
```

`approve` 表示执行下一步，`revise` 表示先修改模型或路线，`reject` 表示停止当前路线，
`skip` 表示跳过当前阶段。安装、求解器运行、源码修改、长时间任务和最终数值/数学结论前都应先问用户。

## 开始优化问题交互

安装完成后，开一个新对话，发送：

```text
使用 $optimization-modeling。
```

Skill 应该先只问交互语言：

```text
你想用中文还是英文交流？
```

选择语言后，直接发送具体优化问题。自然语言、LaTeX、论文片段、源码、README 命令、数据描述、`.mat`/`.npz`/`.json`/`.yaml`/CSV 文件，或已有 `problem.yaml` 都可以。

agent 接下来应该建模、暴露歧义、请你确认模型、提出 solver 路由，并且只有在你批准后才运行代码。examples、solver docs 和代码模板都是辅助材料；主线仍然是模型和 solver route。

## 关于这个 Skill

`optimization-modeling` 是优化任务的统一入口。用户给出具体问题；agent 负责把它转成可 review 的模型，选择合适的 solver 生态，并解释数值证据。

这个 Skill 会引导 agent：

- 先读具体问题，再决定需要追问什么
- 识别变量、目标函数、约束、维度、数据和歧义点
- 必要时对照导入的 OptSkills references
- 在生成可执行 solver code 前，先建立 modeling checkpoint
- 分类 LP、MILP、QP、SOCP、SDP、NLP、least squares、manifold optimization 等问题类型
- 把确认后的模型路由到 CVXPY、Pyomo、SciPy/HiGHS、SDPT3、CVX、YALMIP、IPOPT、CasADi、Manopt、Pymanopt、Geoopt、商业 solver 或仓库原生方法等 solver 生态
- 生成或改写受限的求解入口，并且只在批准后运行
- 报告目标值、feasibility、solver status、数值警告和失败原因

它本身不是 solver，而是一个 workflow layer：帮助 coding agent 更谨慎地使用 solver，并把模型 review 和执行批准保持可见。

## 示例材料

examples 是可选辅助材料，用于测试和 few-shot 参考，不是主流程。主流程仍然是：理解用户的问题，建立经过 review 的模型，选择 solver 路由，并且只在批准后运行。

- 经典 LP/MILP examples：[examples/lp-milp-example-prompts.zh-CN.md](examples/lp-milp-example-prompts.zh-CN.md) 和 [examples/lp-milp-example-prompts.md](examples/lp-milp-example-prompts.md) 覆盖运输 LP、指派 MILP、集合覆盖、设施选址、网络流、调度，以及自然语言到 spec 的转换。配套的 [examples/lp-milp-problem-specs.md](examples/lp-milp-problem-specs.md) 给出 schema-compatible 的 `problem.yaml` drafts。

## 维护者检查

在仓库根目录运行：

```bash
python <path-to-skill-validator>/quick_validate.py skills/optimization-modeling
python -m pytest -q
```

Skill 指令在 [skills/optimization-modeling/SKILL.md](skills/optimization-modeling/SKILL.md)。solver 路由细节在 `skills/optimization-modeling/references/` 目录下。
