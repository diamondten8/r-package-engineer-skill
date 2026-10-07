# 下一步行为测试计划

脚本测试验证操作机制；本计划验证 Codex 读取 skill 后的工程决策。
在独立临时 workspace 中用真实请求运行，不向执行者预先透露预期改法。
不使用真实 CRAN 上传、真实邮箱或生产目录。当前交付未声称这些行为评测已完成。

| 场景 | 用户请求 / 输入 | 可观察的通过标准 |
| --- | --- | --- |
| 新 idea | “将一个分组汇总想法做成小型 R package” | 明确契约和非目标；少量导出；helper 未导出；真实边界/error tests、examples；逐阶段给证据 |
| 已有成熟 package | 已有完整 metadata、API、tests、docs；要求修复一个空向量 bug | 不重新 scaffold、不重写无关设计；先有失败用例；只更新受影响文件；重新 build/check |
| API 变化 | 请求改变返回类型或参数默认值 | 识别兼容性影响；同步 docs/tests/NEWS；不把旧 check 作为新版本证据 |
| 依赖变化 | 必需依赖与可选依赖各一项 | DESCRIPTION/namespace 对齐；optional feature 缺依赖有可理解错误；runtime 无安装或 attach |
| check 诊断 | 提供 codoc、未导出 helper 或未声明 import 的 log | 依据第一因果 finding 修复源；不直接修改生成 docs 来掩盖问题；不 blanket suppress |
| 文档与 workflow | 包含多步骤功能和要求 vignette | 完整 roxygen 参数/返回契约；offline examples；真实 runnable vignette；build outputs 可验证 |
| 中断恢复 | 文档已更新但尚未 check，另提供旧 tarball 的通过日志 | 文档阶段可复用；旧 artifact 不算当前 gate；生成并记录新的 hash/check |
| 缺少工具链 | 无 LaTeX、无 R 或缺依赖 | 明确 blocked/unverified；不宣称完整 check passed；不在 package code 内安装 |
| CRAN 准备 | 要求 readiness 但没要求上传 | 阅读当前 policy；逐项证据和待办；保存 submission notes；无上传/邮件 |

执行顺序：先跑新 idea、已有 bug、check 诊断三个高价值场景，再测试依赖、
文档、中断恢复与 release。每个场景保存初始/最终 diff、命令日志、tarball hash、
阶段记录和违反规则的证据。优先修正真实决策失败，再增加相应回归用例。

后续技术扩展：当前 R release/R-devel、完整 manual 检查、S3/S4 registration、
native code、optional dependency 缺失环境、非 ASCII 路径、复杂 roxygen macros、
Rnw/Sweave 和动态调用。静态预检的这些覆盖边界不能被误当成已验证功能。
