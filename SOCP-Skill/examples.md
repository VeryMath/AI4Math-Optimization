# SOCP 参考示例

<!--
  作者：李爽夕
  Benchmark 数据来源：CBLIB 2014 (Conic Benchmark Library)
  URL: https://cblib.zib.de/
  引用：Friberg, H.A. (2016). Mathematical Programming Computation, 8(2), 191-214.
  DOI: 10.1007/s12532-015-0092-4
  Copyright (c) 2012, Zuse Institute Berlin and the Technical University of Denmark.
  可自由使用，须保留版权声明，不得虚假声称原创。
-->

> 模型：deepseek-v4-pro

---

## 示例 1：基本 SOCP 问题

### 数学模型

```
min  x1 + 2x2 + 3x3
s.t. ||[x1, x2]||_2 <= x3 + 1
     x1 + x2 + x3 <= 10
     x1, x2, x3 >= 0
```

### cvxpy 建模

```python
import numpy as np
import cvxpy as cvx

x = cvx.Variable(3)
objective = cvx.Minimize(x[0] + 2*x[1] + 3*x[2])
constraints = [
    cvx.SOC(x[2] + 1, x[:2]),       # ||[x1, x2]|| <= x3 + 1
    x[0] + x[1] + x[2] <= 10,
    x >= 0,
]
prob = cvx.Problem(objective, constraints)
prob.solve(solver=cvx.COPT)
print(prob.status, prob.value, x.value)
```

---

## 示例 2：投资组合优化（最小化风险）

### 问题描述

有 3 种资产，预期收益率向量 `mu = [0.08, 0.10, 0.12]`，协方差矩阵：

```
Sigma = [[0.01, 0.002, 0.001],
         [0.002, 0.02, 0.003],
         [0.001, 0.003, 0.03]]
```

目标：在目标收益率不低于 9% 的条件下最小化风险（标准差）。满仓操作（权重和 = 1），不允许卖空。

### 符号化

- **变量**：`w_i` = 资产 i 的权重，i = 1,2,3；`t` = 风险（标准差）
- **目标**：`min t`
- **约束**：
  - `sum(w_i) == 1`（满仓）
  - `w_i >= 0`（不允许卖空）
  - `mu^T w >= 0.09`（收益率约束）
  - `||L^T w||_2 <= t`（锥约束，L 为 Cholesky 因子）

### cvxpy 建模

```python
import numpy as np
import cvxpy as cvx

mu = np.array([0.08, 0.10, 0.12])
Sigma = np.array([[0.01, 0.002, 0.001],
                  [0.002, 0.02, 0.003],
                  [0.001, 0.003, 0.03]])
L = np.linalg.cholesky(Sigma)

w = cvx.Variable(3)
t = cvx.Variable()

objective = cvx.Minimize(t)
constraints = [
    cvx.SOC(t, L.T @ w),    # ||L^T w||_2 <= t
    cvx.sum(w) == 1,
    w >= 0,
    mu @ w >= 0.09,
]

prob = cvx.Problem(objective, constraints)
prob.solve(solver=cvx.COPT)
print(f"status: {prob.status}, risk: {prob.value:.4f}")
print(f"weights: {w.value}")
```

---

## 示例 3：最大化夏普比率（Sharpe Ratio）

### 问题描述

夏普比率的定义是 `(mu^T w - r_f) / sqrt(w^T Sigma w)`。最大化夏普比率可以转化为 SOCP（通过引入辅助变量）。

```
max  (mu^T w - r_f) / sqrt(w^T Sigma w)
s.t. sum(w) == 1,  w >= 0
```

### 转化方法

最大化夏普比率等价于求解以下 SOCP：

```
min  t
s.t. ||L^T w||_2 <= t
     mu^T w - r_f = 1
     sum(w) == kappa,  w >= 0
```

更简洁的方式是用二分法搜索。

### cvxpy 建模（二分法）

