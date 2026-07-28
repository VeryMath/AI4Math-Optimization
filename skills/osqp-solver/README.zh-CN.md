# OSQP Solver Skill

English guide: [README.md](README.md)

这个 AI4Math skill 使用原生 OSQP Python 接口，对连续凸二次规划进行建模、求解、
参数更新和独立复核。它目前是
[`VeryMath/AI4Math-Optimization`](https://github.com/VeryMath/AI4Math-Optimization)
的发布就绪本地候选；只有目标仓库接受并合并后，才能称为官方上游 package。

## 适用范围

使用本 skill 处理

\[
\min_x \tfrac12 x^\top P x + q^\top x
\quad\text{subject to}\quad l \leq Ax \leq u,
\qquad P=P^\top\succeq0.
\]

不要把混合整数、非凸、非线性约束、SDP 或一般 SOCP 模型路由到本 package。
附带的 JSON runner 用于可审查的小型 dense 示例，不是生产级 sparse 数据格式。

## 隔离安装

创建隔离环境并安装受支持的 OSQP 主版本：

```bash
python3 -m venv .venv-osqp
source .venv-osqp/bin/activate
python -m pip install -r requirements-test.txt
python scripts/check_osqp_environment.py --json
```

只有 `osqp`、`numpy`、`scipy` 均可导入，而且 OSQP 版本落在支持范围内时，探针才会
报告 `ready: true`。修改已有环境前先取得批准。

## 快速开始

在本 package 目录运行：

```bash
python scripts/solve_qp.py references/feasible-example.json
python scripts/solve_qp.py references/primal-infeasible-example.json
python scripts/solve_qp.py references/dual-infeasible-example.json
```

`--validate-only` 可在不安装数值依赖时做结构校验，但不会执行 PSD 或数值解检查：

```bash
python scripts/solve_qp.py references/feasible-example.json --validate-only
```

需要保存报告时，输出路径必须与输入路径不同：

```bash
python scripts/solve_qp.py references/feasible-example.json \
  --output outputs/feasible-result.json
```

## CLI 合同与边界

- 结构校验成功或求解结果被接受时退出码为 `0`；输入/依赖错误为 `2`；数值状态未被
  接受或 solver 失败为 `3`。
- 成功时标准输出严格为一个 JSON 文档；机器可读错误严格以一个 JSON 文档写入标准错误。
- 求解报告使用 `schema_version: osqp-solver-result-v1`；仅结构校验的报告使用
  `osqp-solver-validation-v1`。
- 拒绝 `settings.verbose: true`，避免 OSQP 日志破坏标准输出的单 JSON 合同。
- runner 会拒绝解析后相同的输入/输出路径，从而保留输入。不同路径上的已有输出文件
  可能被原子替换，因此应使用每次运行独立的路径。
- 默认 dense guard 接受的输入最大为 32 MiB，要求 `n <= 1000`，并且 `P` 与 `A`
  的 logical entry 总数不超过 `2,000,000`。更大问题应直接使用原生 sparse API。
- 被接受的解必须通过 primal feasibility、stationarity、
  normal-cone/complementarity、objective 和 PSD 检查；不可行性证书会先归一化，
  再接受尺度化 residual、方向符号和严格负裕量检查。

完整工作流见 [SKILL.md](SKILL.md)，数学验收条件见
[references/verification.md](references/verification.md)。

## 验证

激活隔离环境后，在 AI4Math Skill Library 根目录运行：

```bash
python -m unittest discover -s tests -p 'test_osqp_solver_skill.py' -v
python scripts/validate_skill_repo.py
```

被跳过的数值测试不能作为发布证据；公开发布前必须在安装 OSQP 的环境中做到该测试集
零跳过，并检查 unittest 汇总中 `skipped=0`。

## 许可证、引用与来源边界

在维护者授权并被上游接受后，本 package 预期沿用 AI4Math 仓库的 MIT license。
单独安装的 OSQP 项目采用 Apache-2.0 license；本 package 不打包、也不重新许可
OSQP 代码。软件许可和学术引用是两项不同义务。官方 OSQP 引用见
[references/citation.md](references/citation.md)。

本工作流和参考材料依据
[references/python-api.md](references/python-api.md) 所列 OSQP 官方文档整理。
公开发布前，人类维护者必须确认发布授权，并如实记录贡献者署名；AI agent 完成打包
不能替代这项授权。
