# LP/MILP 示例 Prompts

[English](lp-milp-example-prompts.md) | 简体中文

这些 prompts 是用于测试 `$optimization-skill` 处理经典运筹优化问题的示例用户请求，包括 LP、MILP、运输问题、指派问题、集合覆盖、网络流和设施选址。

它们是建模和 solver 路由选择的 few-shot prompts。当前自动代码生成最成熟的是 SDPT3；LP/MILP prompts 应该要求 agent 先生成经过 review 的模型，并推荐 CVXPY、Pyomo、YALMIP、CVX 或仓库原生路线，然后再考虑可执行 adapter。

使用方式：在 Skill 已安装且可发现之后，把一个完整的 `text` 代码块复制到新的 agent 会话中。

## Prompt 0：提取 LP/MILP Example Map

```text
使用 $optimization-skill。

我想把经典 LP/MILP 运筹优化 examples 用作这个 Skill 的问题陈述。请把 problem map 提取成三组：

1. 适合 CVXPY 或直接 LP solver 的线性规划 examples
2. 适合 Pyomo 或 YALMIP 的混合整数规划 examples
3. 应该保留已有代码的 repository-native examples

对每个 example，请报告：
- 问题标题；
- 变量和变量域；
- 目标函数类型；
- 核心约束；
- 推荐的建模层或 solver 路线；
- 当前是否已有自动代码生成，还是应该停在经过 review 的 modeling checkpoint。

不要安装包，也不要运行代码。最后推荐我应该最先作为 few-shot tests 使用的两个 examples，并说明原因。
```

## Prompt 1：Transportation Linear Program

```text
使用 $optimization-skill。

请建模一个运输线性规划。

问题：
有 m 个仓库和 n 个客户。仓库 i 有 supply[i]。客户 j 有 demand[j]。从 i 运一单位到 j 的成本是 cost[i,j]。决策变量 x[i,j] >= 0 表示运输量。目标是在满足仓库供给和客户需求的情况下，最小化总运输成本。

要求：
- 先写出数学模型。
- 识别变量、目标函数、约束、维度和数据。
- 生成一个 schema-compatible 的 problem.yaml draft。
- 推荐 CVXPY 或 repository-native LP 路线，但不要声称当前已经有自动 LP codegen，除非 Skill 实际支持。
- 生成或运行代码前，先请我确认模型。
```

## Prompt 2：Assignment MILP

```text
使用 $optimization-skill。

请建模一个二元指派问题。

问题：
有 n 个工人和 n 个任务。每个工人必须分配到恰好一个任务，每个任务也必须由恰好一个工人完成。二元变量 x[i,j] 为 1 表示工人 i 被分配到任务 j。指派成本是 cost[i,j]。目标是最小化总成本。

要求：
- 用 binary variables 写出 MILP 模型。
- 判断它可以作为 classic assignment problem 求解，还是作为 generic MILP 求解。
- 生成一个 schema-compatible 的 problem.yaml draft。
- 推荐 Pyomo、YALMIP 或 repository-native solver route。
- 在我批准模型和执行计划之前，不要运行代码。
```

## Prompt 3：Set Cover MILP

```text
使用 $optimization-skill。

请建模一个 weighted set cover 问题。

问题：
有一个必须覆盖的 universe U，以及一组候选集合 S_k。选择集合 k 的成本是 c[k]。二元变量 y[k] 为 1 表示选择集合 k。每个元素必须至少被一个被选择的集合覆盖。目标是最小化总选择成本。

要求：
- 写出 MILP 模型。
- 把 coverage matrix 明确为数据 a[e,k] in {0,1}。
- 生成一个 schema-compatible 的 problem.yaml draft。
- 推荐 Pyomo 或 YALMIP 路线，并列出可用时的候选 MILP solvers，例如 HiGHS、GLPK、CBC、Gurobi 或 SCIP。
- 未经批准，不要安装依赖或运行代码。
```

## Prompt 4：Capacitated Facility Location MILP

```text
使用 $optimization-skill。

请建模一个 capacitated facility location 问题。

问题：
候选设施 f 有固定开设成本 fixed_cost[f] 和容量 capacity[f]。客户 c 有需求 demand[c]。从设施 f 服务客户 c 的单位运输成本是 ship_cost[f,c]。二元变量 y[f] 表示是否开设设施。连续变量 x[f,c] 表示从设施 f 给客户 c 的供货量。目标是最小化固定开设成本和运输成本之和。

要求：
- 写出包含 binary facility decisions 和 continuous shipment variables 的 MILP。
- 包含 demand satisfaction、capacity 和 linking constraints。
- 生成一个 schema-compatible 的 problem.yaml draft。
- 推荐 Pyomo 或 repository-native MILP 路线。
- 识别数值或建模风险，例如 big-M/linking constraints 和缺失的 capacity data。
```

## Prompt 5：Minimum-Cost Network Flow LP

```text
使用 $optimization-skill。

请建模一个 minimum-cost network flow 问题。

问题：
给定有向图 G=(V,E)，每条弧 (i,j) 有单位成本 c[i,j] 和容量 u[i,j]。每个节点 v 有 balance b[v]，正数表示供给，负数表示需求。选择 flow x[i,j]，在满足流量平衡和弧容量的情况下，最小化总成本。

要求：
- 写出 LP 模型。
- 澄清 node balance 的符号约定。
- 生成一个 schema-compatible 的 problem.yaml draft。
- 根据可用数据推荐 CVXPY、scipy/HiGHS 或 repository-native 路线。
- 在模型确认前，不要生成可执行代码。
```

## Prompt 6：Single-Machine Scheduling MILP

```text
使用 $optimization-skill。

请建模一个小规模 single-machine scheduling MILP。

问题：
有作业集合 J。每个作业 j 有 processing time p[j] 和 due date d[j]。需要在一台机器上安排所有作业，不能重叠。目标是最小化 total tardiness。使用 binary precedence variables y[i,j] 和 completion time variables C[j]。

要求：
- 写出 MILP 模型，并解释 big-M constraints。
- 识别安全 M 值需要哪些数据。
- 生成一个 schema-compatible 的 problem.yaml draft。
- 推荐 Pyomo 或 YALMIP 路线。
- 如果无法证明 big-M 值合理，就停在 modeling checkpoint。
```

## Prompt 7：Natural-Language To LP/MILP Spec Stress Prompt

```text
使用 $optimization-skill。

我会用自然语言描述一个运筹优化问题。请把它转换成经过 review 的 LP/MILP modeling checkpoint 和 schema-compatible 的 problem.yaml draft。不要运行代码。

问题：
一家公司要选择资助哪些项目。项目 k 有利润 p[k]、预算成本 b[k]，并占用工程工时 h[k]。有些项目依赖其他项目：如果选择项目 4，就必须同时选择项目 1。总预算和工程工时有限。目标是选择项目，使总利润最大。

要求：
- 推断 binary decision variables。
- 写出目标函数和约束。
- 包含 dependency constraints。
- 推荐 Pyomo 或 MILP 路线。
- 列出歧义点，并在任何代码生成前请我确认。
```