```python
import numpy as np
import cvxpy as cvx

mu = np.array([0.08, 0.10, 0.12])
Sigma = np.array([[0.01, 0.002, 0.001],
                  [0.002, 0.02, 0.003],
                  [0.001, 0.003, 0.03]])
L = np.linalg.cholesky(Sigma)
rf = 0.03  # 无风险利率

# 二分法搜索最大夏普比率
lo, hi = 0.0, 3.0
for _ in range(20):
    gamma = (lo + hi) / 2  # 当前尝试的夏普比率
    w = cvx.Variable(3)
    objective = cvx.Minimize(cvx.norm(L.T @ w))
    constraints = [
        cvx.sum(w) == 1,
        w >= 0,
        mu @ w - rf >= gamma * cvx.norm(L.T @ w),
    ]
    prob = cvx.Problem(objective, constraints)
    prob.solve(solver=cvx.ECOS)
    if prob.status == "optimal":
        lo = gamma  # 可行，尝试更大值
    else:
        hi = gamma  # 不可行，尝试更小值

optimal_sharpe = (lo + hi) / 2
print(f"最大夏普比率: {optimal_sharpe:.4f}")
```

---

## 示例 4：鲁棒线性规划

### 问题描述

考虑带有不确定性的线性约束：

```
min  c^T x
s.t. (a_i + Delta_i)^T x <= b_i  对所有 ||Delta_i||_2 <= rho_i 成立
     x >= 0
```

其中系数 `a_i` 在一个半径为 `rho_i` 的球内变化。worst-case 等价于：

```
a_i^T x + rho_i * ||x||_2 <= b_i
```

### 具体数值

```
min  x1 + 2x2 + 3x3
s.t. x1 + x2 + x3 + 0.5 * ||x||_2 <= 10
     2x1 + x2 + 0.3 * ||x||_2 <= 8
     x1, x2, x3 >= 0
```

### cvxpy 建模

```python
import numpy as np
import cvxpy as cvx

x = cvx.Variable(3)
c = np.array([1, 2, 3])

objective = cvx.Minimize(c @ x)
t = cvx.Variable()

constraints = [
    cvx.SOC(t, x),                           # ||x||_2 <= t
    np.array([1, 1, 1]) @ x + 0.5 * t <= 10, # 约束1 鲁棒版本
    np.array([2, 1, 0]) @ x + 0.3 * t <= 8,  # 约束2 鲁棒版本
    x >= 0,
]

prob = cvx.Problem(objective, constraints)
prob.solve(solver=cvx.COPT)
print(f"status: {prob.status}, obj: {prob.value:.4f}")
print(f"x: {x.value}")
```

---

## 示例 5：含多个锥约束

### 数学模型

```
min  2x1 + x2
s.t. ||[x1 - 1, x2 - 2]||_2 <= 3
     ||[x1 + 1, x2 - 1]||_2 <= 2
     x1 + 2x2 >= 5
     x1, x2 >= 0
```

### cvxpy 建模

```python
import numpy as np
import cvxpy as cvx

x = cvx.Variable(2)
objective = cvx.Minimize(2*x[0] + x[1])
constraints = [
    cvx.SOC(3, cvx.vstack([x[0] - 1, x[1] - 2])),
    cvx.SOC(2, cvx.vstack([x[0] + 1, x[1] - 1])),
    x[0] + 2*x[1] >= 5,
    x >= 0,
]
prob = cvx.Problem(objective, constraints)
prob.solve(solver=cvx.COPT)
print(f"status: {prob.status}, obj: {prob.value:.4f}")
print(f"x: {x.value}")
```

---

## 示例 6：带概率约束的投资组合

### 问题描述

最大化预期收益，同时要求收益低于某阈值的概率不超过 beta：

```
max  mu^T w
s.t. Prob(r^T w <= alpha) <= beta
     sum(w) == 1,  w >= 0
```

