# 指定求解器的配置场景

<!-- 作者：李爽夕 -->

通用步骤见 [SKILL.md](SKILL.md)。以下场景说明配置范围；命令中的 `python`
必须使用原任务的解释器，配置结果以实际检查为准。

## OptSkills 已选择 COPT / coptpy

原任务已明确使用 COPT，并提供项目 Python 环境。

先检查 `coptpy` 是否装在这个解释器下：

```bash
python -m pip show coptpy
python -c "import coptpy; print(coptpy.__file__)"
```

缺少时按项目版本约束安装。以下命令适用于没有额外版本约束的情况：

```bash
python -m pip install coptpy
```

需要的系统组件和平台要求以 [COPT Python 接口安装说明](https://guide.coap.online/copt/en-doc/pythoninterface.html)
为准，不能把安装 Python 接口等同于所有运行条件均已满足。

如果当前授权采用许可证文件，按 [COPT 许可证安装说明](https://guide.coap.online/copt/en-doc/install.html)
处理 `license.dat` 和 `license.key`。可放在用户主目录下的 `copt` 目录，或将
`COPT_LICENSE_DIR` 指向实际许可证目录；核对实际使用的位置。

当前安装提供 `copt_licgen` 时，可在所用许可证目录执行官方检查：

```bash
copt_licgen -v
```

该工具不可用时，按官方说明检查安装内容。报告实际依赖、许可检查结果及后续
求解进程需要继承的环境设置，然后由原 OptSkills 任务继续建模和求解。

## 已指定 Gurobi，但许可证配置报错

确认当前 Python 使用的是原任务指定的 `gurobipy`，再核对其许可证类型、位置或
服务连接。参考 [Gurobi Python 安装说明](https://support.gurobi.com/hc/en-us/articles/360044290292-How-do-I-install-Gurobi-for-Python)
及其中的许可文档；通过 pip 安装 Python 包不会同时提供 Gurobi 许可证工具。

按实际报错修复该目标环境。缺少有效许可或所需工具时说明缺项，不改用 COPT、
HiGHS 或其他求解器，也不将试用许可描述为完整许可。

## 已指定 MOSEK，许可证不在默认位置

确认目标 Python 下的 `mosek` 安装及用户提供的许可证位置，参考
[MOSEK 安装说明](https://docs.mosek.com/latest/install/installation.html)和
[许可证客户端配置](https://docs.mosek.com/latest/licensing/client-setup.html)。
需要时设置 `MOSEKLM_LICENSE_FILE`，并确保设置对实际求解进程生效。
报告依赖与许可证检查结果，不在环境配置任务中建立模型。

## 用户只说“配置一个能解 LP 的环境”

此时尚未指定求解器。先请用户或原建模任务决定目标，再执行配置；不扫描全部
求解器、不按排名推荐，也不自动安装一套软件。

## 已指定的求解器在当前平台无法安装

核对官方支持的平台、Python 版本、系统架构和实际安装错误，说明缺少的条件。
后续是否更换 Python 环境或求解器，由用户或原建模任务决定。
