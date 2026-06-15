# 求解器配置参考示例

<!-- 作者：李爽夕 -->

> 模型：deepseek-v4-pro

---

## 示例 1：完整的环境检测输出

### 场景

用户首次使用 LP/MIP/SOCP skill，需要检测本地已安装哪些求解器。

### 检测命令

```bash
pip list | grep -iE "coptpy|gurobipy|mosek|cplex|pyscipopt|highspy|clarabel|pulp|mip|ortools|ecos|scs|cvxopt|cosmo|osqp|swiglpk|scipy|lpsolve55|numpy|cvxpy"
```

### 典型输出（示例）

```
clarabel           0.9.0
cvxpy              1.6.4
ecos               2.0.14
highspy            1.7.2
numpy              2.2.6
ortools            9.14.15197
osqp               1.0.4
pulp               2.9.0
pyscipopt          5.4.1
scipy              1.15.3
```

### 解读

```python
# 已安装 = 10 个包，覆盖 11 种求解器
installed = {
    "numpy":     "2.2.6",    # 基础数值计算
    "scipy":     "1.15.3",   # 含 HiGHS（LP only）
    "highspy":   "1.7.2",    # HiGHS（LP + MIP）
    "pulp":      "2.9.0",    # PuLP + CBC（LP + MIP）
    "pyscipopt": "5.4.1",    # SCIP（MIP 最强开源）
    "ortools":   "9.14.15",  # GLOP + SCIP + CP-SAT
    "cvxpy":     "1.6.4",    # SOCP/LP 建模接口
    "clarabel":  "0.9.0",    # SOCP 开源首选
    "ecos":      "2.0.14",   # SOCP 开源备选
    "osqp":      "1.0.4",    # QP（仅 QP 可转化的 SOCP）
}

# 缺失的商业求解器
missing_commercial = ["coptpy", "gurobipy", "mosek", "cplex"]

# 缺失的开源求解器
missing_open = ["mip", "scs", "cvxopt", "cosmo", "swiglpk", "lpsolve55"]

# 按问题类型汇总可用求解器
lp_solvers   = ["HiGHS (scipy/highspy)", "PuLP/CBC",
                "OR-Tools/GLOP", "CLARABEL", "ECOS", "OSQP"]
mip_solvers  = ["SCIP/pyscipopt", "HiGHS/highspy", "PuLP/CBC",
                "OR-Tools/SCIP", "OR-Tools/CP-SAT"]
socp_solvers = ["CLARABEL", "ECOS", "OSQP"]

# 推荐选择
lp_recommend   = "HiGHS (开源 MIT, LP 首选)"
mip_recommend  = "SCIP/pyscipopt (开源 Apache 2.0, MIP 最强开源)"
socp_recommend = "CLARABEL (开源 Apache 2.0, SOCP 首选)"
```

---

## 示例 2：从零安装——只做 LP

### 场景

用户只解线性规划，不需要整数变量和锥约束。

### 操作

```bash
# Step 1：检测（预期为空或只有 numpy）
pip list | grep -iE "scipy|highspy|pulp|cvxpy|coptpy|gurobipy"

# Step 2：安装最小依赖
pip install numpy scipy

# Step 3：验证
python -c "
import numpy; import scipy
from scipy.optimize import linprog
print(f'numpy={numpy.__version__}, scipy={scipy.__version__}')
print('HiGHS (scipy) 就绪，可解 LP')
"
```

### 预期输出

```
numpy=2.2.6, scipy=1.15.3
HiGHS (scipy) 就绪，可解 LP
```

### 求解器选择报告

```
问题类型：LP
已安装：HiGHS — scipy (MIT 开源)
推荐：scipy.optimize.linprog(method='highs')
说明：HiGHS 是当前最佳开源 LP 求解器（单纯形法+内点法双引擎）
```

---

## 示例 3：从零安装——LP + MIP

### 场景

用户需要解含整数变量的优化问题。

### 操作

```bash
# Step 1：检测
pip list | grep -iE "highspy|pulp|pyscipopt|mip|ortools|coptpy|gurobipy|cplex"

# Step 2：安装开源 MIP 求解器
pip install pulp highspy

# Step 3：验证
python -c "
from pulp import PULP_CBC_CMD
import highspy
print('PuLP/CBC OK, HiGHS OK')
"
```

### 预期输出

```
PuLP/CBC OK, HiGHS OK
```

### 求解器选择报告

```
问题类型：MIP
已安装：
  - [✅] PuLP/CBC (EPL)      — 教学友好，CBC 后端
  - [✅] HiGHS/highspy (MIT) — MILP 开源首选
推荐：highspy（HiGHS，MILP 性能优于 CBC）
备选：PuLP/CBC（语法更简洁，适合快速原型）
```

---

## 示例 4：从零安装——全套 SOCP

### 场景

用户需要解二阶锥规划。

### 操作

```bash
# Step 1：检测
pip list | grep -iE "cvxpy|clarabel|ecos|scs|cvxopt|cosmo|osqp|coptpy|gurobipy|mosek"

# Step 2：安装 SOCP 必装
pip install numpy cvxpy clarabel

# Step 3：验证
python -c "
import cvxpy; import clarabel
print(f'cvxpy={cvxpy.__version__}')
print(f'solvers={cvxpy.installed_solvers()}')
"
```

### 预期输出

```
cvxpy=1.6.4
solvers=['CLARABEL', 'SCIPY', 'SCS']
```

### 求解器选择报告

```
问题类型：SOCP
已安装：
  - [✅] CLARABEL (Apache 2.0) — SOCP 开源首选，同质嵌入内点法
  - [✅] SCS (MIT)              — 随 cvxpy 自动安装，ADMM 备选
推荐：cvxpy + CLARABEL
说明：CLARABEL 是 2024 年 Oxford 发布的新一代锥优化求解器，
      性能对标 MOSEK，原生支持 SOCP/SDP/指数锥/幂锥
```