当收益 r 服从 N(mu, Sigma) 时，概率约束等价于：

```
mu^T w + Phi^{-1}(beta) * sqrt(w^T Sigma w) >= alpha
```

其中 beta <= 0.5 时 Phi^{-1}(beta) 为负值，对应锥约束：

```
mu^T w + Phi^{-1}(beta) * t >= alpha
||L^T w||_2 <= t
```

### 具体数值

```python
import numpy as np
import cvxpy as cvx
from scipy.stats import norm

mu = np.array([0.08, 0.10, 0.12])
Sigma = np.array([[0.01, 0.002, 0.001],
                  [0.002, 0.02, 0.003],
                  [0.001, 0.003, 0.03]])
L = np.linalg.cholesky(Sigma)

alpha = 0.0      # 收益不低于 0%（不亏损）
beta = 0.05      # 95% 置信度
phi_inv = norm.ppf(beta)  # 约 -1.645

w = cvx.Variable(3)
t = cvx.Variable()
ret = mu @ w

objective = cvx.Maximize(ret)
constraints = [
    cvx.SOC(t, L.T @ w),
    ret + phi_inv * t >= alpha,  # 概率约束
    cvx.sum(w) == 1,
    w >= 0,
]

prob = cvx.Problem(objective, constraints)
prob.solve(solver=cvx.COPT)
print(f"status: {prob.status}")
print(f"max return: {prob.value:.4f}")
print(f"weights: {w.value}")
print(f"risk (std): {t.value:.4f}")
```

---

## 示例 7：Group Lasso 回归（统计学习）

### 问题描述

Group Lasso 将特征分为若干组，对每组系数整体做 L2 正则化：

```
min  0.5 * ||y - X beta||_2^2 + lambda * sum_g w_g * ||beta_g||_2
```

### SOCP 转化

引入辅助变量 t_g，将问题转为 SOCP：

```
min  t0 + lambda * sum_g w_g * t_g
s.t. ||y - X beta||_2 <= t0
     ||beta_g||_2 <= t_g,  for each group g
```

### 代码实现

```python
import numpy as np
import cvxpy as cvx

# 生成数据
np.random.seed(42)
n, p = 30, 10
X = np.random.randn(n, p)
true_beta = np.array([3, 0, 0, 0, -2, 0, 0, 1.5, 0, 0])
y = X @ true_beta + 0.5 * np.random.randn(n)

# 定义分组：5组，每组2个变量
groups = [[0, 1], [2, 3], [4, 5], [6, 7], [8, 9]]
group_weights = [np.sqrt(len(g)) for g in groups]
lam = 0.5  # 正则化参数

beta = cvx.Variable(p)
t0 = cvx.Variable()
t = cvx.Variable(len(groups))

objective = cvx.Minimize(t0 + lam * cvx.sum(
    [group_weights[i] * t[i] for i in range(len(groups))]
))

constraints = [cvx.SOC(t0, y - X @ beta)]  # 残差锥
for i, g in enumerate(groups):
    constraints.append(cvx.SOC(t[i], beta[g]))  # 每组系数锥

prob = cvx.Problem(objective, constraints)
prob.solve(solver=cvx.ECOS)

print(f"status: {prob.status}")
print(f"beta: {beta.value.round(3)}")
print(f"非零组: {[i for i, g in enumerate(groups) if np.linalg.norm(beta.value[g]) > 1e-4]}")
```

---

## 示例 8：最小化最差情况风险（Worst-case Risk）

### 问题描述

当协方差矩阵本身不确定时（只知道在一个椭球内），最小化最差情况下的组合风险：

```
min  max_{Sigma in U}  w^T Sigma w
s.t. sum(w) == 1,  w >= 0
```

设协方差矩阵的估计值为 `Sigma_0`，不确定半径为 `delta`，则 worst-case 风险有解析形式：

```
w^T Sigma_0 w + delta * ||w||_2^2
```

