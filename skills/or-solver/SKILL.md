---
name: or-solver
description: >-
  Configure the Python environment for a solver already specified by the user
  or a modeling skill. Check the target interpreter and dependencies, install
  required packages, configure licenses and environment variables, troubleshoot
  setup errors, and report availability. Use for installing or repairing a named
  solver environment. Solver choice, problem modeling, and solving belong to the
  caller.
metadata:
  author: "李爽夕"
---

<!-- 作者：李爽夕 -->

# 配置指定求解器的环境

先取得明确的目标求解器，再配置它所需的环境。求解器由用户、OptSkills 或其他
建模任务决定；本 skill 不推荐、排序或替换求解器，也不建模、求解或搜索替代算法。

## 1. 明确配置目标

- 取得指定的求解器名称，以及已经确定的调用接口和版本要求（若有）。例如：
  COPT / `coptpy`，或 CLARABEL / `cvxpy`。
- 确定项目使用的 Python 解释器、虚拟环境或 notebook 内核。用户未指定时，
  先读取当前项目的环境配置，不自行切换系统默认 Python。
- 记录当前安装或许可证报错，以及已提供的许可证位置或服务配置。
- 缺少目标名称时，询问要配置哪个求解器。仅给出“我要解 LP”不足以开始安装；
  将选型交给用户或原建模任务。

## 2. 检查 Python 和目标依赖

以下命令中的 `python` 指目标项目实际使用的解释器；后续安装和检查使用同一个解释器。

```bash
python -c "import sys; print(sys.executable); print(sys.version)"
python -m pip --version
```

只检查目标求解器及指定接口所需的包、动态库和系统依赖，不扫描全部求解器。
用 `python -m pip show` 查看目标包的安装位置和版本，再导入其实际模块，区分
“未安装”“装在另一个环境”“版本或架构不匹配”“动态库无法加载”等情况。

按目标求解器的官方安装文档核对支持的 Python 版本和平台，并遵守项目已有版本约束。
只读取当前目标所需的资料；不维护求解器能力矩阵或优先级列表。

## 3. 安装并配置

- 在目标 Python 环境内，用 `python -m pip` 或项目已有的包管理方式安装缺失依赖。
  已满足要求的包不重装，不批量安装其他求解器，也不升级无关依赖。
- 安装遵循当前任务的授权；用户已要求安装或配置该环境时，不重复询问同一动作。
- 按官方文档配置目标求解器需要的许可证、许可证服务或环境变量。软件包安装成功
  不代表取得了完整许可证；只使用用户已有或实际取得的许可。
- 环境变量必须对后续求解进程生效。复用项目已有的启动或环境配置方式，说明
  生效范围及是否需要重启终端或 notebook 内核，不把一次性子进程的设置当成持久配置。
- 不输出许可证密钥或文件正文，也不将其写入公开仓库。

具体命令按目标求解器及操作系统确定，见 [配置场景](examples.md)。

## 4. 排查并说明是否可用

重新检查目标包的导入、版本、动态库和必要环境变量。许可证使用官方诊断工具或
接口提供的检查方式；按实际结果说明许可证类型、限制和错误，不仅凭导入成功就宣布可用。

如果许可证只能在真正求解时确认，说明依赖配置已完成、许可证尚待原任务确认。
不另造问题或运行求解示例来验证环境；真实求解和结果检查由原建模任务完成。

按具体错误处理解释器路径、Python/系统架构、包版本、动态库、许可证路径和
许可证服务连接问题。无法完成时说明原因及缺少的条件，不自行改用另一求解器。

返回简短的配置结果：

- 指定的求解器、调用接口和实际 Python 路径。
- 依赖版本，以及已执行的安装或配置操作。
- 许可证与环境变量的检查结果及生效范围。
- 环境是否可用；尚未确认的事项或阻碍。

完成后由原任务继续执行。单独调用时在配置结果处结束，不启动建模 skill。