---

## 示例 5：商业求解器 License 配置

### 场景：配置 COPT 学术 License

```bash
# 1. 安装
pip install coptpy

# 2. 下载 License 文件（从 https://www.shanshu.ai/copt）
#    将 license 文件放到指定目录，例如 /opt/copt/license/

# 3. 设置环境变量
export COPT_LICENSE_DIR=/opt/copt/license

# 4. 验证
python -c "
import coptpy as cp
from coptpy import COPT
env = cp.Envr()
print(f'COPT version: {cp.__version__}')
m = env.createModel('test')
print('COPT License OK')
"
```

### 场景：配置 Gurobi 学术 License

```bash
# 1. 注册 https://www.gurobi.com/downloads/
# 2. 安装
pip install gurobipy

# 3. 激活（使用注册后获取的 key）
grbgetkey XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX

# 4. 验证
python -c "
import gurobipy as gp
m = gp.Model('test')
print(f'Gurobi version: {gp.__version__}, License OK')
"
```

---

## 示例 6：全部本地求解器不可用 → 走 GitHub 搜索

### 场景

用户在受限环境（无 pip、离线、系统不兼容），所有本地求解器均不可用。

### 判断流程

```
检测 → 全部缺失
  → pip install 失败（网络/权限/系统不兼容）
    → 确认无法安装任何本地求解器
      → 进入 GitHub 搜索路径
```

### GitHub 搜索关键词

| 问题类型 | 推荐搜索词 |
|----------|-----------|
| LP | `site:github.com linear programming simplex solver python pure python` |
| MIP | `site:github.com branch and bound MILP solver python` |
| SOCP | `site:github.com second order cone programming python numpy only` |

### 筛选标准

1. **Star 数** > 50
2. **近期更新**（近 2 年有 commit）
3. **纯 Python 实现**（无 C/C++ 编译依赖）
4. **有 README** 含 API 文档和使用示例

### 输出模板（GitHub 搜索路径）

```markdown
### 环境与依赖
- 本地求解器检测：全部不可用
- pip install 尝试：失败（原因：网络受限）
- 策略：进入 GitHub 搜索路径

### GitHub 搜索结果
- 仓库：[owner/repo](URL)
- Star 数：xxx
- 最后更新：YYYY-MM-DD
- 授权：MIT / Apache 2.0 / ...
- 适配方式：...

### 求解结果
...
```

---

## 求解器综合对比表

### 开源求解器（无需 License）

| 求解器 | 安装 | 授权 | LP | MIP | SOCP | 推荐场景 |
|--------|------|------|:--:|:--:|:----:|----------|
| HiGHS | `pip install scipy` / `pip install highspy` | MIT | ★★★ | ★★★ | ✗ | LP+MIP 开源首选 |
| pyscipopt | `pip install pyscipopt` | Apache 2.0 | △ | ★★★ | ✗ | MIP 最强开源 |
| CLARABEL | `pip install clarabel` | Apache 2.0 | ★★ | ✗ | ★★★ | SOCP 开源首选 |
| PuLP/CBC | `pip install pulp` | EPL | ★★ | ★★ | ✗ | 教学首选 |
| python-mip | `pip install mip` | EPL | △ | ★★ | ✗ | MIP 现代接口 |
| OR-Tools | `pip install ortools` | Apache 2.0 | ★★ | ★★ | ✗ | Google 生态 |
| ECOS | `pip install ecos` | GPLv3 | ★ | ✗ | ★★ | SOCP 备选 |
| SCS | `pip install scs` | MIT | △ | ✗ | ★★ | 大规模稀疏 SOCP |
| CVXOPT | `pip install cvxopt` | GPLv3 | ★ | ✗ | ★ | 教学验证 |
| COSMO | `pip install cosmo` | Apache 2.0 | △ | ✗ | ★ | ADMM 锥优化 |
| OSQP | `pip install osqp` | Apache 2.0 | ★ | ✗ | △ | QP 实时控制 |
| GLPK | `pip install swiglpk` | GPLv3 | ★ | ★★ | ✗ | GNU 生态 |
| lpsolve | `pip install lpsolve55` | LGPL | ★ | ★ | ✗ | 嵌入式 |

### 商业求解器（需 License，学术免费）

| 求解器 | 安装 | LP | MIP | SOCP | 特色 |
|--------|------|:--:|:--:|:----:|------|
| COPT | `pip install coptpy` | ★★★ | ★★★ | ★★★ | 国产高性能，全支持 |
| Gurobi | `pip install gurobipy` | ★★★ | ★★★ | ★★★ | 业界标杆，v11+ SOCP |
| MOSEK | `pip install mosek` | ★★★ | ★★★ | ★★★ | 锥优化标杆，支持 MIP |
| CPLEX | `pip install cplex` | ★★★ | ★★★ | ★★ | IBM 生态，v20+ SOCP |

---

## 常见安装场景总结

| 场景 | 最小安装命令 | 安装时间（估算） | 磁盘占用 |
|------|-------------|:--------------:|:------:|
| 只做 LP | `pip install numpy scipy` | ~30 s | ~120 MB |
| LP + MIP | `pip install numpy pulp highspy` | ~45 s | ~180 MB |
| LP + SOCP | `pip install numpy cvxpy clarabel` | ~60 s | ~250 MB |
| 全套开源 | `pip install numpy scipy pulp highspy cvxpy clarabel ecos scs` | ~90 s | ~400 MB |
| 全套+商业 | 加上 `pip install coptpy gurobipy` | +30 s | +200 MB |
