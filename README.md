# pku-semester-toolkit

一个面向大学生日常学习的 Windows 本地工具箱。目前已完成命令行菜单、PDF 工具、课程文件整理、Deadline 管理、成绩计算器和 LaTeX 作业模板。Python 工具日常运行不需要联网。文件操作默认保留原件，输出重名时自动使用新文件名。

## 当前能做什么

运行 `python main.py` 后，输入 `1` 使用 PDF 工具：

- 按输入顺序合并两个或更多 PDF。
- 将 PDF 逐页拆成独立文件，或提取连续页码到一个新 PDF。页码从 1 开始，包含结束页。
- 将 JPG、JPEG、PNG 或 BMP 图片按输入顺序转为一个 PDF；每张图片占一页。
- 将 PDF 与上述图片按输入顺序合并成扫描作业；PDF 原有的所有页面会在该位置依次加入。

输入 `2` 可整理课程文件：先预览分类，输入 `y` 后才复制。输入 `3` 可记录和查看作业。输入 `4` 可计算当前成绩，并反推达到目标总评所需的期末分数。

`templates/homework-template.tex` 是数学 / 经济学作业模板，`examples/example-homework.tex` 是完整示例；它们是独立的 `.tex` 文件，无需进入 CLI 菜单。

## Windows 安装与运行（PowerShell）

建议使用 Python 3.11 或更新版本。先打开 PowerShell，逐行执行：

```powershell
py -3 --version
```

如果显示的版本低于 3.11，先从 Python 官网安装新版本，并在安装时勾选将 Python 加入 PATH。接着进入项目目录；如果你后来移动了项目，请把这一行改成实际路径：

