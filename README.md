# r-package-engineer

一个用于 R package 工程工作的 Agent Skill：从 idea、architecture、scaffold，
到 implementation、tests、documentation、`R CMD check` 和 CRAN readiness。
既支持从零开发，也支持已有 package 的维护、API 修改和 check 问题修复。

它先识别当前阶段，只补充缺失或因修改失效的工作。入口保持简短；工程规则、
文档与提交知识按需加载；脚本负责可重复的操作。公共 API 小而稳定，内部 helper
不自动导出。最终技术验收来自构建后 tarball 的完整 `R CMD check --as-cran`。

## 安装

仓库中的 **`r-package-engineer/` 才是可安装的 skill 目录**，不要把整个仓库当成 skill。
根据 [OpenAI 官方技能说明](https://learn.chatgpt.com/docs/build-skills)，可放到
用户级 `~/.agents/skills/` 或目标项目的 `.agents/skills/`。

Windows PowerShell，先克隆，然后复制到用户级目录：

```powershell
git clone https://github.com/diamondten8/r-package-engineer-skill.git
$skillSource = Join-Path (Get-Location) 'r-package-engineer-skill\r-package-engineer'
$skillParent = Join-Path $env:USERPROFILE '.agents\skills'
$skillTarget = Join-Path $skillParent 'r-package-engineer'
if (Test-Path -LiteralPath $skillTarget) { throw '目标 skill 已存在，请先检查旧版本。' }
New-Item -ItemType Directory -Force -Path $skillParent | Out-Null
Copy-Item -LiteralPath $skillSource -Destination $skillTarget -Recurse
```

macOS/Linux：

```sh
git clone https://github.com/diamondten8/r-package-engineer-skill.git
mkdir -p ~/.agents/skills
test ! -e ~/.agents/skills/r-package-engineer && \
  cp -R r-package-engineer-skill/r-package-engineer ~/.agents/skills/
```

项目级安装时，改为复制到目标 R 项目的 `.agents/skills/r-package-engineer/`。
复制后在 Codex 新会话中检查 skill 是否可选。更新时检查本地修改后替换安装副本；
普通 `git pull` 不会自动更新已经复制的目录。本次仓库交付不修改用户级 skill 安装。

## 使用

在 Codex 中输入：

```text
使用 $r-package-engineer，将这个 idea 设计成 R package，先确定最小公共 API。
使用 $r-package-engineer，检查当前 package 的阶段，继续完成测试、文档和 check。
使用 $r-package-engineer，修复 00check.log 中的问题，并准备 CRAN readiness 记录。
```

无需提前加载全部 references。Skill 允许默认的自动匹配，也支持上述显式调用。
准备 CRAN submission 不等于已经提交；真正上传需用户明确要求。

## 脚本与环境

- Python 3.10+：scaffold/check 只用标准库。
- R/Rscript：static validation 只用 base R 和随 R 附带的 tools；check 需要 R。
- 开发环境：roxygen2、testthat；Rmd vignette 还需 knitr、rmarkdown 和 Pandoc。
  完整 PDF manual 检查需要适合 R 文档的 LaTeX 工具；编译型 package 另需相应工具链。
- Skill 结构验证另需 `PyYAML>=6,<7`。开发依赖在独立环境或 CI 中配置，
  package 代码和这些工程脚本都不会自动安装依赖。

以下命令从本仓库根目录执行；安装后把脚本路径换成实际 skill 目录。
请用真实作者、邮箱、描述和确认过的许可证替换示例身份。

```sh
python r-package-engineer/scripts/scaffold.py /absolute/path/newpkg \
  --name newpkg --title "Small Numeric Tools" \
  --description "Provides deterministic transformations for numeric vectors." \
  --given "Given" --family "Family" --email "maintainer@example.org" \
  --license MIT --vignette

Rscript --vanilla r-package-engineer/scripts/validate_package.R /absolute/path/newpkg
Rscript --vanilla -e 'roxygen2::roxygenise(commandArgs(TRUE)[1])' /absolute/path/newpkg
python r-package-engineer/scripts/check_package.py /absolute/path/newpkg \
  --output /absolute/path/check-artifacts
```

PowerShell 的多行命令需用其续行语法，或把上述命令写为单行。
scaffold 接受 MIT 或 GPL-3；其他许可证按项目需求手工配置。脚手架没有虚构公共
功能与测试，需要实现实际 API、添加行为测试并生成文档，才能期待 check 通过。
它拒绝非空目标，不能用于重建已有 package。

`validate_package.R` 检查 metadata、直接禁用调用、未声明的 `::` namespace、
宽泛导出、R 语法、roxygen/Rd examples 和常见 Rmd R chunks。注释和字符串不会被
当成可执行调用。ERROR 退出 1，WARN 为需要人工审查的建议。动态调用、别名、NSE、
内联/Sweave chunks、native code、API 语义和 optional dependency guard 仍需审查。

`check_package.py` 不替代 roxygen2，也不执行 CRAN 上传。它在外部 artifact 目录
新建独立 `run-*`，执行 build 和 check，保留原始日志、tarball、SHA-256、R 版本、
locale 和 summary.json。ERROR/WARNING/NOTE 都退出 1；中断或缺失关键产物退出 2。
完整无 findings 的运行才标记技术通过；自定义 `_R_CHECK_*` 环境需审查，不能自动
标记最终验收。被合理解释的 NOTE 由工程记录保留，脚本不自行豁免。

默认执行完整 `--as-cran`。`--development` 只跳过 PDF manual，始终标记为开发检查。
不能用它声称 CRAN ready。Windows 的旧 R 可能不支持 Unix `C.UTF-8`；可用
`--locale English_United States.utf8` 指定可用 locale，仅影响子进程。
`--r` 和 `--rscript` 支持路径含空格的可执行文件。

## 目录与职责

```text
r-package-engineer-skill/
├── README.md                         安装、使用、结构和验证入口
├── LICENSE                           保留仓库原有 MIT 许可证
├── .gitignore                        排除开发环境和生成产物
├── .gitattributes                    文本换行约定
├── .github/workflows/validate.yml     三平台基础验证与 artifact 上传
├── r-package-engineer/
│   ├── SKILL.md                       阶段识别、核心约束、按需路由、验收
│   ├── agents/openai.yaml             显示名称、简介和调用提示
│   ├── references/
│   │   ├── workflow.md                阶段 gate、完成证据、失效规则
│   │   ├── coding-practices.md         API、helper、依赖、错误与状态规则
│   │   ├── testing-documentation.md   行为测试、roxygen2、examples、vignettes
│   │   ├── cran-readiness.md           提交前 checklist 和证据记录
│   │   └── check-errors.md             常见 check finding 的定位和修复
│   └── scripts/
│       ├── _common.py                 R 定位、子进程环境、日志共用逻辑
│       ├── scaffold.py                仅创建新 package，不覆盖已有文件
│       ├── validate_package.R         不执行 package 源码的静态预检
│       ├── check_package.py           tarball build/check、摘要和退出状态
│       └── validate_skill.py          YAML、名称、链接和 Python 语法检查
├── tests/
│   ├── test_scripts.py                防覆盖、注入、验收状态等回归测试
│   ├── smoke_check.py                 真实 R package 流程与失败用例
│   └── behavioral-plan.md             下一步 Codex 行为测试场景与通过标准
└── reports/
    └── self-review.md                 本次重复/矛盾/遗漏审查与验证证据
```

开发期间 `.venv/` 和 `.artifacts/` 是本地生成目录，不提交，也不属于安装 bundle。

## 本地验证与 CI

```sh
python -m venv .venv
# 激活此独立环境后：
python -m pip install 'PyYAML>=6,<7'
python r-package-engineer/scripts/validate_skill.py r-package-engineer
python -m unittest discover -s tests -p 'test_*.py' -v
python tests/smoke_check.py --vignette
# 具备完整文档工具链时再运行：
python tests/smoke_check.py --vignette --full
```

CI 在 Linux、Windows、macOS 上运行结构验证、回归测试，以及含真实函数、内部 helper、
tests、examples 和 Rmd vignette 的 scaffold → roxygen2 → build → check smoke。
CI 环境配置阶段可以安装工具；此处与 package 运行时禁止安装依赖的规则不冲突。
Smoke 检查默认跳过 PDF manual，且仅容许测试 fixture 中明确列出的 NOTE 类别；
`check_package.py` 本身仍对 NOTE 返回非零状态。绿色 CI 只证明这些基础工程路径，
不代表任意未来 package 已通过完整 CRAN 验收。

本次结果见 [自检报告](reports/self-review.md)，后续测试见
[行为测试计划](tests/behavioral-plan.md)。工程参考以
[Writing R Extensions](https://cran.r-project.org/doc/manuals/r-release/R-exts.html)、
[当前 CRAN policy](https://cran.r-project.org/web/packages/policies.html)、
[roxygen2 文档](https://roxygen2.r-lib.org/articles/namespace.html) 为准。