### 代码实现

```python
import numpy as np
import cvxpy as cvx

mu = np.array([0.08, 0.10, 0.12])
Sigma_0 = np.array([[0.01, 0.002, 0.001],
                    [0.002, 0.02, 0.003],
                    [0.001, 0.003, 0.03]])
delta = 0.005  # 不确定性半径

w = cvx.Variable(3)

L = np.linalg.cholesky(Sigma_0)
t = cvx.Variable()

augmented_matrix = cvx.vstack([L.T @ w, np.sqrt(delta) * w])

objective = cvx.Minimize(t)
constraints = [
    cvx.SOC(t, augmented_matrix),
    mu @ w >= 0.09,
    cvx.sum(w) == 1,
    w >= 0,
]

prob = cvx.Problem(objective, constraints)
prob.solve(solver=cvx.COPT)
print(f"status: {prob.status}")
print(f"worst-case risk: {prob.value:.4f}")
print(f"weights: {w.value}")
```

---

## 示例 9：天线阵列校准 — CBLIB nb_L2

> **数据来源**：CBLIB 2014, "nb" pack, instance `nb_L2`.
> 引用：Friberg, H.A. (2016). Mathematical Programming Computation, 8(2), 191-214.
> 原始研究：Coleman, J.O. & Vanderbei, R.J. (1999). "Random-process formulation
> of computationally efficient performance measures for wideband arrays."

### 问题描述

天线阵列校准问题：在抑制非目标方向信号的同时，保持目标方向增益。等价于带 L2 正则化的范数最小化 SOCP：

```
min  t
s.t. ||A x - b||_2 <= t      (拟合误差锥)
     ||x||_2 <= M              (L2 正则化锥)
     （线性约束，如相位/增益界）
```

CBLIB 中 `nb_L2` 为连续 SOCP：变量数~4195，锥约束~2797。

### 简化示例代码（小规模演示）

```python
import numpy as np
import cvxpy as cvx

# 模拟天线阵列：m 个方向，n 个阵元
np.random.seed(42)
m, n = 50, 10
A = np.random.randn(m, n)
x_true = np.random.randn(n) * 0.5
b = A @ x_true + np.random.randn(m) * 0.1
M_reg = 3.0  # 正则化参数

x = cvx.Variable(n)
t = cvx.Variable(1)
objective = cvx.Minimize(t)
constraints = [
    cvx.SOC(t, A @ x - b),          # ||Ax - b||_2 <= t
    cvx.SOC(M_reg, x),               # ||x||_2 <= M
]

prob = cvx.Problem(objective, constraints)
prob.solve(solver=cvx.ECOS)

print(f"status: {prob.status}")
print(f"fit error ||Ax-b||_2 = {t.value[0]:.6f}")
print(f"regularization ||x||_2 = {np.linalg.norm(x.value):.4f} <= {M_reg}")
```

---

## 示例 10：塑性极限分析 — CBLIB qssp30

> **数据来源**：CBLIB 2014, "strain" pack, instance `qssp30`.
> 引用：Friberg, H.A. (2016). Mathematical Programming Computation, 8(2), 191-214.
> 原始研究：Andersen, K.D., Christiansen, E. & Overton, M.L. (1998).
> "Computing Limit Loads by Minimizing a Sum of Norms." SIAM J. Sci. Comput., 19(3).

### 问题描述

塑性极限分析用于确定结构在塑性屈服前的最大承载能力。数学模型为 SOCP：

```
min  -lambda
s.t. B^T sigma = lambda * f        (平衡方程)
     ||D_e sigma||_2 <= sigma_y    (屈服约束，每个单元 e 一个锥)
     （边界条件）
```

CBLIB 中 `qssp30` 为连续 SOCP：变量数~349，锥约束~120。

### 简化示例代码

