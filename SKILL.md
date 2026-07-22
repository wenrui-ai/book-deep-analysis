---
name: book-deep-analysis
description: 把纸质书/电子书拆成可调用的知识资产——OCR + 概念卡 + Obsidian 知识图谱的完整流水线。支持扫描件 PDF（GLM-4.6V OCR）和电子版（Calibre 转 Markdown），GLM-5.2 提炼概念卡，Obsidian Graph View 可视化知识网络。
version: 1.0.0
author: 文瑞AI
license: MIT
platforms: [windows, macos, linux]
tags: [book, reading, OCR, scanned-pdf, knowledge-base, obsidian, zhipu]
---

# book-deep-analysis

把一本已落档的电子书/扫描书，拆成可入库的知识卡片（章节卡 + 概念卡 + 总览），再用 Obsidian Graph View 可视化为一张知识图谱。

## 它解决什么问题

书买了 → 翻几十页停住 → 三个月后跟没读一样。

**核心原因**：读完一遍就完了，知识没有变成能调用的东西。

这个 skill 把读书从「过一遍眼睛」变成「生成可检索、可互链、可追问的知识资产」：

```
290 页纸质书 → OCR → 25 章节卡 → 81 概念卡 → Obsidian 知识图谱
                                              ↓
                                    随时问任何一个概念，秒答
```

## 7 步流程

### Step 1 · 判断书的格式
拿到书第一件事，右键试一下能不能复制文字。
- 能复制 → 走 A 路（Calibre 转 Markdown，5 分钟）
- 不能复制 → 走 B 路（扫描件 OCR，35 分钟）

### Step 2A · 电子版走 Calibre
```bash
# mobi / epub / azw3 → Markdown
calibre-debug -e ebook-convert book.epub output.md
```

### Step 2B · 扫描件走 GLM-4.6V OCR
```bash
export ZHIPU_API_KEY="你的Key"

# 先验证 5 页
python scripts/ocr_zhipu_4v.py --pdf book.pdf --output _test.md --start 1 --end 5

# 全本 OCR
python scripts/ocr_zhipu_4v.py --pdf book.pdf --output 全本.md --concurrency 5
```
290 页扫描书，并发 5，约 35 分钟，¥0（Coding Plan 内部额度）。

### Step 3 · 按章节切分
OCR 出的全本是连续 Markdown，带 `<!-- page=N -->` 标记。
用正则 `^#+\s*第\s*(\d+)\s*章` 定位章节起始行，按行号切分成独立 .md 文件。

### Step 4 · AI 拆概念卡
```bash
python scripts/extract_concepts.py \
  --chapters-dir ./output/章节 \
  --output-dir ./output/概念 \
  --book-name "你的书名"
```
每章喂全文给 GLM-5.2，输出 3-5 张概念卡（JSON），写成 Obsidian .md。
25 章约 60 分钟，70% 自动生成。

### Step 5 · 手工补卡（关键）
AI 漏的 30% 卡，恰好是全书最核心的概念。
**必须自己读一遍补上**，否则这本书白拆了。

### Step 6 · 修复 wikilink
```bash
python scripts/fix_wikilinks.py \
  --concepts-dir ./output/概念 \
  --chapters-dir ./output/章节 \
  --book-name "你的书名"

python scripts/shorten_wikilinks.py \
  --vault-dir ./your-vault \
  --book-name "你的书名"
```

### Step 7 · 知识图谱
把概念卡放进 Obsidian vault（30_书籍阅读/书名/），打开 Graph View（Ctrl+G）。
81 个节点 + 728 条连接 = 这本书的可调用知识网络。

**Graph View 是知识图谱主载体**。Canvas（.canvas 文件）可作辅助但不推荐依赖——在某些环境下渲染不稳定。

## 依赖

| 工具 | 用途 | 免费？ |
|---|---|---|
| [pymupdf](https://pypi.org/project/pymupdf/) | PDF 拆图 | ✅ |
| [智谱 GLM-4.6V](https://open.bigmodel.cn/) | 扫描件 OCR | Coding Plan ¥0 |
| [智谱 GLM-5.2](https://open.bigmodel.cn/) | 概念卡提炼 | Coding Plan ¥0 |
| [Calibre](https://calibre-ebook.com/) | 电子书转 Markdown | ✅ |
| [Obsidian](https://obsidian.md/) | 知识库 + 图谱 | ✅ |

```bash
pip install pymupdf
```

## 文件结构

```
book-deep-analysis/
├── SKILL.md                  ← 本文件（流程说明）
├── README.md                 ← GitHub 仓库说明
├── LICENSE                   ← MIT
├── scripts/
│   ├── ocr_zhipu_4v.py       ← 扫描件 PDF → Markdown（GLM-4.6V）
│   ├── extract_concepts.py   ← 章节 Markdown → 概念卡（GLM-5.2）
│   ├── fix_wikilinks.py      ← wikilink 4 步修复
│   └── shorten_wikilinks.py  ← 长路径 → 短路径（提升 Graph View）
├── references/
│   ├── pdf-ocr-tool-selection.md       ← OCR 工具选型决策表
│   ├── scanned-pdf-ocr-recipe.md       ← 扫描件 OCR 完整 SOP
│   ├── concepts-extraction-guide.md    ← 概念卡提炼 + wikilink 修复
│   ├── obsidian-graph-view-guide.md    ← 知识图谱 + Graph View 配置
│   └── zhipu-api-endpoints.md          ← 智谱 API 端点 + 额度池说明
├── templates/
│   ├── book-overview.md      ← 书籍总览卡模板
│   ├── chapter-card.md       ← 章节卡模板
│   └── concept-card.md       ← 概念卡模板
└── examples/
    └── sample-concept-card.md ← 概念卡示例
```

## 关键设计决策

1. **OCR 用视觉模型，概念提炼用纯文本模型，不要混着用**
   - GLM-4.6V 视觉模型 OCR 强，GLM-5.2 纯文本模型提炼强
   - 混着用反而费劲（用户实测确认）

2. **Key 走环境变量，绝不硬编码**
   - `export ZHIPU_API_KEY=xxx` → 脚本读 `os.environ.get()`
   - 不要写进任何文件

3. **概念卡覆盖率 100% 才算完事**
   - AI 自动生成 70%，剩下 30% 必须手工补
   - 漏的恰好是最核心的概念

4. **Graph View > Canvas**
   - Obsidian Graph View（Ctrl+G）是知识图谱主载体
   - Canvas（.canvas）在某些环境下渲染不稳定，不推荐依赖

5. **短路径 wikilink > 完整路径**
   - `[[第12章_三篮分类法]]` 比 `[[30_书籍阅读/书名/概念/第12章_三篮分类法]]` 更稳定
   - Graph View 连接数提升 ~13%

## 实战数据

| 指标 | 数据 |
|---|---|
| 书的规格 | 290 页扫描件 PDF |
| OCR 耗时 | 35 分钟（并发 5） |
| OCR tokens | ~56 万 |
| OCR 成本 | ¥0（Coding Plan 内部额度） |
| 概念卡数 | 81 张 |
| 知识图谱节点 | 81 |
| 知识图谱连接 | 728 |
| 全流程耗时 | 2 小时 40 分钟 |

## License

MIT — 随便用，注明出处就行。
