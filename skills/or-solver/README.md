<!-- 作者：李爽夕 -->

# 配置指定求解器的环境

`or-solver` 为用户或建模任务已经选定的求解器配置 Python 环境：

- 检查当前 Python、目标软件包和必要依赖。
- 按需安装软件包，配置许可证及环境变量。
- 排查配置错误，说明环境是否可用。

求解器选型、问题建模和求解由用户或 OptSkills 等建模任务负责。

## 使用方式

> 为当前项目配置 COPT 的 Python 环境，使用 coptpy。检查依赖和许可证，
> 处理配置错误，告诉我当前环境是否可用。

也可以由 OptSkills 指定目标后调用：

OptSkills 决定使用 COPT → or-solver 配置 COPT 环境 → OptSkills 继续求解。

未指定求解器时，先明确目标；不会仅根据 LP、MIP 或 SOCP 类型自动挑选。
配置失败时说明阻碍，将后续决定交回原任务。

执行步骤见 [SKILL.md](SKILL.md)，安装和许可证配置场景见 [examples.md](examples.md)。
