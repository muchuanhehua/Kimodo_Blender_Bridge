"""Central Chinese UI translation without changing identifiers or rig names."""
import re

import bpy

ZH = {
    "2D ground-plane position (XZ). Place an Empty where you want the character's root to be.": "平面上的根运动路径点；在角色需要经过的位置放置空物体",
    "Full-body keyframe. Pose an armature exactly as you want the character at this frame.": "全身关键姿态；将参考骨架摆成该帧需要的姿态",
    "Left wrist/hand end-effector target. Place an Empty at the desired hand position.": "左手腕的位置目标；在目标位置放置空物体",
    "Right wrist/hand end-effector target.": "右手腕的位置目标",
    "Left foot/heel end-effector target. Place an Empty at the desired foot position.": "左脚或脚跟的位置目标；在目标位置放置空物体",
    "Right foot/heel end-effector target.": "右脚或脚跟的位置目标",
    "Delete the partial virtual environment, then reinstall": "删除未完成的独立环境后重新安装",
    "Delete the virtual environment": "删除独立 Python 环境",
    "Copy only rotation; root bone also gets Copy Location": "复制旋转，根骨同时复制位移",
    "Copy location + rotation + scale together": "同时复制位置、旋转和缩放",
    "Full parent-child relationship; preserves rest-pose offset": "建立父子约束并保留静止姿态偏移",
    "Child Of constraint with only rotation enabled (no location or scale)": "仅使用父子约束的旋转通道",
    "SOMA / SMPL": "SOMA 人形",
    "Also constrain the facing direction at this waypoint": "同时约束这个路径点的角色朝向",
    "Also delete the Empty/object from the scene": "同时删除场景中的约束标记对象",
    "Apply generated motion to this armature instead of creating a new one. Preserves retargeting constraints already pointing at it. Leave empty to always create a new armature.": "将生成动作应用到所选动作源骨架；留空时创建新的动作源骨架",
    "Automatically offset all constraint positions so the earliest waypoint lands at Kimodo's (0,0) origin.": "整体偏移约束位置，使首个路径点对齐 Kimodo 原点",
    "Bar colour in the timeline": "动作段在时间线中的显示颜色",
    "Bezier or NURBS curve to sample as root XZ waypoints": "用于采样角色根运动路径点的贝塞尔或 NURBS 曲线",
    "Blender frame at which this constraint applies": "这个生成约束生效的 Blender 帧",
    "Desired facing direction in degrees (0 = +Y forward in Blender / -Z in Kimodo)": "角色的目标朝向；零角度对应 Blender 的 +Y 方向",
    "Empty or Armature that defines the spatial constraint in the viewport": "用于在视口中定义生成约束的空物体或骨架",
    "File format Kimodo should export": "Kimodo 输出的动作文件格式",
    "Folder where the Kimodo virtual environment is created and looked for. Stored in the addon preferences so it is remembered across Blender restarts and scenes. Leave blank to use the default ~/.kimodo-venv.": "独立 Kimodo 环境的安装目录，保存后可在重启与不同工程间复用；留空使用默认目录",
    "Frames-per-second Kimodo generates at (default 30). Used to convert Blender frame numbers to Kimodo frame indices.": "Kimodo 动作的源帧率，用于换算当前场景的帧数，默认 30 FPS",
    "How this bone pair is driven": "这组骨骼映射使用的驱动方式",
    "Index of the constraint to remove (-1 = active)": "要移除的生成约束序号；-1 表示当前项",
    "JSON blob of all saved bone-mapping presets": "所有已保存骨骼映射预设的 JSON 数据",
    "Kimodo constraint type": "生成约束的类型",
    "Last-built constraints JSON (read-only preview)": "最近生成的约束 JSON，只读显示",
    "Optional HuggingFace access token (hf_...). Prevents rate-limiting during model downloads. Get a free read token at huggingface.co/settings/tokens": "可选的 Hugging Face 只读令牌，用于模型下载认证或减少限流；不会写入发布文件",
    "Optional human-readable label for this constraint": "生成约束的自定义显示标签",
    "Override the target bone's 'Inherit Rotation' property. When unchecked, this bone will not inherit rotation from its parent. Applied immediately on toggle and again when you click Apply Constraints": "旧版映射的继承旋转选项；新的人形解算保留模型原始继承设置",
    "Path to the Python executable (or venv/conda root) that has Kimodo installed. Leave blank to auto-detect from PATH.": "已安装 Kimodo 的 Python 可执行文件或独立环境目录；留空时自动检测",
    "Root / hip bone on the target armature (gets position + rotation)": "目标角色中承接整体位移的骨骼",
    "Seed actually used in the most recent generation. Switching to FIXED copies this into `seed` so the result can be locked.": "上次实际使用的种子；切换到固定模式后复用这个种子",
    "Show advanced connection overrides: the Python executable path, HuggingFace token, and the Kimodo venv install location": "显示 Python 路径、Hugging Face 令牌和独立环境目录等高级配置",
    "Single Clip generates one motion from one prompt. Timeline builds a longer animation from multiple prompt segments stitched together": "单段模式按一个描述生成动作；时间线模式组合多段动作描述",
    "Which Kimodo skeleton/model to use": "用于生成动作的 Kimodo 骨架模型",
    "Standard human body skeleton (SOMA). Best for most use cases.": "标准 SOMA 人体骨架，适合人形角色重定向",
    "Standard motion capture format. Blender imports natively.": "通用骨骼动作格式，可直接导入并重定向",
    "Kimodo native format (requires manual import).": "Kimodo 原始数据格式，需要另行处理",
    "Kimodo Blender Bridge": "Kimodo 动作桥接",
    "⚙  Connection": "① Kimodo 环境",
    "🎬  Generate": "② 动作生成",
    "🎯  Motion Constraints": "生成约束",
    "🔗  Retargeting": "③ 动作重定向",
    "ℹ  Help": "帮助",
    "Connection": "连接", "Generate": "动作生成", "Retargeting": "动作重定向",
    "Advanced": "高级设置", "Status": "状态", "Settings": "设置",
    "Start Kimodo": "启动 Kimodo", "Stop Kimodo": "停止 Kimodo",
    "Install Kimodo (Auto)": "自动安装 Kimodo", "Use Installed Kimodo": "使用已安装的 Kimodo",
    "Retry Install": "重试安装", "Reset Venv": "重置环境", "Delete Venv": "删除环境",
    "Delete Virtual Environment": "删除独立 Python 环境", "Delete Directory": "删除目录",
    "Install Location": "环境安装目录", "System Python": "系统 Python", "Python": "Python",
    "HuggingFace Token": "Hugging Face 访问令牌", "Kimodo Python:": "Kimodo Python：",
    "Kimodo not installed": "尚未安装 Kimodo", "Installation incomplete": "安装未完成",
    "Kimodo venv ready": "Kimodo 环境已就绪", "Installing Kimodo…": "正在安装 Kimodo…",
    "Enable Memory Offload": "启用内存卸载", "Model": "模型", "Model:": "模型：",
    "NVIDIA GPU required!": "需要 NVIDIA 显卡", "Kimodo only works with NVIDIA GPUs (CUDA).": "Kimodo 需要支持 CUDA 的 NVIDIA 显卡。",
    "AMD and Intel GPUs are not supported.": "当前后端不支持 AMD 和 Intel 显卡。",
    "No compatible Python was found on your system.": "未找到兼容的系统 Python。",
    "Python 3.10–3.12 required!": "需要 Python 3.10–3.12",
    "Requires:  Python 3.10 - 3.12, ~8 GB disk, internet": "需要 Python 3.10–3.12、磁盘空间和网络",
    "Click Install, then pick a folder for the Kimodo venv.": "点击安装，为独立环境选择目录。",
    "Leave blank to auto-detect from PATH / sibling venv": "留空时自动检测已配置的 Python 环境",
    "Install location (blank = default ~/.kimodo-venv):": "安装目录（留空使用默认目录）：",
    "HF Token (optional — set if model downloads stall):": "HF 令牌（可选，下载受限时填写）：",
    "System Python 3.10–3.12 (override auto-detect):": "系统 Python 3.10–3.12（手动指定）：",
    "Select your Python 3.10–3.12 executable:": "选择 Python 3.10–3.12 可执行文件：",
    "Or install Python from python.org:": "也可从 python.org 安装 Python：",
    "Download Python 3.12": "下载 Python 3.12", "Download Python 3.12 Installer": "下载 Python 3.12 安装程序",
    "Click below to download the Python 3.12 installer (Windows 64-bit).": "点击下方下载 Windows 64 位 Python 3.12。",
    'Run it, tick "Add Python to PATH".': '安装时勾选“Add Python to PATH”。',
    "On Windows: run the installer as Administrator.": "Windows 下按安装程序提示完成安装。",
    "Then restart Blender before clicking Retry Install.": "完成安装后重启 Blender，再重试。",
    "On Windows, restart your computer (not just Blender)": "若环境变量仍未生效，可重新登录 Windows",
    "so the new PATH takes effect.": "以使新的 PATH 生效。",
    "Really delete this directory?": "确定删除这个环境目录？",
    "It and everything inside it will be permanently removed.": "该目录及其中的环境文件将被永久删除。",
    "This cannot be undone.": "此删除操作无法撤销。",
    "Confirm deletion of the Kimodo virtual environment folder": "确认删除 Kimodo 独立环境目录",
    "Generate Motion": "生成动作", "Generate Mode": "生成方式", "Single Clip": "单段动作", "Timeline": "多段时间线",
    "Generate All Segments": "生成所有动作段", "Generate Selected": "生成所选动作段",
    "Generate Variations": "生成多个变体", "Variations": "变体数量",
    "Prompt": "动作描述", "Prompt:": "动作描述：", "Duration": "时长", "Duration (s)": "时长（秒）",
    "Seed": "随机种子", "Seeds": "各段种子", "Seed Mode": "种子模式", "Last Used Seed": "上次使用的种子",
    "Use Standard T-Pose": "使用标准 T 姿态", "Reuse Armature": "复用动作源骨架", "Reuse": "复用",
    "Output:": "输出：", "Format": "格式", "Manual Import": "导入已有动作", "Import BVH": "导入 BVH 动作",
    "Import BVH at Frame": "在指定帧导入 BVH", "BVH Path": "BVH 路径", "Last BVH Path": "最近 BVH 路径",
    "Set to 30 FPS": "设为 30 FPS", "Set Scene to 30 FPS": "设置场景帧率为 30 FPS",
    "Cancel": "取消", "⏹  Cancel": "取消", "Working…": "正在处理…",
    "History": "生成历史", "Show History": "展开生成历史", "Clear History": "清空历史记录",
    "Re-import BVH": "重新导入 BVH", "No generations yet.": "暂无生成记录。",
    "Start": "开始", "End": "结束", "Start F": "开始帧", "End F": "结束帧",
    "Start Frame": "开始帧", "End Frame": "结束帧", "Frame": "帧", "Timestamp": "生成时间",
    "Active History Entry": "当前历史记录", "Active Segment": "当前动作段",
    "Add": "添加", "Remove": "移除", "Add Segment": "添加动作段", "Remove Segment": "移除动作段",
    "Duplicate Segment": "复制动作段", "Select Segment": "选择动作段", "Move Up": "上移", "Move Down": "下移",
    "No segments yet.": "暂无动作段。", "Click Add to create one.": "点击添加，建立动作段。",
    "Transition Frames": "过渡帧数", "Transition Frames:": "过渡帧数：", "Sync Seeds": "同步随机种子",
    "Type": "类型", "Object": "对象", "Enabled": "启用", "Color": "颜色", "Label": "标签", "Index": "序号",
    "Root Waypoint": "根运动路径点", "Full-Body Pose": "全身姿态", "Left Hand": "左手", "Right Hand": "右手",
    "Left Foot": "左脚", "Right Foot": "右脚", "Root XZ": "根路径", "Full-Body": "全身姿态",
    "L.Hand": "左手", "R.Hand": "右手", "L.Foot": "左脚", "R.Foot": "右脚",
    "Add Constraint at Current Frame:": "在当前帧添加约束：", "Add Constraint Marker": "添加生成约束",
    "Remove Constraint": "移除生成约束", "Clear All": "清空", "Clear All Constraints": "清空生成约束",
    "Select Marker": "选择标记", "Go to Frame": "跳到约束帧", "Marker": "约束标记",
    "Delete Marker Object": "删除标记对象", "Preview JSON": "查看约束数据",
    "Preview Constraints JSON": "预览约束 JSON", "Constraint JSON": "约束 JSON",
    "Auto-Origin": "自动对齐原点", "Auto-Canonicalize": "自动对齐原点", "Include Heading": "约束朝向",
    "Heading": "朝向", "Heading (°)": "朝向（°）", "Kimodo FPS": "Kimodo 帧率",
    "Full-Body tip:": "全身姿态提示：", "Select an armature first, then click Full-Body.": "先选择骨架，再添加全身姿态。",
    "Or generate once — source arm will be duplicated.": "也可先生成动作，再使用动作源骨架。",
    "Select an armature above then click Full-Body again": "请先指定骨架，再添加全身姿态",
    "No constraints — motion is unconstrained": "未添加约束，将按动作描述生成",
    "Sample Curve as Waypoints": "将曲线采样为路径点", "Path Curve": "路径曲线", "Curve": "曲线",
    "Draw": "绘制", "Draw Curve": "绘制路径", "Points": "采样点数", "Waypoints": "路径点数",
    "Link Selected as Constraint": "将所选对象设为约束",
    "Armatures": "角色骨架", "Source (Kimodo)": "动作源骨架", "Target (Your Rig)": "目标角色骨架",
    "Source Armature": "动作源骨架", "Target Armature": "目标角色骨架", "Source Bone": "源骨骼", "Target Bone": "目标骨骼",
    "Root Bone": "位移承接骨骼", "Root Bone (Target)": "目标位移骨骼", "Bone Mapping:": "骨骼映射：",
    "Auto-Match Bones": "自动匹配骨骼", "Add Bone Pair": "添加骨骼映射", "Remove Bone Pair": "移除骨骼映射",
    "Mode": "方式", "Inherit Rotation": "继承旋转", "Apply Constraints": "预览重定向",
    "Apply Retargeting": "预览重定向", "Remove Constraints": "恢复原动作",
    "Bake & Remove Constraints": "保存为独立动作", "Bake Animation": "保存重定向动作",
    "Bone Map Presets": "骨骼映射预设", "Preset Name": "预设名称", "Saved Presets": "已保存预设",
    "Save Preset": "保存预设", "Load Preset": "加载预设", "Delete Preset": "删除预设",
    "Export to File": "导出预设", "Import from File": "导入预设", "Export Bone Map": "导出骨骼映射",
    "Import Bone Map": "导入骨骼映射", "Copy Rotation": "复制旋转", "Copy Transforms": "复制变换",
    "Child Of": "父子约束", "Child Of (Rotation)": "父子约束（仅旋转）",
    "Quick Start:": "使用步骤：", "Docs & Source:": "文档与源码：",
    "1. Click 'Install Kimodo (Auto)' in the Connection panel": "1. 在模型准备中导入 PMX 并自动修复",
    "   (or point Kimodo Python at your own venv)": "2. 配置独立的 Kimodo Python 环境",
    "2. Start Kimodo": "3. 启动 Kimodo，生成或导入 BVH 动作",
    "   (model loads once, stays loaded)": "   模型加载后可连续生成动作",
    "3. Enter prompt → Generate Motion": "4. 输入动作描述并生成动作",
    "4. In Retarget tab, Pick source + target rigs": "5. 指定动作源骨架与目标角色骨架",
    "5. Auto-Match → Apply Constraints": "6. 自动匹配骨骼，预览重定向",
    "6. If it does not match, manually add your control bones": "   检查并修正必要的骨骼映射",
    "7. Click Apply Constraints": "7. 检查动作姿态、位移和腿部控制",
    "8. Bake when satisfied": "8. 保存为独立动作，或恢复原动作",
    "Not started": "尚未启动", "Stopped": "已停止", "Ready": "已就绪", "Starting…": "正在启动…",
    "Launching…": "正在启动进程…", "Loading…": "正在加载…", "Installed successfully": "安装完成",
    "Standard human body skeleton": "标准人形骨架", "Standard human SOMA skeleton (recommended)": "标准 SOMA 人形骨架（推荐）",
    "One prompt, one motion clip": "一段描述生成一个动作", "Multiple prompt segments stitched into one animation": "将多段描述合成为连续动作",
    "Text description of the motion to generate": "描述需要生成的人体动作，建议使用英文或双语预设",
    "Text description of the motion for this segment": "本动作段的动作描述",
    "Length of the generated motion in seconds": "需要生成的动作时长，单位为秒",
    "What happens to the seed after each generation": "每次生成后如何处理随机种子",
    "First frame of this motion segment": "本动作段的开始帧", "Last frame of this motion segment": "本动作段的结束帧",
    "Bone name in the Kimodo-generated armature": "生成动作源骨架中的骨骼名称",
    "Bone name in your target armature": "目标角色骨架中的骨骼真实名称",
    "Your character's armature to drive with the motion": "需要应用动作的目标角色骨架",
    "The Kimodo-generated armature (imported from BVH)": "从 BVH 导入的动作源骨架",
    "Include this bone in retargeting": "将本骨骼映射用于重定向",
    "Include this constraint in generation": "生成时使用本约束", "Include this segment in generation": "生成时使用本动作段",
    "Currently selected motion segment": "当前选中的动作段", "Expand / collapse the generation history list": "展开或折叠生成历史",
    "Number of random-seed variations to generate": "使用不同随机种子生成的动作数量",
    "Number of blended frames between segments in multi-prompt generation": "多段动作之间用于过渡的帧数",
    "Done ✓": "完成 ✓", "Failed ✗": "失败 ✗", "Cancelled": "已取消", "Cancelling…": "正在取消…",
    "Saving combined output file…": "正在保存合并动作…",
    "Pre-encoding text prompt (CPU Offload)...": "正在编码动作描述（内存卸载）…",
    "Pre-encoding text prompts (CPU Offload)...": "正在编码多段动作描述（内存卸载）…",
    "Kimodo is already running.": "Kimodo 已在运行。", "Kimodo bridge stopped.": "Kimodo 已停止。",
    "Kimodo is not running — click 'Start Kimodo' first.": "请先点击“启动 Kimodo”。",
    "Already generating — please wait.": "正在生成动作，请稍候。", "Already generating.": "正在生成动作。",
    "Generation cancelled — result discarded.": "生成已取消，本次结果已丢弃。",
    "Nothing is generating.": "当前没有正在生成的动作。",
    "No generation was running — state reset.": "当前没有生成任务，状态已重置。",
    "Cancellation requested — result will be discarded.": "已请求取消，本次生成结果将被丢弃。",
    "BVH imported but no armature found in scene.": "BVH 已导入，但场景中未找到骨架。",
    "Set the Source Armature first.": "请先指定动作源骨架。", "Set Source Armature.": "请指定动作源骨架。",
    "Set the Target Armature first.": "请先指定目标角色骨架。", "Set Target Armature.": "请指定目标角色骨架。",
    "No bone mappings defined. Use Auto-Match or add manually.": "尚无骨骼映射，请先自动匹配或手动添加。",
    "Enter a preset name first.": "请先填写预设名称。", "File does not contain a JSON array.": "文件中不含有效的 JSON 数组。",
    "No segment selected.": "尚未选择动作段。", "No enabled segments.": "没有启用的动作段。",
    "Segment frame ranges adjusted to be contiguous (no gaps/overlaps).": "已将动作段调整为连续帧范围。",
    "Select an object first.": "请先选择对象。", "No object linked to this constraint.": "这个约束尚未关联对象。",
    "No Kimodo-generated armatures found in scene": "场景中没有 Kimodo 动作源骨架。",
    "Invalid history index.": "历史记录序号无效。", "Generation history cleared.": "生成历史已清空。",
    "All constraints cleared.": "生成约束已清空。", "Scene FPS set to 30.": "场景帧率已设为 30 FPS。",
    "Set a curve object in the Path Curve field.": "请先在路径曲线中指定曲线对象。",
    "Start Frame must be less than End Frame.": "开始帧必须早于结束帧。",
    "Could not sample any points from the curve.": "无法从这条曲线采样路径点。",
    "Draw tool active! Sketch a path in the 3D Viewport, then click 'Sample Curve' when done.": "路径绘制工具已启用；在视口绘制后，点击“将曲线采样为路径点”。",
    "Full-Body constraint needs an armature. Either: (a) select an armature first, or (b) generate a motion first so a source armature exists to duplicate.": "全身姿态约束需要骨架；请先选择骨架，或先生成动作以复制动作源骨架。",
    "⚠ Not an armature!": "所选对象不是骨架", "Fix →": "更正 →", "Or set →": "或指定 →",
    "e.g. /usr/bin/python3.12  or  C:\\Python312\\python.exe": "例如 /usr/bin/python3.12 或 C:\\Python312\\python.exe",
    "Path to the Python 3.10–3.12 executable (python3.12 / python.exe) used to create the Kimodo venv. Select the executable file, not a folder. Leave blank to auto-detect from PATH.": "用于创建独立环境的 Python 3.10–3.12 可执行文件；请选择程序文件，留空时从 PATH 检测",
    "Kimodo installation started — watch the Connection panel.": "Kimodo 安装已开始，可在“Kimodo 环境”中查看进度。",
    "Installation is already in progress.": "正在安装，请稍候。", "Managed Kimodo venv already exists.": "独立 Kimodo 环境已存在。",
    "Cannot reset while installation is in progress.": "安装过程中无法重置环境。",
    "No venv found — nothing to reset.": "未找到可重置的独立环境。",
    "Number of evenly-spaced waypoints to sample from the curve": "沿曲线均匀采样的路径点数量",
    "Timeline frame for the first waypoint": "首个路径点所在帧", "Timeline frame for the last waypoint": "最后路径点所在帧",
    "Name to save / load bone mapping preset": "用于保存和加载骨骼映射预设的名称",
    "Path of the most recently imported motion file": "最近导入的动作文件路径",
    "Kimodo model to load into the bridge process": "桥接进程需要加载的 Kimodo 模型",
    "Enable CPU/RAM/VRAM offloading for low-memory GPUs (e.g. <= 8GB)": "显存不足时在 CPU、内存和显存之间卸载模型",
    "Export BVH with standard T-pose rest pose instead of BONES-SEED pose (SOMA models only)": "使用标准 T 姿态导出 SOMA BVH，便于姿态校准",
    "Base seed used in FIXED / INCREMENT / DECREMENT modes (RANDOM ignores it)": "固定、递增或递减模式使用的随机种子；随机模式自动产生新种子",
    "Don't edit — keep this exact seed for every generation": "固定使用同一个随机种子",
    "Increase the seed by 1 after each generation (+1)": "每次生成后将种子加 1",
    "Decrease the seed by 1 after each generation (-1)": "每次生成后将种子减 1",
    "Use a new random seed for every generation": "每次生成使用新的随机种子",
}

