<div align="center">

# AI4Math · 优化

面向数学优化建模、求解器配置、LP/MIP/SOCP workflow 和流形约束优化的 AI4Math 技能集合。

[English](README.md) · [技能包](#技能包) · [快速开始](#快速开始) · [安全边界](#安全边界)

![version](https://img.shields.io/badge/version-0.1.0-blue)
![skills](https://img.shields.io/badge/skills-6-2ea44f)
![license](https://img.shields.io/badge/license-MIT-green)

</div>

## 这个仓库是什么

这个仓库是 AI4Math 优化方向的技能入口，收集用于数学规划建模、求解器选择、环境检查、示例适配和优化运行证据报告的技能包。

根 README 负责说明地图；具体建模或求解时，请进入匹配问题类型的 `skills/` 子目录。

## 技能包

| 包 | 适用任务 | 入口 |
| --- | --- | --- |
| [`cdopt-optimization`](skills/cdopt-optimization/) | CDOpt 和流形约束优化建模、验证、runner 生成和证据报告。 | [`README`](skills/cdopt-optimization/README.md) · [`SKILL`](skills/cdopt-optimization/SKILL.md) |
| [`copt-linear-program`](skills/copt-linear-program/) | COPT/coptpy 线性规划 workflow、文字题重述和求解脚本。 | [`README`](skills/copt-linear-program/readme.md) · [`SKILL`](skills/copt-linear-program/SKILL.md) |
| [`linear-programming`](skills/linear-programming/) | 通用 LP 建模、求解器选择和自然语言到模型的工作流。 | [`README`](skills/linear-programming/README.md) · [`SKILL`](skills/linear-programming/SKILL.md) |
| [`mixed-integer-programming`](skills/mixed-integer-programming/) | 含 binary、integer 和 continuous 变量的 MILP/MIP 建模。 | [`README`](skills/mixed-integer-programming/README.md) · [`SKILL`](skills/mixed-integer-programming/SKILL.md) |
| [`second-order-cone-programming`](skills/second-order-cone-programming/) | SOCP 建模和基于 cvxpy 的锥优化求解流程。 | [`README`](skills/second-order-cone-programming/README.md) · [`SKILL`](skills/second-order-cone-programming/SKILL.md) |
| [`or-solver`](skills/or-solver/) | 为 OR skills 提供统一求解器检测、安装规划、license 检查和选择策略。 | [`README`](skills/or-solver/README.md) · [`SKILL`](skills/or-solver/SKILL.md) |

## 快速开始

克隆仓库并选择技能包：

```bash
git clone https://github.com/VeryMath/AI4Math-Optimization.git
cd AI4Math-Optimization
```

求解器配置与选择从这里开始：

```text
skills/or-solver/SKILL.md
```

通用 LP/MIP/SOCP 建模请进入 `skills/` 下对应包。CDOpt 或流形约束优化从这里开始：

```text
skills/cdopt-optimization/SKILL.md
```

## 仓库结构

```text
AI4Math-Optimization/
├── README.md
├── README.zh-CN.md
├── SKILL.md
└── skills/
    ├── cdopt-optimization/
    ├── copt-linear-program/
    ├── linear-programming/
    ├── mixed-integer-programming/
    ├── or-solver/
    └── second-order-cone-programming/
```

求解器示例、脚本、references 和生成的运行证据应放在所属技能包内。

## 验证

这个仓库没有根级构建步骤。修改技能包后，请检查 `SKILL.md`、README 链接、脚本和包内示例；如果使用 Codex 本地 skill validator，请对每个变更过的标准技能包运行验证。

## 安全边界

不要提交求解器 license、API key、私有数据集、`.env` 文件、含敏感数据的 solver logs 或本地运行输出。公开示例应包含 benchmark 数据来源说明，并确认可以再分发。
