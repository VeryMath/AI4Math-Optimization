<!-- 作者：李爽夕 -->

# 线性规划 (LP) 求解

## 简介

求解**线性规划 (Linear Program)**：线性目标 + 线性约束。



## 适用场景

- 生产计划、资源分配
- 运输调度、最低运费
- 配方混合、最低成本
- 网络流、任何线性决策问题

## 快速开始

直接向 AI 用自然语言描述问题，例如：

> "工厂生产 A、B。A 利润 3/件，B 利润 5/件。原料 ≤ 100，工时 ≤ 120。求最大利润。"

也可以给矩阵 JSON 格式。

## 环境

```bash
pip install numpy scipy            # 必装（scipy 内置 HiGHS 求解器）
```

支持 **13 种求解器**：COPT、Gurobi、MOSEK、CPLEX、HiGHS (scipy/highspy)、CLARABEL、OR-Tools/GLOP、PuLP/CBC、ECOS、CVXOPT、GLPK、SoPlex、lpsolve。无任何求解器时自动从 GitHub 搜索开源代码。

## 输出格式

AI 回答包含：**环境与依赖**（求解器选择及原因）→ **问题重述** → **符号化模型**（变量/目标/约束） → **求解结果**（状态/最优值/变量值） → **约束验证** → **结果解释**

## 示例

详见 [examples.md](examples.md)，含 6 个示例（生产、运输、配方、产销计划 + 矩阵 JSON）。

## 基准测试

基于 **NETLIB LP** 标准学术测试集（92 个问题：via scipy benchmarks），对本 skill 进行验证。

| 指标 | 数值 |
|------|------|
| 测试集 | [NETLIB LP](http://www.netlib.org/lp/) (via [scipy benchmarks](https://github.com/scipy/scipy/tree/main/benchmarks/benchmarks/linprog_benchmark_files)) |
| 问题数 | 92 |
| 通过率 | **100.0%** (92/92) |
| 平均求解时间 | 9.40 s |
| 求解器 | COPT（经环境检测 → 优先级选择自动选定） |

![LP Benchmark](../tests/results/lp_netlib_summary.png)

### Direct vs Skill 求解对比

同一测试集（92 个 NETLIB LP 问题）上，对比**直接调用求解器 API** 和 **经由 skill 工作流求解**：

| 指标 | 直接求解 | Skill 求解 |
|------|---------|-----------|
| 通过率 | 100.0% (92/92) | 100.0% (92/92) |
| 平均求解时间 | 9.40 s | 9.40 s |
| 目标值一致性 | — | 100.0% |
| 时间比 (skill/direct) | — | 1.00x |
| Skill 额外开销 | — | ~0 s（同一求解器，无额外开销） |
| 选用求解器 | COPT | COPT（经环境检测 → 优先级选择） |

![LP Comparison](../tests/results/comparison_lp_netlib.png)

> Skill 工作流（环境检测 → 求解器选择 → 建模 → 求解 → 约束验证）未引入可测量的额外开销，通过率和目标值与直接调用完全一致。

## 边界

- 能求解：连续变量 LP
- 不能：整数规划 (MILP)、非线性目标/约束