```powershell
cd "C:\Users\JINZHIXUN\Documents\Codex\pku-semester-toolkit"
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

`venv` 是项目专用的 Python 环境，避免不同项目之间的包互相影响。安装命令会下载两个依赖：

- [`pypdf`](https://pypdf.readthedocs.io/en/stable/)：读取、合并和拆分 PDF。
- [`Pillow`](https://pillow.readthedocs.io/en/stable/)：读取图片，并将图片写入 PDF。

版本固定在 `requirements.txt` 中，便于复现已测试的环境。退出虚拟环境可运行 `deactivate`。

以后再次运行时，只需要：

```powershell
cd "C:\Users\JINZHIXUN\Documents\Codex\pku-semester-toolkit"
.\.venv\Scripts\Activate.ps1
python main.py
```

如果你使用命令提示符（CMD），激活命令换成 `.venv\Scripts\activate.bat`；其余命令相同。也可以不激活，直接运行 `.\.venv\Scripts\python.exe main.py`。

**以后最省事的启动方式：**在文件资源管理器中打开项目文件夹，双击 `start-toolkit.cmd`，即可进入同一个菜单。它会自动使用项目的 `.venv`，无需先打开 PowerShell 或激活环境。首次使用仍需先按上面的步骤安装 Python 依赖；如果 `.venv` 不存在，启动文件会提示查看 README。

## 使用示例

```text
=== PKU Semester Toolkit ===
1. PDF 工具
2. 整理课程文件
3. 作业 / Deadline
4. 成绩计算器
5. 查看使用帮助
6. 退出
请选择（1-6）：1
--- PDF 工具 ---
1. 合并多个 PDF
2. 拆分 PDF
3. 图片转 PDF
4. 按指定顺序合并扫描作业（PDF / 图片）
5. 返回主菜单
请选择（1-5）：1
按目标顺序逐行输入文件路径；直接按 Enter 结束。
文件 1：C:\Users\JINZHIXUN\Desktop\HW\page 1.pdf
文件 2：C:\Users\JINZHIXUN\Desktop\HW\page 2.pdf
文件 3：
输出文件夹（留空 = 第一个文件所在文件夹）：
已生成：C:\Users\JINZHIXUN\Desktop\HW\page 1_merged_2files.pdf
```

这个例子中的路径是示意，请改成自己的文件路径。路径包含中文或空格时直接粘贴即可；从 Windows 复制的带双引号路径也可使用。输入顺序就是合并顺序，空行结束文件列表。输出文件夹可以留空；如果填写，必须是已存在的文件夹。生成文件名会标明操作，重名时追加 `(2)`、`(3)` 等，不覆盖旧文件。PDF 子菜单输入 `5` 返回主菜单；主菜单输入 `6` 退出。

PDF 拆分时，选 `1` 会生成 `原名_page_001.pdf` 等逐页文件；选 `2` 后输入起始和结束页码，会生成 `原名_pages_001-003.pdf` 这样的范围文件。图片转换和扫描件合并的操作方式与上例相同。

**当前限制：**受密码保护的 PDF、TIFF、HEIC 和多帧图片暂不支持。图片按 300 DPI 写入 PDF；工具会先在内存中生成输出，再写入新文件，特别大的扫描作业可能占用较多内存。

## 整理课程文件

先用 VS Code 打开项目根目录的 `course_rules.json`，将示例课程和关键词改成自己的课程。例如：

```json
{
  "微观经济学": ["微观", "microeconomics"],
  "宏观经济学": ["宏观", "macroeconomics"]
}
```

左侧是要创建的课程文件夹名，右侧是文件名关键词。关键词不区分英文字母大小写，按**文件名中的文字**匹配，不读取文件内容。请保留 JSON 的双引号、逗号和方括号；课程名不能包含 Windows 文件夹名不允许的字符。示例规则只是起点，建议运行前改成自己的课程。

运行 `python main.py`，选择 `2`，输入待整理文件夹路径。目标文件夹留空时使用该文件夹中的 `Sorted`；也可以输入别的目标路径。程序会列出每个文件的分类，只有输入 `y` 后才创建目标文件夹并复制。其他输入都会取消，原文件始终保留。

目前只扫描所选文件夹**顶层**的文件，不递归处理子文件夹。支持 PDF、PPT/PPTX、Word 的 DOC/DOCX、Excel 的 XLS/XLSX/CSV，以及 PNG、JPG/JPEG、BMP、GIF、WebP、TIF/TIFF、HEIC。其他格式和子文件夹会跳过。一个文件名只匹配一门课时，复制到对应课程文件夹；没有匹配或同时匹配多门课时，复制到 `Unsorted`，需要你之后人工判断。

例如，`微观 第1讲.pdf` 会进入 `Sorted/微观经济学/`；`未知讲义.pdf` 会进入 `Sorted/Unsorted/`。如果目标目录已有同名文件，会生成 `微观 第1讲 (2).pdf`，不会覆盖旧文件。再次运行也会继续生成编号副本，因此不需要重复整理同一批文件。课程整理只使用 Python 标准库，没有增加第三方依赖。

## 作业与 Deadline

运行 `python main.py`，选择 `3`。子菜单可以添加作业、查看全部或未完成作业、查看未来 7 天截止和已逾期的作业，以及按编号修改完成状态。添加时依次输入课程名称、作业名称、截止日期（例如 `2026-10-01`）、备注和是否已完成；日期必须是真实的 `YYYY-MM-DD`。

“未来 7 天”按电脑的本地日期计算，**包含今天和之后 6 个日历日**；“已逾期”指截止日期早于今天且仍未完成。完成的作业不会出现在未完成、未来 7 天或逾期列表中，但仍可在“全部作业”里看到，并可改回未完成。当前只记录日期，不记录具体时刻。

数据保存在 `data/deadlines.json`，不需要联网或数据库服务器。第一次添加作业时才创建文件。每次修改先将完整新内容写入临时文件，再替换当前文件；更新已有数据前，还会将上一版保存在 `data/deadlines.json.bak`。程序读到损坏数据会停止写入，不会用空列表覆盖它。两个文件均被 Git 忽略，属于你的个人数据；请按自己的备份习惯定期复制到安全位置。

目前面向单人、单窗口使用；不要同时在两个运行中的程序窗口修改同一份 Deadline 数据。

这一阶段选择 JSON，是因为个人作业数量少，用 Python 标准库即可读写，也方便你用 VS Code 查看。以后若需要多人同时使用或更复杂查询，再考虑 SQLite。没有为 Deadline 模块增加第三方依赖。

## 成绩计算器

运行 `python main.py`，选择 `4`，再选择 `1` 逐项录入已经知道的成绩。每项输入名称、百分制分数和占课程总评的权重；例如权重输入 `30` 表示占总评的 30%。项目名称留空结束录入。若要修改，重新选择 `1` 录入完整列表。退出成绩子菜单后，已录入成绩会清除，不写入磁盘。

选择 `2` 会显示两个不同的数字：**已计入总评**是各项 `分数 × 权重 ÷ 100` 之和；**已录入项目的加权平均**是把已录入项目的权重归一到 100% 后的平均分。例如平时作业 80 分、权重 30%，期中考试 90 分、权重 20%，已计入总评是 42 分，已录入项目的加权平均是 84 分；尚未录入的权重是 50%。

选择 `3` 后输入期末考试权重和目标总评。以上例继续，期末权重输入 `50`，目标总评输入 `85`，程序会显示“期末至少需要 86.00 分”。计算式是 `(目标总评 - 已计入总评) ÷ 期末权重比例`。反推时，已录入权重加期末权重必须恰好等于 100%；若还有尚未录入的平时项目，先录入其实际成绩，程序不会擅自假定这些项目的分数。若所需分数超过 100，会提示目标无法达到；显示的最低分按 0.01 分向上取整。

成绩和权重只接受 0 到 100 的有限数字，单项权重必须大于 0，项目名称不能重复，已录入权重不能超过 100%。输入错误时会显示原因并允许继续操作。成绩计算器仅使用 Python 标准库，没有新增第三方依赖。

## LaTeX 作业模板

模板在 `templates/homework-template.tex`，可参考 `examples/example-homework.tex`。模板已包含姓名、学号、课程、作业编号和日期；`problem` 自动编号题目，`solution` 用于解答，`proof` 用于证明。数学模式中可以使用 `\R`、`\E`、`\Var`、`\Cov` 和 `\dd` 等宏。示例用两道中级微观经济学题展示公式和证明。

每次写新作业时，建议复制模板，保留原文件。例如在项目根目录的 PowerShell 中运行：

```powershell
New-Item -ItemType Directory -Force .\output\latex | Out-Null
$target = '.\output\latex\homework-1.tex'
if (Test-Path -LiteralPath $target) { throw '目标作业文件已存在，请换一个新文件名' }
Copy-Item -LiteralPath .\templates\homework-template.tex -Destination $target
```

然后用 VS Code 打开 `output/latex/homework-1.tex`，修改文件开头的五项信息，再把 `problem`、`solution` 块复制成需要的题目数量。`output/` 不会提交到 Git；如果想长期保留自己的作业，请按自己的备份习惯保存。

**编译 `.tex` 需要独立的 LaTeX 编译器**，它不由 Python 的 `requirements.txt` 安装。本项目已用 [Tectonic 0.17.0](https://tectonic-typesetting.github.io/book/latest/getting-started/install.html) 实际编译模板和示例。它是一个基于 XeTeX 的独立程序，首次编译时联网下载所需的 `ctex`、数学宏包和字体，以后使用本地缓存。在项目根目录的 PowerShell 中，首次使用时逐行执行：

```powershell
New-Item -ItemType Directory -Force .\output | Out-Null
Invoke-WebRequest -Uri 'https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.17.0/tectonic-0.17.0-x86_64-pc-windows-msvc.zip' -OutFile .\output\tectonic-0.17.0-windows.zip
$actual = (Get-FileHash .\output\tectonic-0.17.0-windows.zip -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actual -ne 'f61ce51f0b0ade1015b7de7ef368541c5424e9756ecbd0d7af97d6d48030845f') { throw '下载文件校验失败，请勿解压运行' }
Expand-Archive -LiteralPath .\output\tectonic-0.17.0-windows.zip -DestinationPath .\output\tectonic-0.17.0
.\output\tectonic-0.17.0\tectonic.exe --version
```

下载地址是 Tectonic 的[官方发布文件](https://github.com/tectonic-typesetting/tectonic/releases/tag/tectonic%400.17.0)；命令会核对 SHA-256，再解压到 Git 忽略的 `output/`。若 `output/tectonic-0.17.0/tectonic.exe` 已存在，或 `tectonic` 已安装在 PATH 中，可以跳过下载。编译自己的作业或项目示例时，仍在项目根目录运行：

```powershell
python .\scripts\build_latex.py .\output\latex\homework-1.tex
python .\scripts\build_latex.py .\examples\example-homework.tex
```

程序会显示生成的 PDF 绝对路径，例如 `output/latex/homework-1/homework-1.pdf`。再次编译同一文件会自动使用 `homework-1 (2)` 等新目录，保留旧 PDF。模板采用 UTF-8 和 `ctexart`，支持中文姓名和正文；请不要用 `pdflatex` 编译。复制 `.tex` 或仅打开编辑器不会自动产生 PDF；编译成功后再打开实际生成的 PDF。LaTeX 模板不会读取或更改 Deadline 数据。

**不想输入编译命令时：**把你的 `.tex` 文件拖到项目根目录的 `build-homework.cmd` 上。窗口会显示新 PDF 的完整路径，按任意键才关闭；也可以在 PowerShell 中运行 `.\build-homework.cmd "你的作业.tex"`。这个入口同样需要先完成 `.venv` 与 Tectonic 的首次安装。

上述 Tectonic 路径已实际编译并检查模板与示例各一页。克隆仓库时，`output/` 不会随 Git 下载，需要重新执行首次安装命令。

## 运行测试

在项目目录、激活虚拟环境后执行：

```powershell
python -m unittest discover -s tests -v
```

测试使用 Python 标准库 `unittest`，并用已安装的 PDF、图片依赖生成临时样本；不会处理个人文件。测试覆盖菜单、PDF 文件顺序和异常、课程整理的匹配与原件保护、Deadline 的日期边界和数据保护，以及成绩计算的权重、反推、舍入和错误输入。

## 项目目录

```text
pku-semester-toolkit/
├── main.py             # 程序入口；运行这个文件
├── start-toolkit.cmd    # Windows 双击打开主菜单
├── build-homework.cmd   # 拖入 .tex 文件进行编译
├── toolkit/             # 菜单与后续功能模块
│   ├── __init__.py
│   ├── cli.py           # 主菜单
│   ├── pdf_cli.py       # PDF 子菜单与输入提示
│   ├── pdf_tools.py     # PDF 功能；可被其他界面复用
│   ├── organizer_cli.py # 课程整理的预览与确认
│   ├── organizer.py     # 文件扫描、分类与安全复制
│   ├── deadlines_cli.py # 作业菜单与输入提示
│   ├── deadlines.py     # 本地 JSON 存储和日期筛选
│   ├── grades_cli.py    # 成绩录入与结果显示
│   └── grades.py        # 加权成绩与目标反推计算
├── course_rules.json    # 可修改的课程关键词
├── data/                # Deadline 本地数据；个人数据不提交 Git
├── templates/           # LaTeX 作业模板
├── examples/            # 可独立编译的示例作业
├── scripts/             # LaTeX 编译入口；保留旧 PDF
├── tests/               # CLI、PDF、课程整理、Deadline 与成绩测试
├── requirements.txt     # pypdf 与 Pillow 的固定版本
├── .gitignore           # Git 不追踪的本地文件
└── README.md            # 安装与使用说明
```

采用 `toolkit/` 包保存功能逻辑，`main.py` 只启动菜单。PDF 的文件操作在 `pdf_tools.py`，交互提示在 `pdf_cli.py`；课程整理的复制逻辑在 `organizer.py`，预览和确认在 `organizer_cli.py`；Deadline 的读写和日期筛选在 `deadlines.py`，交互在 `deadlines_cli.py`；成绩公式在 `grades.py`，输入和显示在 `grades_cli.py`。以后增加 GUI 或 Web 界面时，可直接复用功能函数。想调整课程关键词，先看 `course_rules.json`；想调整日期筛选，先看 `deadlines.py` 中的 `due_next_7_days` 和 `overdue`；想修改成绩计算，先看 `grades.py`。

## 常见问题

- **`py` 不是内部或外部命令**：先安装 Python；也可尝试 `python --version`。确认版本至少为 3.11 后，将上述命令中的 `py -3` 换为 `python`。
- **PowerShell 禁止运行脚本**：可仅在当前 PowerShell 会话运行 `Set-ExecutionPolicy -Scope Process RemoteSigned`，再执行激活命令；或直接用 `.\.venv\Scripts\python.exe main.py`，无需激活。
- **`python` 找不到或版本不对**：先激活 `.venv`，或执行 `.\.venv\Scripts\python.exe --version` 检查环境。
- **`No module named toolkit`**：先用 `cd` 进入项目根目录，再运行 `python main.py`，不要直接运行 `toolkit\cli.py`。
- **`No module named pypdf` 或 `No module named PIL`**：确认已激活 `.venv`，再运行 `python -m pip install -r requirements.txt`。
- **PDF 提示受密码保护或无法读取**：先用阅读器检查原件；本版不会尝试破解或修改原件。
- **图片提示格式不支持**：目前只接受 JPG、JPEG、PNG、BMP；其他格式请先在可信的软件中另存为其中一种。
- **课程文件分类不符合预期**：检查 `course_rules.json` 的关键词。未匹配或匹配多门课的文件会进入 `Unsorted`；程序不会猜测课程。
- **课程规则提示无法读取**：检查 JSON 的引号、逗号和方括号，可用 VS Code 打开文件查看语法提示。
- **整理时提示复制失败**：确认目标文件夹可写，并查看菜单列出的失败文件；已成功复制的文件会保留，原件不会删除。
- **截止日期提示无效**：检查是否是 `YYYY-MM-DD`，例如 `2026-10-01`；`2026-02-30` 等不存在的日期也会被拒绝。
- **作业数据提示无法读取或格式损坏**：先保留 `data/deadlines.json` 原文件，再检查 `data/deadlines.json.bak`。程序不会自动覆盖损坏的数据。
- **成绩反推提示权重未达到 100%**：请检查是否漏录了某项平时成绩，或期末考试权重填错；只有已录入项目与期末考试合计恰好 100% 才能反推。
- **成绩反推提示目标无法达到**：即使期末考 100 分也达不到输入的目标；可检查课程权重、已录入成绩和目标总评。
- **提示没有找到 Tectonic**：确认已执行上面的下载、校验与解压命令，且 `output/tectonic-0.17.0/tectonic.exe` 存在。Python 虚拟环境不会安装它。
- **首次编译很慢或提示下载失败**：Tectonic 首次需要联网获取宏包和字体；检查网络后重试。已下载的资源会缓存，无需每次重下。
- **出现 `Fontconfig error`**：本机首次与后续编译都出现过这条提示，但 PDF 成功生成，中文和公式也经实际渲染检查。以脚本是否显示“已生成”和 PDF 是否可打开为准；若编译退出且没有 PDF，请保留完整报错排查。
- **LaTeX 提示找不到 `ctexart.cls` 或宏包**：检查首次下载是否完成；若用自己安装的其他 TeX 发行版，也须有 `ctex`、`geometry` 与 AMS 宏包。
- **中文变成乱码或无法编译**：将 `.tex` 保存为 UTF-8，并使用本节的 Tectonic 命令，不要用 `pdflatex`。
- **找不到或打不开作业 PDF**：按编译脚本显示的绝对路径查找。仅复制 `.tex` 或打开编辑器不会生成 PDF；编译成功后再打开同名 PDF。

## 后续开发路线

| 阶段 | 工作内容 | 主要检查 |
| --- | --- | --- |
| Phase 1（已完成） | 项目骨架、CLI、README | 菜单启动、退出与异常输入 |
| Phase 2（已完成） | PDF 合并、拆分、图片转 PDF、扫描件顺序合并 | 合法文件、空输入、损坏文件、输出命名与原件保护 |
| Phase 3（已完成） | 课程文件按关键词分类 | 同名、中文、空格、未知课程、已有目标文件 |
| Phase 4（已完成） | 本地 Deadline 管理 | 增查改完成状态、近 7 天与逾期筛选、数据读写 |
| Phase 5（已完成） | 成绩计算器 | 权重、分数范围、目标反推与错误提示 |
| Phase 6（已完成） | LaTeX 模板和示例 | Tectonic 编译、PDF 内容与版面检查 |
| Phase 7（已完成） | 全局检查与 Windows 快捷入口 | 路径、异常处理、README、CLI 与全部测试 |

文件处理默认保留原件；对输出重名采用新文件名，不静默覆盖。

后续若确有需要，可增加 Deadline 提醒、成绩数据保存或图形界面；第一版先保持本地 CLI 简单可读。

## Git 提交建议

本项目是独立 Git 仓库。建议每完成一个可运行、测试通过的阶段后提交一次，不必按单个文件拆分：

```text
chore: scaffold CLI project
feat: add PDF tools
feat: organize course files
feat: track assignment deadlines
feat: calculate grades
docs: add LaTeX homework template
chore: finish integration checks
```

`data/` 中的个人数据、`.venv/` 虚拟环境和 Python 缓存不会进入 Git。提交前可用 `git status` 检查将要提交的文件。

本地 PDF 工具案例放在 `output/pdf/`，LaTeX 编译结果放在 `output/latex/`；`output/` 不会进入 Git。
