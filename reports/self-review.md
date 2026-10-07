# 自检与验证记录

日期：2026-10-07（Asia/Shanghai）。这是 skill 与工程脚本交付的验证，
不是任何实际业务 R package 的 CRAN acceptance 证明。

## 重复、矛盾与遗漏

| 自检维度 | 结果与处理 |
| --- | --- |
| 内容重复 | SKILL.md 只保留硬性约束、阶段入口和 reference 路由；阶段细节集中 workflow；编码、测试文档、readiness、错误定位各有独立职责。README 是用户安装/运行说明，不作为第二套工程规则 |
| 阶段重复执行 | 记录完成证据和变更失效规则；已有 package 禁止重建 scaffold；旧日志不能证明当前 tarball |
| 安装依赖的规则 | Package runtime、tests/examples/vignettes 禁止安装；仓库 CI 的开发环境 provision 可以安装，明确区分执行位置 |
| namespace/helper | 明确区分 intentional exports 与 unexported helpers；禁止宽泛 exportPattern；测试验证 helper 不在 namespace exports 中 |
| API 与错误处理 | 契约先行、兼容性、边界验证、可恢复条件、全局状态/资源清理均有规则；不新增无必要依赖 |
| 文档与 tests | 覆盖 testthat、roxygen2、生成 namespace/Rd、Runnable examples、数据/方法文档、Rmd vignettes；vignette 按功能需要生成，用户明确要求则必须完成 |
| 技术验收 | 默认 full as-CRAN；development 模式明确降级；NOTE 返回非零状态；缺少产物或最终 Status 不可能自动通过 |
| CRAN readiness | metadata/license、artifact/hash、platform/R-devel、native code、reverse dependencies、submission notes 和当前 policy 检查均有 checklist；prepare 与 upload 分离 |
| 自动化边界 | AST preflight 不能证明动态调用、别名、NSE、optional guards、native code、复杂 chunks 或 API 语义。完整 check/人工审查补足，README 和脚本帮助明确说明 |

未发现阻碍交付的规则矛盾或用户要求遗漏。自动化覆盖与 Codex 行为评测的
限制仍存在，见下面证据与下一步计划；这不等于声称所有未来 package 都已验证。

## 已执行验证

- skill-creator 自带 `quick_validate.py`：通过。
- 本仓库 `validate_skill.py`：通过；YAML、name、description、内部 Markdown
  链接、UI prompt 和 Python 语法无错误。
- Python unittest：7 项测试方法通过，含多组参数化 case；覆盖非空目录
  拒绝且文件不变、metadata 注入拒绝、作者字符串转义、license 分支、artifact
  不污染 source、Status 解析、NOTE/中断/development/full 的验收状态和破损链接。
- Windows / R 4.4.3 / Python 3.14：真实 `smoke_check.py --vignette` 通过。
  包含 scaffold、roxygen2、6 个 testthat assertions、examples、内部 helper
  隔离、Rmd vignette、`R CMD build` 和 installed-package tests。
- 静态负例：直接/qualified setwd、install.packages、runtime library、未声明
  namespace、外部 :::、R 语法错误、roxygen example 和 Rmd chunk 违规均被拒绝；
  注释和字符串中的调用文本被正确忽略。
- 修正了实际试运行发现的缺省参数 AST 遍历、空 examples Rd 提取、Windows
  version 输出、UTF-8 输出解码、旧 R locale 和 NEWS numeric header 问题。

最新本地开发 smoke 的 artifact：

```text
.artifacts/smoke space-zb1cakns/checks/run-ufte6h2o/summary.json
R CMD check --as-cran --no-manual
ERROR 0 / WARNING 0 / NOTE 2
SHA-256 ea8ef25318bb6a4696a664b5eb855998e52c54e33bdd1bdcd9ec401b35ade971
```

两个 NOTE：测试 fixture 是新 submission 且版本 `0.0.0.9000` 含较大组件；
检查服务无法验证当前时间。记录来自真实 log，未关闭 incoming/time 检查。
`check_package.py` 返回 1，`final_acceptance` 为 false；smoke 只验证工程机制，
对这些明确列出的 fixture NOTE 类别进行断言，不替实际 package 豁免 NOTE。

另执行了一次默认 full as-CRAN 分支，验证不跳过 PDF manual：
`.artifacts/full-check/run-kyckngnm/summary.json`。本机缺少 LaTeX，检查出现
ERROR/WARNING，脚本保留日志并返回 1，没有误报通过。该次使用前一轮 fixture，
还包含已修正的 NEWS NOTE；不得把它当作最新业务 package 的检查证据。

GitHub Actions 配置覆盖 Linux/Windows/macOS、release R、Python 3.12 和 vignette
smoke，保留各平台 artifact。远端运行状态以对应 commit 的 Actions 记录为准。
CI 默认 no-manual，因此绿色基础 CI 仍不能证明完整 CRAN readiness。

## 下一步

优先执行 [行为测试计划](../tests/behavioral-plan.md) 中的新 idea、已有 package
bug fix 和 check 诊断场景；然后测试依赖、vignette、变更失效与 readiness。
在有完整工具链的隔离环境补充 full manual 与 R-devel；按实际 package 类型
扩展 native code、S3/S4 和 reverse-dependency 证据。

参考知识链接已按当前官方来源检查：
[Writing R Extensions](https://cran.r-project.org/doc/manuals/r-release/R-exts.html)、
[CRAN policy](https://cran.r-project.org/web/packages/policies.html)、
[roxygen2 namespace](https://roxygen2.r-lib.org/articles/namespace.html)、
[testthat fixtures](https://testthat.r-lib.org/articles/test-fixtures.html)、
[OpenAI skill 安装说明](https://learn.chatgpt.com/docs/build-skills)。
提交前仍要求重新核对 CRAN 的实时规则。
