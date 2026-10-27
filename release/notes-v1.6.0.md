## Kimodo 动作桥接 1.6.0

在 Blender 中通过中文界面生成 Kimodo 动作，并将动作适配到 PMX 角色。PMX 导入后自动修复骨名与骨序，按人形语义、静止姿态和身体比例完成重定向。

- 中文面板、参数说明、操作反馈与走路、挥手、下蹲、转身预设。
- 独立预览 Action，支持恢复原动作与保存结果，保留原骨骼层级、约束和权重。
- 识别 SOMA 的实际骨架命名；按当前场景帧率导入动作。
- 独立 Kimodo 运行环境，模型下载支持续传与 SHA256 校验。

### 验证

Blender 5.2.3 LTS、MMD Tools 4.5.14。两个真实 Kimodo 动作在三个 PMX 角色上完成六组验证，覆盖自动修复、重复准备、22 个人形关节、原约束保留、恢复原动作和独立 Action。保存重开姿态矩阵一致，桌面重定向预览撤销重做通过。脱敏结果见附件与仓库 `release/verification-v1.6.0.json`。

首版为 FK 重定向；FBX、足部接触修正和精细手指后续适配。中文界面提供双语动作预设，任意中文描述翻译暂未接入。

### 安装与更新

在 Blender 扩展仓库中添加：

`https://raw.githubusercontent.com/muchuanhehua/Kimodo_Blender_Bridge/main/release/index.json`

同步并安装「Kimodo 动作桥接」。也可以下载 ZIP 从磁盘安装。Kimodo 模型、运行环境和私人参考模型不包含在安装包中。
