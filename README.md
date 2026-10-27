# Kimodo 动作桥接

中文 Kimodo 动作生成与通用人形动作重定向插件。首期支持通过 MMD Tools 导入 PMX、自动骨骼修复、参考姿态校准与独立动作输出；FBX 导入适配留待后续。

本项目基于 [Lewdineer/Kimodo_Blender_Bridge](https://github.com/lewdineer/Kimodo_Blender_Bridge) 的社区插件开发，保留原作者署名和 GPL 声明。上游原始说明保存在 [UPSTREAM.md](UPSTREAM.md)。Kimodo 模型与运行依赖沿用各自的许可和来源。

## 版本与安装

当前版本 **1.6.1**。安装包见 [Releases](https://github.com/muchuanhehua/Kimodo_Blender_Bridge/releases)。

推荐在 Blender「偏好设置 → 获取扩展 → 仓库」添加远程仓库：

`https://raw.githubusercontent.com/muchuanhehua/Kimodo_Blender_Bridge/main/release/index.json`

同步后安装「Kimodo 动作桥接」。后续通过这个仓库更新。也可以从 Release 下载 ZIP，使用「从磁盘安装」。

已实际验证：Windows、Blender **5.2.3 LTS**、MMD Tools **4.5.14**、NVIDIA RTX 4060 Ti 16GB。Kimodo 使用独立 Python 环境，不往 Blender 内置 Python 安装 PyTorch。

## 使用流程

1. 在 `3D 视图 → 侧栏 → Kimodo → 模型准备` 点击「导入 PMX 并自动修复」。已有角色可选中模型后点击「使用所选角色并自动修复」。
2. 在「Kimodo 环境」指定独立环境 Python，或使用自动安装。点击「启动 Kimodo」。
3. 在「动作生成」选择中文预设，检查英文动作描述、时长和随机种子，生成动作。也可以导入已有 BVH。
4. 在「动作重定向与保存」指定动作源和目标，点击「自动匹配骨骼」，检查映射、帧范围和角色移动方式。
5. 点击「预览重定向」。这会创建独立预览 Action；「恢复原动作」可还原之前的 Action、姿态和 IK 设置。
6. 检查满意后，填写动作名称并点击「保存为独立动作」。原动作保留，模型的辅助骨、原有约束和权重不被删除。

PMX 自动修复会明确启用导入器的骨序修复，并修复骨名编码、15 字节长度限制和重名。原名称作为别名保留，修复后重新检测人形关节。骨名修复不能代替骨轴、比例和参考姿态校准，后者由重定向核心完成。

本版按 SOMA 的实际层级识别源骨架；例如 SOMA 的 `LeftLeg` 是大腿，不能按 Mixamo 的同名小腿处理。源动作按当前场景帧率导入，30 FPS 动作在 24 FPS 场景中保持时间长度。

## Kimodo 环境

自动安装沿用社区 Aero-Ex 离线适配后端，下载文本编码器和 NVIDIA SOMA 模型。下载支持分段、续传与 LFS SHA256 校验，安装完成后可离线生成。

开发环境可用系统 Python 3.12 执行：

```text
python tools/setup_runtime.py
```

默认创建项目下忽略的 `.runtime/kimodo-venv`。在插件高级设置或偏好设置中指定这个环境目录与其中的 `Scripts/python.exe`。模型、依赖和令牌均不进入安装包。

中文界面不代表模型原生支持任意中文动作描述。本版提供中文动作预设，对应的英文描述可查看、修改；自由中文翻译后续另行适配。

## 验证与边界

- 三个不同层级、分别有 332、643、283 根骨骼的 PMX 角色，均识别出 22 个人形关节。
- 实际生成 Kimodo 走路和挥手动作，并在三个角色上检查导入、重复修复、重定向、原 Action 保留、恢复与独立动作输出。
- 原约束与原骨架父子层级保留；保存重开后抽查的 54 个姿态矩阵一致。
- 首版采用经过姿态校准的 FK 重定向，尚未提供足部接触修正、精细手指、表情或 FBX 导入适配。
- 启用的 NLA 轨道可能混合目标动作，本版会明确要求先停用这些轨道。

验证入口为 `tools/verify_blender.py` 和 `tools/inspect_saved.py`。私人参考模型、动作、工程和图像证据放在仓库外的 Test 或忽略的 `.verification/` 中，不随源码和安装包分发。

当前维护与发布约束见 [AGENTS.md](AGENTS.md)。
