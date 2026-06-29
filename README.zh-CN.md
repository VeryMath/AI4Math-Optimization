<div align="center">

# AI4Math · 优化

面向数学优化建模、求解器配置、LP/MIP/SOCP workflow 和流形约束优化的 AI4Math 技能集合。

[English](README.md) · [贡献者](CONTRIBUTORS.md) · [技能包](#技能包) · [安装](#安装) · [快速开始](#快速开始) · [安全边界](#安全边界)

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

## 安装

推荐方式是 AI 自动安装：让你的 coding agent 自己 clone 或更新仓库、读取 Skill 说明、安装入口并验证 discovery。

```text
请帮我安装这些 AI4Math Skills。

仓库：https://github.com/VeryMath/AI4Math-Optimization.git
分支：main
Skill 路径：
- skills/cdopt-optimization
- skills/copt-linear-program
- skills/linear-programming
- skills/mixed-integer-programming
- skills/second-order-cone-programming
- skills/or-solver

请执行：
1. 本地 clone 或更新仓库。
2. 读取 README.md、SKILL.md、AGENTS.md（如果存在）以及每个目标 Skill 入口。
3. 如果当前环境支持本地 Skill discovery，把每个包含 SKILL.md 的目录链接到本地 skills 目录。
4. 如果某个 Skill 依赖相邻的共享支持目录，请保留这些 sibling 目录。
5. 验证安装后的 Skills 是否可被发现。
6. 告诉我安装路径、是否需要重启 agent，并给我一个测试 prompt。
```

Codex 风格本地 discovery 的手工 fallback：

```bash
git clone https://github.com/VeryMath/AI4Math-Optimization.git
cd AI4Math-Optimization
mkdir -p ~/.codex/skills
ln -s "$PWD/skills/cdopt-optimization" ~/.codex/skills/cdopt-optimization
ln -s "$PWD/skills/copt-linear-program" ~/.codex/skills/copt-linear-program
ln -s "$PWD/skills/linear-programming" ~/.codex/skills/linear-programming
ln -s "$PWD/skills/mixed-integer-programming" ~/.codex/skills/mixed-integer-programming
ln -s "$PWD/skills/second-order-cone-programming" ~/.codex/skills/second-order-cone-programming
ln -s "$PWD/skills/or-solver" ~/.codex/skills/or-solver
```

如果你的 agent 使用别的本地 Skill 目录，把 `~/.codex/skills` 替换成对应配置路径。

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