```python
import numpy as np
import cvxpy as cvx

# 构造一个小规模极限分析问题（6 应力变量，3 单元）
np.random.seed(77)
ns, ne = 6, 3
B = np.random.randn(ns, ne) * 0.5        # 平衡矩阵 (ns x ne)
f_load = np.ones(ne)                       # 参考载荷
D_list = [np.random.randn(2, ns) * 0.3 for _ in range(ne)]
sigma_y = 1.0

sigma = cvx.Variable(ns)
lam = cvx.Variable(1)

objective = cvx.Minimize(-lam)
constraints = [
    B.T @ sigma == lam * f_load,           # 平衡方程
]
for D_e in D_list:
    constraints.append(cvx.SOC(sigma_y, D_e @ sigma))

prob = cvx.Problem(objective, constraints)
prob.solve(solver=cvx.ECOS)

print(f"status: {prob.status}")
print(f"collapse multiplier lambda* = {lam.value[0]:.6f}")
print(f"stress: {sigma.value}")

# 验证屈服约束
for i, D_e in enumerate(D_list):
    stress_norm = np.linalg.norm(D_e @ sigma.value)
    print(f"  element {i}: ||D_{i}*sigma|| = {stress_norm:.6f} <= {sigma_y}")
```

---

## CBLIB 基准问题映射表

以下 CBLIB 2014 问题包均可通过本 Skill 的 cvxpy 工作流求解：

| CBLIB Pack | 描述 | 问题类型 | 典型规模 |
|------------|------|----------|----------|
| `nb`, `nb_L2` | 天线阵列校准 | 范数最小化 SOCP | ~4200 变量 |
| `qssp30`, `nql30` | 塑性极限分析 | 平衡+屈服锥 SOCP | ~350 变量 |
| `filterdesign` | FIR 滤波器优化设计 | 多锥 L1/L2 混合 | ~1000 变量 |
| `chainsing` | Chained Singular 函数 | 学术测试函数 | ~1000-50000 变量 |
| `portfoliocard` | 投资组合 + 基数约束 | MISOCP | ~200 变量 |
| `sched` | 并行机调度 | SOCP 松弛 | ~5000 变量 |

---

## 锥约束转化参考表

| 数学形式 | SOCP 等价形式 | 应用场景 |
|----------|--------------|----------|
| `||x||_2 <= t` | `(x, t) in Q` (标准锥) | 基本锥约束 |
| `x^T Q x <= t^2`, Q >= 0 | `||L^T x||_2 <= t` (L = Cholesky(Q)) | 投资组合风险 |
| `x^2 <= y z`, y,z >= 0 | `||[2x, y-z]||_2 <= y+z` (旋转锥) | 双曲约束 |
| `t >= 1/x`, x >= 0 | `||[sqrt(2), x-t]||_2 <= x+t` | 倒数约束 |
| `sqrt(x1 * x2 * ... * xk)` | 多个旋转锥组合 | 几何平均 |
| `||x||_1 <= t` | 多个线性约束（非锥） | L1 正则化 |
| `sum_i ||x_i||_2 <= t` | 多个锥约束之和 | Group Lasso |
| `a^T x + rho*||x||_2 <= b` | 单锥约束 | 鲁棒优化 |

---

## 常见问题与诊断

### 锥约束方向

SOCP 要求 `||A x + b||_2 <= c^T x + d` 的**右端必须是非负的**。如果建模后得到 `infeasible`，检查是否锥方向反了（右端为负）。

### 选择求解器

| 求解器 | 适用场景 | 是否需要授权 |
|--------|----------|-------------|
| COPT | 大规模、商业环境 | 是 |
| ECOS | 中小规模、嵌入式 | 否（开源） |
| SCS | 大规模、低精度需求 | 否（开源） |

### 数值稳定性

- 使用 Cholesky 分解时确保矩阵正定
- 当变量量级差异大时，先做标准化再建模
- 对接近不可行的问题，尝试降低 `FeasibilityTol`
