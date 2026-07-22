# PDF OCR / 解析工具选型决策表

> **适用场景**：要把 PDF 转成结构化文本/章节 Markdown，给 book-deep-analysis skill 做前置步骤
> **触发**：`pymupdf doc[i].get_text()` 空页 > 80%（扫描件），或正常 PDF 但需要结构化提取
> **不适用**：纯电子版 .md/.txt/.epub（直接读）

## 判断流程

```
拿到一本书
    │
    ├── mobi / epub / azw3 ──→ Calibre 转 Markdown（5 分钟）
    │
    └── PDF
            │
            ├── 有文字层（能复制）──→ pymupdf get_text() 直接提取
            │
            └── 无文字层（扫描件）──→ 走 OCR
                                            │
                                            ├── GLM-4.6V（推荐，¥0，35 min/290页）
                                            ├── Mathpix（¥10/月，需翻墙）
                                            └── 本地 OCR（marker-pdf，CPU-only 慢）
```

## 工具对比

| 工具 | 类型 | 成本 | 290 页耗时 | 中文精度 | 推荐度 |
|---|---|---|---|---|---|
| GLM-4.6V | 云端 API | Coding Plan ¥0 | 35 min | 出版级 | ⭐⭐⭐⭐⭐ |
| GLM-4V-flash | 云端 API | ¥0 | 30 min | 好 | ⭐⭐⭐⭐ |
| Mathpix | 云端 API | ¥10/月起 | 15 min | 好 | ⭐⭐⭐ |
| marker-pdf | 本地 | 免费 | 3-5 小时 | 好 | ⭐⭐ |
| paddleocr | 本地 | 免费 | 2-3 小时 | 中 | ⭐⭐ |
| tesseract | 本地 | 免费 | 1-2 小时 | 一般 | ⭐ |

## 选型决策

### 有 Coding Plan 套餐
→ **GLM-4.6V**。¥0，出版级中文 OCR，35 分钟 290 页。不要犹豫。

### 没有智谱账号，但愿意付费
→ **Mathpix**。¥10/月，速度快，但需翻墙过 reCAPTCHA。

### 无网/纯本地/CPU 够强（i7+ / 16GB+）
→ **marker-pdf**。免费，但 i3 低压 U 跑 290 页要 3-5 小时，还容易 OOM。

### 无网/CPU 弱
→ 别用本地 OCR。等有网再用云端。i3 + 8GB 跑本地 OCR = 浪费生命。

## 关键坑

1. **Coding Plan Key 走 `/api/coding/paas/v4` 端点，不是 `/api/paas/v4`**
   - 用错端点会报 429（code 1113 = 余额不足）
   - Coding Plan 套餐用户走 coding 端点 = ¥0

2. **GLM-5V-Turbo 存在但 Coding Plan 套餐不开（code 1311）**
   - GLM-4.6V 是 Pro 套餐最高可用视觉模型
   - 4.6V 跟 5V 精度差距 < 3%

3. **不要用 GLM-5-Turbo / GLM-4-flash 做 OCR**
   - 它们是纯文本模型，不支持图片输入
   - 报 `messages.content.type 参数非法`

4. **pymupdf 检测文字层**
   ```python
   import pymupdf
   doc = pymupdf.open("book.pdf")
   empty_pages = sum(1 for i in range(len(doc)) if not doc[i].get_text().strip())
   ratio = empty_pages / len(doc)
   print(f"空页比例: {ratio:.1%}")
   # > 80% = 扫描件，需要 OCR
   ```
