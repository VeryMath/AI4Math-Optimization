# AI4Math 优化 Skill

[English](README.md) | 简体中文

`optimization-skill` 是给 coding agent 使用的数学优化 Skill。它帮助 agent 读取具体优化问题，建立经过 review 的模型，匹配 OptSkills 参考，选择 solver 路由，生成经过批准的求解入口，解析证据，并诊断失败原因。

推荐的使用方式很简单：让你的 coding agent 自己安装这个 Skill，然后让它用这个 Skill 处理你的优化问题。环境路径、复制、软链接、配置和重载都尽量交给 agent 做。

## 1. 让 Coding Agent 安装

把下面这段发给你的 coding agent：

```text
请从 https://github.com/VeryMath/AI4Math-Optimization 安装 optimization-skill 到你自己的 skill 系统。

如果本地已经有 checkout，就使用本地版本；否则 clone 这个仓库。请检测你的环境把 skills 存在哪里，把 skills/optimization-skill 安装或软链接到正确位置，按需更新 registry 或配置，必要时 reload 或 restart，并验证 $optimization-skill 可以被发现。
```

agent 应该自己判断需要用户级 skill 目录、项目级 skill 目录、软链接、复制目录，还是配置文件。用户不需要知道它内部的 skill 路径。

## 2. 开始优化问题交互

安装完成后，开一个新对话，发送：

```text
使用 $optimization-skill。
```

Skill 应该先只问交互语言：

```text
你想用中文还是英文交流？
```

选择语言后，直接发送具体优化问题。自然语言、LaTeX、论文片段、源码、README 命令、数据描述、`.mat`/`.npz`/`.json`/`.yaml`/CSV 文件，或已有 `problem.yaml` 都可以。

agent 接下来应该建模、暴露歧义、请你确认模型、提出 solver 路由，并且只有在你批准后才运行代码。

## CDOpt Workflow

CDOpt 任务分成两个检查：

1. 安装/API 验证：运行或提出运行安装后的 manifold smoke test。

```bash
cd /Users/conanxu/cdopt_manifold_tests
python run_all_notebooks.py
```

2. 应用级 examples：smoke test 通过后，使用 [examples/cdopt-example-prompts.zh-CN.md](examples/cdopt-example-prompts.zh-CN.md) 或 [examples/cdopt-example-prompts.md](examples/cdopt-example-prompts.md) 中可复制的 prompts。

smoke test 只验证 CDOpt runtime 和核心 API，不代表某个应用模型在数学上正确。

## 关于这个 Skill

`optimization-skill` 是优化任务的统一入口。用户给出具体问题；agent 负责把它转成可 review 的工作流。

这个 Skill 会引导 agent：

- 先读具体问题，再决定需要追问什么
- 识别变量、目标函数、约束、维度、数据和歧义点
- 必要时对照导入的 OptSkills references
- 在生成可执行 solver code 前，先建立 modeling checkpoint
- 把确认后的模型路由到 SDPT3、CDOpt 或仓库原生方法等 solver 生态
- 生成受限的求解入口，并且只在批准后运行
- 报告目标值、feasibility、solver status、数值警告和失败原因

它本身不是 solver，而是一个 workflow layer：帮助 coding agent 更谨慎地使用 solver，并把模型 review 和执行批准保持可见。

## 维护者检查

在仓库根目录运行：

```bash
python /Users/conanxu/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/optimization-skill
python -m pytest -q
```

Skill 指令在 [skills/optimization-skill/SKILL.md](skills/optimization-skill/SKILL.md)。solver 路由细节在 `skills/optimization-skill/references/` 目录下。