PATTERNS = [
    (r"Kimodo ready: Ready — (.+) on (.+) \((\d+) fps\)", r"Kimodo 已就绪：\1 · \2 · \3 FPS"),
    (r"Ready — (.+) on (.+) \((\d+) fps\)", r"已就绪：\1 · \2 · \3 FPS"),
    (r"Kimodo failed to start: (.*)", r"Kimodo 启动失败：\1"),
    (r"Motion generated and imported from (.*)", r"动作已生成并导入：\1"),
    (r"Motion generated \((.*)\) but BVH import failed — see error above\.", r"动作已生成（\1），但 BVH 导入失败，请查看错误提示。"),
    (r"Motion saved to (.*) \(NPZ — import manually\)", r"NPZ 动作已保存至 \1，需要另行处理。"),
    (r"Generation failed: (.*)", r"动作生成失败：\1"),
    (r"Preset '(.*)' saved \((\d+) bone pairs\)", r"预设“\1”已保存，共 \2 组骨骼映射"),
    (r"Loaded preset '(.*)' \((\d+) bone pairs\)", r"已加载预设“\1”，共 \2 组骨骼映射"),
    (r"Deleted preset '(.*)'", r"已删除预设“\1”"),
    (r"Preset '(.*)' not found\.?", r"未找到预设“\1”"),
    (r"Exported (\d+) bone pairs to (.*)", r"已导出 \1 组骨骼映射至 \2"),
    (r"Imported (\d+) bone pairs from (.*)", r"已导入 \1 组骨骼映射，来源：\2"),
    (r"Export failed: (.*)", r"导出失败：\1"), (r"Import failed: (.*)", r"导入失败：\1"),
    (r"BVH file no longer exists: (.*)", r"BVH 文件已不存在：\1"),
    (r"Re-imported '(.*)'", r"已重新导入“\1”"),
    (r"Reuse target set to '(.*)'", r"已将复用动作源设为“\1”"),
    (r"Updated (\d+) segments with seed (\d+)", r"已将 \1 个动作段的种子设为 \2"),
    (r"Generating: (.*)", r"正在生成：\1"),
    (r"Generating (\d+) segments as multi-prompt sequence…", r"正在合成 \1 个动作段…"),
    (r"All (\d+) segments generated ✓", r"\1 个动作段已生成 ✓"),
    (r"Multi-prompt generation complete \((\d+) segments\) ✓", r"多段动作生成完成，共 \1 段 ✓"),
    (r"Segment '(.*)' generated ✓", r"动作段“\1”已生成 ✓"),
    (r"NPZ saved to (.*)", r"NPZ 已保存至 \1"),
    (r"Variation (\d+)/(\d+)…", r"正在生成变体 \1/\2…"),
    (r"Variation (\d+) failed ✗", r"变体 \1 生成失败 ✗"),
    (r"Variation (\d+) failed: (.*)", r"变体 \1 生成失败：\2"),
    (r"All (\d+) variations done ✓", r"\1 个变体已生成 ✓"),
    (r"Generated (\d+) variations ✓", r"已生成 \1 个变体 ✓"),
    (r"Variations cancelled after (\d+) of (\d+)\.", r"变体生成已取消，已完成 \1/\2。"),
    (r"Running multi-prompt diffusion \((\d+) segments, (\d+) steps\).*", r"正在合成多段动作（\1 段，\2 步）…"),
    (r"Pose Ref  \((\d+) bones\)", r"姿态参考（\1 根骨骼）"),
    (r"Added (\d+) path waypoints \(frames (\d+)–(\d+)\)", r"已添加 \1 个路径点，帧范围 \2–\3"),
    (r"Constraints JSON written to Text Editor: '(.*)'", r"约束数据已写入文本编辑器：\1"),
    (r"Constraint build failed \(generating without\): (.*)", r"生成约束构建失败，本次未使用这些约束：\1"),
    (r"Failed to build JSON: (.*)", r"约束数据构建失败：\1"),
    (r"Python path set to: (.*)", r"Python 路径已设为：\1"),
    (r"Managed venv not found at (.*)", r"未找到独立环境：\1"),
    (r"Could not remove (?:partial )?venv: (.*)", r"独立环境删除失败：\1"),
    (r"Removed (.*) — ready for a fresh install\.", r"已删除环境 \1，可以重新安装。"),
    (r"Ready (.*)", r"已就绪 \1"),
    (r"Loading (.*)", r"正在加载 \1"),
    (r"Importing Kimodo.*", r"正在导入 Kimodo…"),
    (r"Running diffusion \((\d+) steps\).*", r"正在生成动作（\1 步）…"),
    (r"Saving output file.*", r"正在保存动作文件…"),
    (r"History \((\d+)\)", r"生成历史（\1）"),
    (r"Generate (\d+) Variations", r"生成 \1 个变体"),
    (r"Sample (\d+) Waypoints", r"采样 \1 个路径点"),
    (r"Scene is (.+) FPS — Kimodo needs 30 FPS", r"当前场景 \1 FPS；导入时自动换算动作时间"),
    (r"(\d+) constraints?:", r"\1 个生成约束："),
    (r"Error: (.*)", r"错误：\1"),
    (r"Failed to (.*)", r"操作失败：\1"),
    (r"File not found: (.*)", r"文件不存在：\1"),
    (r"Imported '(.*)' with (\d+) bones", r"已导入动作源“\1”，共 \2 根骨骼"),
]


