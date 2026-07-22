# book-deep-analysis

> 把一本书拆成可调用的知识资产：OCR → 概念卡 → Obsidian 知识图谱

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)

## 这是什么

一个把纸质书/电子书拆解为结构化知识资产的完整工具链。290 页的扫描书，2 小时 40 分钟变成 81 张概念卡 + 一张可检索的知识图谱。

读完一本书 ≠ 拥有这本书的知识。这个项目把读书从「过一遍眼睛」变成「生成可检索、可互链、可追问的知识资产」。

### 核心能力

```
纸质书 / PDF
    │
    ├── 电子版 (mobi/epub) ──→ Calibre (5 min) ──┐
    │                                            │
    └── 扫描件 PDF ──→ GLM-4.6V OCR (35 min) ───┘
                                                   │
                                            Markdown 全文
                                                   │
                                    GLM-5.2 按章拆概念卡 (60 min)
                                                   │
                                        Obsidian 知识图谱
                                         81 节点 + 728 连接
                                                   │
                                         随时问任何概念，秒答
```

## 快速开始

### 1. 安装依赖

```bash
pip install pymupdf
```

需要一个 [智谱 BigModel](https://open.bigmodel.cn/) 账号（Coding Plan 套餐 ¥0 可用）。

### 2. 设置 API Key

```bash
# Git Bash
export ZHIPU_API_KEY="你的Key"

# PowerShell
$env:ZHIPU_API_KEY="你的Key"
```

### 3. 跑 OCR（扫描件 PDF）

```bash
# 先验证 5 页
python scripts/ocr_zhipu_4v.py --pdf your-book.pdf --output _test.md --start 1 --end 5

# 全本 OCR
python scripts/ocr_zhipu_4v.py --pdf your-book.pdf --output full-text.md --concurrency 5
```

### 4. 按章节切分

OCR 输出的是连续 Markdown，按 `第N章` 标题切分成独立文件：

```
output/
├── 章节/
│   ├── 第01章_绪论.md
│   ├── 第02章_xxx.md
│   └── ...
```

### 5. AI 拆概念卡

```bash
python scripts/extract_concepts.py \
  --chapters-dir ./output/章节 \
  --output-dir ./output/概念 \
  --book-name "你的书名"
```

### 6. 手工补卡（关键！）

AI 会自动生成 ~70% 的概念卡。**剩下 30% 是全书最核心的概念**，必须自己读一遍补上。

### 7. 修复 wikilink + 放进 Obsidian

```bash
python scripts/fix_wikilinks.py \
  --concepts-dir ./output/概念 \
  --chapters-dir ./output/章节 \
  --book-name "你的书名"

python scripts/shorten_wikilinks.py \
  --vault-dir ./your-obsidian-vault \
  --book-name "你的书名"
```

把概念卡文件夹复制到 Obsidian vault 的 `30_书籍阅读/书名/` 下，打开 Graph View（Ctrl+G），就能看到这本书的知识网络。

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

## 脚本说明

| 脚本 | 作用 |
|---|---|
| `ocr_zhipu_4v.py` | 扫描件 PDF → Markdown（GLM-4.6V 视觉 OCR，并发，自动重试） |
| `extract_concepts.py` | 章节 Markdown → 概念卡 .md（GLM-5.2，每章 3-5 张卡） |
| `fix_wikilinks.py` | 修复概念卡 wikilink（冒号/路径/死链/占位符 4 步） |
| `shorten_wikilinks.py` | 长路径 wikilink → 短路径（Graph View 连接数 +13%） |

## 模板

| 模板 | 用途 |
|---|---|
| `templates/book-overview.md` | 每本书的总览卡 |
| `templates/chapter-card.md` | 每章的章节卡 |
| `templates/concept-card.md` | 每个概念的概念卡 |

## 设计理念

1. **工具不在多在对路** —— 4 个工具（Calibre / GLM-4.6V / GLM-5.2 / Obsidian）就够
2. **视觉模型做 OCR，纯文本模型做提炼** —— 不要混着用
3. **概念卡 100% 覆盖才算完事** —— AI 漏的那 30% 恰好是核心
4. **Key 走环境变量** —— 绝不硬编码进文件
5. **Graph View > Canvas** —— Obsidian Graph View 是知识图谱主载体

## 适用场景

- 买了一堆书但永远停在 47 页的人
- 读完一本书三个月后跟没读一样的人
- 想构建跨书知识网络（多本书的概念图谱叠加）的人
- 需要 AI 直接追问书里任何概念的人

## 不适用场景

- 只想快速了解一本书大意（用 AI 总结就够了）
- 纯文学/小说（叙事类不适合拆概念卡）
- 漫画/图册（OCR 无意义）

## 致谢

- [智谱 GLM](https://open.bigmodel.cn/) — GLM-4.6V 视觉 OCR + GLM-5.2 文本提炼
- [pymupdf](https://pymupdf.readthedocs.io/) — PDF 处理
- [Obsidian](https://obsidian.md/) — 知识库 + Graph View
- [Calibre](https://calibre-ebook.com/) — 电子书格式转换

## License

[MIT](LICENSE) — 随便用，注明出处就行。
