# OptSkills

OptSkills 是一个独立的薄入口，连接 103 张已发布的 OptSkills
问题原型卡片。它帮助智能体选择卡片、为用户的实际运筹问题建模、在环境允许时求解，并如实报告已检查的内容。

## 来源选择

该库包含 93 张 NanoCO 卡片和 10 张仅来自 learned 的卡片；不包含重复的
cluster 卡片，也不包含 `ingredients.json`。选中的卡片及其相对路径列在
`skill_library/index.json` 中。

## 安装

克隆 `VeryMath/AI4Math-Optimization`，然后只把 `skills/optskills`
链接到智能体的技能目录：

```bash
git clone https://github.com/VeryMath/AI4Math-Optimization.git
cd AI4Math-Optimization
mkdir -p ~/.codex/skills
ln -s "$PWD/skills/optskills" ~/.codex/skills/optskills
```

## 快速开始

使用下面的提示：

> 阅读 `SKILL.md`，通过 `skill_library/index.json` 选择相关的 OptSkills
> 卡片，为我的问题建模，在可以时求解，并检查关键约束。

## 更新

只有需要上游更新时才使用下面的提示：

> Update this standalone OptSkills package from the official upstream. Read `UPDATE.md`, report proposed changes first, and wait for approval before editing.

## 边界

原始卡片可能含有占位符或未经验证的示例。已安装、已加载、已求解和已检查是不同的声明；应分别报告。普通使用仅依赖本包，不调用同仓库的其他技能，也不要求上游的训练、智能体、聊天或嵌入系统。

## 许可与来源

上游署名见 [SOURCES.md](SOURCES.md)，许可信息见 [LICENSE](LICENSE)。
