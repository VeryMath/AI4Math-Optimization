<!-- 作者：李爽夕 -->

# 混合整数规划 (MIP) 求解

## 简介

求解**混合整数线性规划 (MILP)** 及可线性化转化的整数规划问题：线性目标 + 线性约束 + 部分/全部变量为整数。

$$
\min \; c^T x \quad \text{s.t.} \quad Ax \leq b,\; x_j \in \mathbb{Z} \text{ 或 } \{0,1\} \text{ 或 } \mathbb{R}
$$

## 适用场景

- 背包问题、指派问题、旅行商问题（TSP）
- 选址问题（设施选址、覆盖选址、P-中位）
- 生产排产与调度（多期生产、机器调度、换产时间）
- 车辆路径规划（VRP）
- 投资组合优化（含交易手数、最小交易量）
- 网络设计、固定费用问题
- 逻辑约束建模（Big-M、indicator、SOS1/SOS2）
- 混合整数扩展：MIQP、MISOCP

## 快速开始

直接向 AI 用自然语言描述问题，例如：

> "3 个备选仓库，覆盖 5 个城市。建仓固定成本 100/120/150，每个仓库最多服务 2 个城市。求最小成本选址方案。"

也可以给矩阵或 JSON。

## 环境

```bash
pip install numpy pulp               # 必装（PuLP 含 CBC 求解器）
pip install highspy                   # 推荐（HiGHS，MIT 开源）
pip install pyscipopt                 # 最强开源 MIP（SCIP）
```

支持 **12 种求解器**：COPT、Gurobi、CPLEX、MOSEK、SCIP/pyscipopt、HiGHS/highspy、PuLP/CBC、python-mip、OR-Tools/SCIP、OR-Tools/CP-SAT、GLPK、lpsolve。无任何求解器时自动从 GitHub 搜索开源代码。

## 输出格式

AI 回答包含：**环境与依赖**（求解器选择及原因）→ **问题重述** → **符号化模型**（变量/目标/约束，标注整数类型） → **数值化（可选）** → **求解结果**（状态/最优值/变量值/MIP gap/求解时间） → **约束验证** → **结果解释**

## 示例

详见 [examples.md](examples.md)，含 8 个完整示例（背包、选址、指派、排产、TSP、逻辑约束、投资组合、矩阵 JSON）。

## 基准测试

基于纯学术测试集（100 个问题），对本 skill 进行验证：

| 问题类型 | 数量 | 学术来源 | 引用 |
|---------|:--:|------|------|
| TSP | 10 | TSPLIB 风格实例 (MIP 验证最优值) | Reinelt (1991) |
| 背包问题 | 30 | Pisinger 标准生成器 | Pisinger (2005) |
| 指派问题 | 20 | OR-Library | Martello & Toth (1990) |
| 设施选址 | 20 | Beasley OR-Library | Beasley (1990) |
| 排产调度 | 20 | OR-Library 单机加权延迟 | Beasley (1990) |

| 指标 | 数值 |
|------|------|
| 测试集 | TSP-style + Pisinger (2005) + Beasley (1990) OR-Library |
| 问题数 | 100 |
| 通过率 | **100.0%** (100/100) |
| 平均求解时间 | 1.26 s |
| 求解器 | COPT（经环境检测 → 优先级选择自动选定） |

![MIP Benchmark](../tests/results/mip_academic_summary.png)

### Direct vs Skill 求解对比

同一测试集（100 个学术 MIP 问题）上，对比**直接调用求解器 API** 和 **经由 skill 工作流求解**：

| 指标 | 直接求解 | Skill 求解 |
|------|---------|-----------|
| 通过率 | 100.0% (100/100) | 100.0% (100/100) |
| 平均求解时间 | 1.26 s | 1.26 s |
| 目标值一致性 | — | 100.0% |
| 时间比 (skill/direct) | — | 1.00x |
| Skill 额外开销 | — | ~0 s（同一求解器，无额外开销） |
| 选用求解器 | COPT | COPT（经环境检测 → 优先级选择） |

![MIP Comparison](../tests/results/comparison_mip_academic.png)

> Skill 工作流（环境检测 → 求解器选择 → 建模（含 vtype 标注）→ 求解 → 整数容差验证）通过率与 direct 完全一致。

### 学术引用

- **TSP**: Reinelt, G. (1991). TSPLIB — A Traveling Salesman Problem Library. *ORSA Journal on Computing*, 3(4), 376-384.
- **Knapsack**: Pisinger, D. (2005). Where are the hard knapsack problems? *Computers & Operations Research*, 32(9), 2271-2284.
- **Assignment**: Martello, S. & Toth, P. (1990). *Knapsack Problems: Algorithms and Computer Implementations*. Wiley.
- **Facility Location & Scheduling**: Beasley, J.E. (1990). OR-Library: Distributing test problems by electronic mail. *Journal of the Operational Research Society*, 41(11), 1069-1072.

## 边界

- 能求解：MILP、可通过线性化转化的整数规划（分段线性、逻辑约束、SOS1/SOS2）
- 能求解（商业求解器）：MIQP、MISOCP
- 不能：非线性整数规划（MINLP，除非可完全线性化）、纯约束规划（如 `alldifferent` 全局约束）

