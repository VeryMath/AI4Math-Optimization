# 优化建模 Skill

[English](README.md) | 简体中文

`optimization-modeling` 是给 coding agent 使用的通用优化建模 Skill。它帮助 agent 读取具体优化问题，建立经过 review 的数学模型，分类问题类型，选择 solver 路由，在合适时生成或改写求解代码，解析证据，并诊断失败原因。

推荐的使用方式很简单：让你的 coding agent 自己安装这个 Skill，然后让它用这个 Skill 处理你的优化问题。环境路径、复制、软链接、配置和重载都尽量交给 agent 做。

## AI4Math 角色

这个 Skill 是 AI4Math 体系里的通用优化建模和 solver 路由层。当问题首先是一个优化模型，
而不是某个特定 package 的任务时使用它：自然语言、LaTeX、论文片段、数据、代码或 solver
失败都应先经过可 review 的模型，再进入执行。

## 交接

上游可能来自 `paper-to-skill`、`discover-math-problems`、计算复现 workflow，或用户直接给出的
优化问题。当 CDOpt/流形结构是核心时交给 `cdopt-optimization`；当主要工作是运行
科研代码仓库时交给科学计算复现 Skill；当已有 evaluator 需要搜索改进时交给
`openevolve-experiment-workflow`。数值 solver 证据、目标值和改进后的程序不是 proof artifacts；
如果它们产生 theorem claims 或 proof obligations，应交给 `rethlas-proving` 或
`lean-formalization`。

## 安装 / 加载

优先从当前仓库 checkout 使用。让 coding agent 读取：

```text
AGENTS.md
SKILL.md
skills/optimization-modeling/SKILL.md
```

如果目标 agent 支持本地 Skill discovery，可以把 `skills/optimization-modeling/`
安装或软链接到它的 Skill 路径，然后按需 reload 或 restart。Codex、Claude、
Gemini 和 OpenCode 的薄 adapter 分别见 `.codex/INSTALL.md`、`CLAUDE.md`、
`GEMINI.md` 和 `.opencode/INSTALL.md`。

远端安装 prompt：

```text
请从 https://github.com/VeryMath/AI4Math-Optimization 安装 optimization-modeling 到你自己的 skill 系统。

如果本地已经有 checkout，就使用本地版本；否则 clone 这个仓库。请检测你的环境把 skills 存在哪里，把 skills/optimization-modeling 安装或软链接到正确位置，按需更新 registry 或配置，必要时 reload 或 restart，并验证 $optimization-modeling 可以被发现。
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