def zh(text):
    if not isinstance(text, str):
        return text
    if text in ZH:
        return ZH[text]
    variation = re.fullmatch(r"Variation (\d+)/(\d+): (.*)", text)
    if variation:
        return f"变体 {variation[1]}/{variation[2]}：" + zh(variation[3])
    for pattern, replacement in PATTERNS:
        if re.fullmatch(pattern, text):
            return re.sub(pattern, replacement, text)
    return text


def report(operator, levels, message):
    operator.report(levels, zh(message))


class _Layout:
    """Only display text is translated; data identifiers are passed untouched."""
    def __init__(self, layout):
        object.__setattr__(self, "_layout", layout)

    def __getattr__(self, name):
        attr = getattr(self._layout, name)
        if not callable(attr):
            return attr
        def call(*args, **kwargs):
            if "text" in kwargs:
                kwargs["text"] = zh(kwargs["text"])
            result = attr(*args, **kwargs)
            return ui(result) if isinstance(result, bpy.types.UILayout) else result
        return call

    def __setattr__(self, name, value):
        setattr(self._layout, name, value)


def ui(layout):
    return layout if isinstance(layout, _Layout) else _Layout(layout)


def localize_class(cls):
    for attribute in ("bl_label", "bl_description"):
        if attribute in cls.__dict__:
            setattr(cls, attribute, zh(getattr(cls, attribute)))
    if issubclass(cls, bpy.types.Operator) and "bl_description" not in cls.__dict__:
        label = getattr(cls, "bl_label", "")
        original = cls.__doc__ or ""
        cls.bl_description = zh(original) if original in ZH else label
    for deferred in getattr(cls, "__annotations__", {}).values():
        keywords = getattr(deferred, "keywords", None)
        if keywords is None:
            continue
        for key in ("name", "description"):
            if key in keywords:
                keywords[key] = zh(keywords[key])
        items = keywords.get("items")
        if isinstance(items, (list, tuple)):
            keywords["items"] = [(item[0], zh(item[1]), zh(item[2]), *item[3:]) if item else item for item in items]
    return cls


def register():
    dictionary = {(context, source): value for source, value in ZH.items() for context in ("*", "Operator")}
    bpy.app.translations.register(__package__, {"zh_HANS": dictionary, "zh_CN": dictionary})


def unregister():
    bpy.app.translations.unregister(__package__)
