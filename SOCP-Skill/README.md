<!-- 作者：李爽夕 -->

# 二阶锥规划 (SOCP) 求解

## 简介

求解**二阶锥规划及其可转化为 SOCP 的问题**。

$$
\min \; c^T x \quad \text{s.t.} \quad \|A_i x + b_i\|_2 \leq d_i^T x + e_i
$$

## 适用场景

- 投资组合优化（最小化风险 / 最大化夏普比率）
- 鲁棒优化（参数不确定下的稳健决策）
- 天线阵列校准、塑性极限分析、FIR 滤波器设计
- Group Lasso 回归（统计学习转 SOCP）
- 概率约束规划（正态分布假设下转 SOCP）

## 快速开始

直接向 AI 用自然语言描述问题，例如：

> "有 3 种资产，预期收益率 8%、10%、12%。在目标收益 ≥ 9% 下最小化风险，不允许卖空。"

也可以给矩阵或 JSON。

## 环境

```bash
pip install numpy cvxpy          # 必装
pip install clarabel              # 推荐开源求解器
```

支持 **10 种求解器**：COPT、Gurobi、MOSEK、CPLEX、CLARABEL、ECOS、SCS、CVXOPT、COSMO、OSQP。无任何求解器时自动从 GitHub 搜索开源代码。

## 输出格式

AI 回答包含：**环境与依赖**（求解器选择及原因）→ **问题重述** → **符号化模型**（变量/目标/约束） → **求解结果**（状态/最优值/变量值） → **约束验证** → **结果解释**

## 示例

详见 [examples.md](examples.md)，含 10 个完整示例（投资组合、鲁棒优化、CBLIB 基准等）。

## 基准测试

基于纯学术测试集（100 个问题），对本 skill 进行验证：

| 问题类型 | 数量 | 学术来源 | 引用 |
|---------|:--:|------|------|
| 投资组合优化 | 35 | CBLIB 2014 / Markowitz | Friberg (2016) |
| 可行 SOCP | 50 | CBLIB 2014 锥约束实例 | Friberg (2016) |
| 鲁棒优化 | 15 | Ben-Tal & Nemirovski 椭球不确定集 | Ben-Tal & Nemirovski (1999) |

| 指标 | 数值 |
|------|------|
| 测试集 | CBLIB 2014 (Friberg 2016) + Ben-Tal & Nemirovski (1999) |
| 问题数 | 100 |
| 通过率 | **100.0%** (100/100) |
| 平均求解时间 | 0.005 s |
| 求解器 | COPT（经环境检测 → 优先级选择自动选定） |

![SOCP Benchmark](../tests/results/socp_academic_summary.png)

### Direct vs Skill 求解对比

同一测试集（100 个学术 SOCP 问题）上，对比**直接调用求解器 API** 和 **经由 skill 工作流求解**：

| 指标 | 直接求解 | Skill 求解 |
|------|---------|-----------|
| 通过率 | 100.0% (100/100) | 100.0% (100/100) |
| 平均求解时间 | 0.005 s | 0.005 s |
| 目标值一致性 | — | 100.0% |
| 时间比 (skill/direct) | — | 1.00x |
| Skill 额外开销 | — | ~0 s（同一求解器，无额外开销） |
| 选用求解器 | COPT | COPT（经环境检测 → 优先级选择） |

![SOCP Comparison](../tests/results/comparison_socp_academic.png)

> Skill 工作流（环境检测 → 求解器选择 → 建模 → 求解 → 锥约束验证）与 direct 通过率完全一致，开销在测量噪声范围内。

### 学术引用

- **SOCP**: Friberg, H.A. (2016). CBLIB 2014: a benchmark library for conic mixed-integer and continuous optimization. *Mathematical Programming Computation*, 8, 191-214.
- **Portfolio**: Markowitz, H. (1952). Portfolio selection. *The Journal of Finance*, 7(1), 77-91.
- **Robust Optimization**: Ben-Tal, A. & Nemirovski, A. (1999). Robust solutions of uncertain linear programs. *Mathematics of Operations Research*, 24(4).

## 边界

- 能求解：连续 SOCP
- 不能：MISOCP、SDP、非凸问题

## 数据引用

SOCP 标准学术测试集基于经典问题公式（投资组合优化、鲁棒优化、锥约束可行问题），以固定随机种子生成确保可复现。
