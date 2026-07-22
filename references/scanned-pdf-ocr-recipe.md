# 扫描件 PDF 的 OCR 与分析 SOP

## 适用场景
- PDF 无文字层（`pymupdf doc[i].get_text()` 返回空字符串）
- 常见来源：扫描仪导出（Creator = "RICOH Aficio" / "Canon iR" 等）+ iLovePDF 优化过
- 物理页码跟 PDF 页码不一致（有前置封面/版权/前言/目录页）

## 完整步骤

### Step 1 · 检测是否真的需要 OCR
```python
import pymupdf
doc = pymupdf.open("book.pdf")
for i in range(min(5, len(doc))):
    text = doc[i].get_text().strip()
    print(f"Page {i+1}: {len(text)} chars")
# 全是 0 或个位数 = 扫描件
```

### Step 2 · 设置 API Key
```bash
export ZHIPU_API_KEY="你的Key"
# Coding Plan 用户默认走 /api/coding/paas/v4 端点（脚本已配）
```

### Step 3 · 验证 5 页
```bash
python scripts/ocr_zhipu_4v.py \
  --pdf book.pdf \
  --output _test.md \
  --start 1 --end 5
```
检查 _test.md 看看 OCR 精度是否可接受。

### Step 4 · 全本 OCR
```bash
python scripts/ocr_zhipu_4v.py \
  --pdf book.pdf \
  --output 全本.md \
  --concurrency 5
```

### Step 5 · 检查输出
- 每页有 `<!-- page=N -->` 标记（N = PDF 物理页码）
- 失败页有 `<!-- 第 N 页 OCR 失败 -->` 标记
- 末尾有耗时 + tokens 统计

## 性能基线（290 页扫描书）

| 配置 | 耗时 | tokens |
|---|---|---|
| 并发 3 | ~60 min | ~60 万 |
| 并发 5（推荐） | ~35 min | ~56 万 |
| 并发 8 | ~25 min | ~56 万（QPS 可能限流） |

- DPI 120 够 OCR + 省 token
- 超过并发 8 容易触发 429（限流后自动等 5s 重试）

## 常见问题

### Q: 429 频率太高怎么办？
A: 降并发到 3，或增加重试等待时间。脚本默认 429 等 5s。

### Q: 某些页 OCR 出来是乱码？
A: 可能是：
- 该页是图片/图表（OCR 无意义）
- 该页倾斜角度太大（先做纠偏再 OCR）
- DPI 太低（调到 150-200）

### Q: 物理页码跟目录页码对不上？
A: 目录页码 = PDF 物理页码 - 前置页数。前置页数 = 封面 + 版权 + 前言 + 目录页的总和。
通常 `物理页码 = 目录页码 + 偏移量`，偏移量需要手动确认（翻到正文第 1 章，看它的 PDF 物理页码）。
