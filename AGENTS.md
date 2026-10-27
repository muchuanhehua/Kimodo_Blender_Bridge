# Kimodo Blender Bridge 项目入口

## 项目与当前阶段

- 遵循上级 `../AGENTS.md`；本项目独立于 MAVR，不继承其发布授权、验证结果和发布流程。
- 用户于 2026-10-27 要求 Fork 仓库并预览中文化方案；随后明确定位为通用动作重定向插件，首期适配 PMX 模型，后续扩展 FBX 模型，二者均需重定向。
- Fork：`https://github.com/muchuanhehua/Kimodo_Blender_Bridge`。
- 上游：`https://github.com/lewdineer/Kimodo_Blender_Bridge`；本次读取基线为 `7181a24624cc98549791540c7fce5b78e4496e12`，声明版本为 `1.5.8`。
- 当前发布版本为 1.6.1，已实现中文界面、PMX 自动修复、人形语义识别、姿态与比例校准，以及独立 Action 预览、恢复和保存。真实 Kimodo 走路、挥手动作已在三个角色验证；保存重开与桌面预览撤销重做通过。Release 与标签已发布，本地 Blender 已通过远程仓库更新、配置，并通过桌面 GPU 启动、生成及 BVH 导入验证。
- `design/kimodo-retarget-preview.html` 只演示拟议界面和流程，按钮不连接 Blender 或 Kimodo。

## 范围与资源

- 用户已于 2026-10-27 明确授权实施中文化、PMX 导入后自动修复和动作重定向，使用 Test 的三个角色实际验证，提交并更新仓库，再远程更新、配置本地 Blender；FBX 后续适配。
- 本轮授权包含所需的 Kimodo 环境与模型配置、独立 Blender 验证、插件安装和更新配置；不改动私人原始 PMX 文件，不覆盖用户已有工程。
- 保留上游作者署名和许可证声明；模型与第三方组件单独记录来源，不将模型权重、私人 PMX、贴图、动作和 Blender 工程加入发布仓库。
- 环境、模型缓存和私人验证证据保存在忽略的 `.runtime/`、`.verification/` 中，不能进入发布包或 Git 提交。
- 本项目的职责为动作生成、模型准备和通用人形动作重定向；MAVR 为独立材质与展示项目。
- 工作区 `../Test/原神模型/` 由用户提供，含刻晴、奥黛塔、希诺宁角色及道具，供参考与验证；原始资源保持原位，不复制进本仓库或安装包。
- 本轮实际验证环境为 Blender 5.2.3 LTS、MMD Tools 4.5.14；1.6.0 的两个真实 Kimodo 动作分别在三个 PMX 角色上通过。1.6.1 补齐动态界面文字，构建时核对相同核心指纹，并另做实际安装、桌面启动和生成导入验证。私密证据位于 `.verification/`，公开的脱敏摘要位于 `release/verification-v1.6.0.json`、`release/verification-v1.6.1.json`。

## 后续实现约束

- 中文化集中维护翻译；技术标识、协议字段、骨骼真实名称与第三方错误原文保留。界面中文化与自由中文提示词翻译分别设计。
- 架构采用格式导入与修复适配器、统一人形骨骼定义和参考姿态、公共重定向求解、目标骨架写回与独立 Action。PMX 和后续 FBX 共享公共重定向核心，不按文件格式复制一套求解算法。
- PMX 使用 MMD Tools 导入，导入器显式启用骨序修复，导入后自动调用骨名问题修复并检查结果。修复前保留原始名称别名与骨架信息，记录修复结果；只处理本次导入的模型，重复准备应保持结果稳定。
- MMD Tools 的 `fix_bone_issues` 主要修复名称编码、长度和重名；`fix_bone_order` 整理骨骼 ID 与顺序。两者不能代替拓扑、骨轴与参考姿态校准。IK 链、固定轴等结构调整按检测结果和验证过的导入配置处理，不盲目启用所有选项。
- PMX 适配按语义识别日文、英文和实际骨名，保留左右标记并处理歧义；不能用删除所有非英文字符的匹配替代语义识别。FBX 后续使用自身骨架配置和同一人形定义，不依赖 MMD Tools 的元数据。
- 跨模型的一致性建立在中间人形定义或求解骨架上；原模型的辅助骨、追加变换、IK 控制、权重与物理绑定需要保留。不能为了相同骨数或相同父子层级直接裁剪原骨架。
- 新动作使用独立 Action；烘焙只处理本插件管理的对象、通道和临时约束，保留 MMD Tools 的 IK、附加变换及已有动作。
- 记录参考姿态、单位、根运动和腿部控制方式；无法支持的骨架或缺少关键骨时明确报告，不跳过后宣称成功。
- 实施前核实用户 Blender 与 MMD Tools 的实际版本。运行验证和发布规则由本项目单独确定。

## 构建与更新

- 构建入口为 `tools/build_release.py --blender <Blender executable>`，使用原生扩展构建与校验，检查版本、精确载荷、源码与 ZIP 字节一致性、CRC、SHA256 以及实际验证核心指纹。
- 发布内容为源码、`release/index.json`、构建与脱敏验证摘要、版本 ZIP。远程仓库入口为 GitHub main 的 `release/index.json`，安装包下载自对应 Release。
- 已公开的版本、tag 和 ZIP 不覆盖；发布后载荷变动需递增版本。发布前后的纯项目规则或安装状态记录不改变插件载荷时不重新打包。
- 1.6.1 发布源码为 `05cac993ab603ba9981f77042050f97fc9c76f5d`；ZIP SHA256 为 `510eb8734cad7846f266a6ba6b618369b3cb93ec440f202572d07597cff448da`，GitHub Release 摘要一致，本地 23 个安装文件已逐一核对。远程仓库入口为 `https://raw.githubusercontent.com/muchuanhehua/Kimodo_Blender_Bridge/main/release/index.json`。
- 本地扩展模块为 `bl_ext.kimodo.kimodo_blender_bridge`。运行环境位于忽略的 `.runtime/kimodo-venv/`，偏好设置已保存；新 Blender 进程验证 23 个安装文件与发布包一致，并能自动定位运行环境。配置复现入口为 `tools/configure_installed.py`，`--update` 仅同步并安装 Kimodo 仓库中的此扩展。实际安装与桌面结果保存在 `.verification/installed-fresh-process.json`、`.verification/installed-gui-result.json`，桌面验证工程为 `.verification/installed-demo-v1.6.1.blend`。
- 本次桌面验证脚本曾在无窗口上下文时切换侧栏导致 Blender 原生崩溃；崩溃栈定位在 `ED_region_visibility_change_update`。工具脚本已使用显式窗口上下文，且不再赋值只读侧栏类别；后续桌面面板与预览撤销重做通过。此脚本不进入安装包。
