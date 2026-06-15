<!-- 作者：李爽夕 -->

# 运筹优化求解器统一配置

## 简介

为线性规划 (LP)、混合整数规划 (MIP)、二阶锥规划 (SOCP) 提供**统一的求解器检测、安装、选择与 License 配置**。避免三个 skill 各自维护重复的求解器管理逻辑。

## 覆盖范围

| 问题类型 | 可用求解器数 | 开源首选 | 商业首选 |
|----------|:----------:|----------|----------|
| LP（线性规划） | 13 | HiGHS (MIT) | COPT |
| MIP（混合整数规划） | 12 | SCIP (Apache 2.0) / HiGHS (MIT) | COPT / Gurobi |
| SOCP（二阶锥规划） | 10 | CLARABEL (Apache 2.0) | COPT / MOSEK |

共覆盖 **20 种求解器/接口**，含 4 种商业求解器和 16 种开源求解器。

## 快速开始

### 1. 检测已有求解器

```bash
pip list | grep -iE "coptpy|gurobipy|mosek|cplex|pyscipopt|highspy|clarabel|pulp|mip|ortools|ecos|scs|cvxopt|cosmo|osqp|swiglpk|scipy|lpsolve55|numpy|cvxpy"
```

### 2. 一键安装（按需）

```bash
# 只做 LP
pip install numpy scipy

# LP + MIP
pip install numpy pulp highspy

# LP + MIP + SOCP（全套开源）
pip install numpy scipy pulp highspy cvxpy clarabel ecos scs
```

### 3. 验证

```python
import numpy, scipy
from scipy.optimize import linprog
import cvxpy; print(cvxpy.installed_solvers())
```

## 降级策略（统一优先级）

```
商业: COPT > Gurobi > MOSEK > CPLEX
开源: HiGHS/SCIP/CLARABEL > PuLP/CBC/ECOS > CVXOPT/GLPK/...
最终: GitHub 搜索独立实现
```

## 被引用的 Skill

- `@LP/SKILL.md` — 线性规划
- `@MIP/SKILL.md` — 混合整数规划
- `@SOCP/SKILL.md` — 二阶锥规划

## 示例

详见 [examples.md](examples.md)，含检测输出示例和安装场景示例。
