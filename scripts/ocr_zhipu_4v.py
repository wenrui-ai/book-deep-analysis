# -*- coding: utf-8 -*-
"""
智谱 GLM-4.6V 扫描件 PDF OCR pipeline

用法:
  # 设置环境变量（Key 不落盘，安全）
  export ZHIPU_API_KEY="你的Key"

  # 验证 5 页
  python scripts/ocr_zhipu_4v.py --pdf book.pdf --output _test.md --start 1 --end 5

  # 全本 OCR
  python scripts/ocr_zhipu_4v.py --pdf book.pdf --output 全本.md --concurrency 5

关键设计:
- Key 走环境变量 ZHIPU_API_KEY（绝不硬编码）
- pymupdf 拆 PDF 为 PNG（120 DPI，够 OCR + 省 token）
- ThreadPoolExecutor 并发 5（避免 QPS 限流）
- 429/5xx 自动重试（429 等 5s，5xx 等 2s）
- 输出 Markdown 每页带 <!-- page=N --> 标记，方便后续按 page 切章节

支持的端点:
- Coding Plan 套餐: https://open.bigmodel.cn/api/coding/paas/v4/chat/completions
- 通用余额:        https://open.bigmodel.cn/api/paas/v4/chat/completions
"""
import os
import sys
import json
import time
import argparse
import base64
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

import pymupdf
import urllib.request
import urllib.error

# ============ 配置 ============
API_KEY = os.environ.get('ZHIPU_API_KEY')
if not API_KEY:
    print('❌ 环境变量 ZHIPU_API_KEY 未设置')
    print('   Git Bash:  export ZHIPU_API_KEY=你的Key')
    print('   PowerShell: $env:ZHIPU_API_KEY="你的Key"')
    sys.exit(1)

# Coding Plan 用户用这个端点；通用余额用户改成 /api/paas/v4
API_URL = os.environ.get('ZHIPU_API_URL', 'https://open.bigmodel.cn/api/coding/paas/v4/chat/completions')
MODEL = os.environ.get('ZHIPU_OCR_MODEL', 'glm-4.6v')
DPI = 120  # 够 OCR 又省 token
CONCURRENCY = 5
MAX_RETRIES = 3
TIMEOUT = 60

OCR_PROMPT = """你是中文扫描书 OCR 引擎。请把这张图里的所有中文文字按原文逐字逐行抄给我。

严格要求:
1. 按原文逐字抄录，不总结、不省略、不改正错别字
2. 保留段落结构和换行
3. 标题用 # 二级标题，小节标题用 ## 三级标题
4. 表格用 Markdown 表格语法
5. 引用、引文段落保持原样
6. 如果有页码，忽略掉（我们用 PDF 物理页码追踪）
7. 章节起始时如果有"第X章"或 PART 标记，保留作为标题

只输出 OCR 文本本身，不要加任何"以下是..."的引导词。"""


def pdf_page_to_png_bytes(doc, page_idx, dpi=DPI):
    page = doc[page_idx]
    pix = page.get_pixmap(dpi=dpi)
    return pix.tobytes("png")


def ocr_one_page(png_bytes, page_num):
    img_b64 = base64.b64encode(png_bytes).decode()
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
            {"type": "text", "text": OCR_PROMPT}
        ]}],
        "max_tokens": 4000,
        "temperature": 0.1
    }
    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(
                API_URL,
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    'Authorization': f'Bearer {API_KEY}',
                    'Content-Type': 'application/json'
                }
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                result = json.loads(r.read())
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                usage = result.get('usage', {})
                return content, usage, None
        except urllib.error.HTTPError as e:
            err_body = e.read().decode()
            if e.code == 429:
                time.sleep(5)
                continue
            elif e.code >= 500:
                time.sleep(2)
                continue
            else:
                return "", {}, f"HTTP {e.code}: {err_body[:200]}"
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(2)
                continue
            return "", {}, str(e)[:200]
    return "", {}, "Max retries exceeded"


def process_page(doc, page_idx, page_num):
    png_bytes = pdf_page_to_png_bytes(doc, page_idx)
    content, usage, err = ocr_one_page(png_bytes, page_num)
    return {
        'page_num': page_num,
        'content': content.strip(),
        'usage': usage,
        'error': err,
    }


PROGRESS_LOCK = Lock()


def progress_print(msg):
    with PROGRESS_LOCK:
        print(msg, flush=True)


def main():
    parser = argparse.ArgumentParser(description='扫描件 PDF → Markdown OCR pipeline（GLM-4.6V）')
    parser.add_argument('--pdf', required=True, help='PDF 文件路径')
    parser.add_argument('--output', required=True, help='输出 Markdown 文件路径')
    parser.add_argument('--start', type=int, default=1, help='起始 PDF 物理页（1-indexed）')
    parser.add_argument('--end', type=int, default=None, help='结束 PDF 物理页')
    parser.add_argument('--concurrency', type=int, default=CONCURRENCY, help='并发数')
    args = parser.parse_args()

    print(f'📖 打开 PDF: {args.pdf}')
    doc = pymupdf.open(args.pdf)
    total_pages = doc.page_count
    print(f'📄 总页数: {total_pages}')

    start_page = max(1, args.start)
    end_page = args.end if args.end else total_pages
    end_page = min(end_page, total_pages)
    pages_to_process = list(range(start_page, end_page + 1))
    print(f'🎯 处理范围: 第 {start_page} - {end_page} 页，共 {len(pages_to_process)} 页')
    print(f'⚡ 并发数: {args.concurrency} | 模型: {MODEL}')
    print()

    results = {}
    total_usage = {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
    start_time = time.time()
    completed = 0

    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        future_to_page = {
            executor.submit(process_page, doc, page_idx - 1, page_idx): page_idx
            for page_idx in pages_to_process
        }
        for future in as_completed(future_to_page):
            page_idx = future_to_page[future]
            try:
                r = future.result()
                results[r['page_num']] = r
                if r['usage']:
                    for k in total_usage:
                        total_usage[k] += r['usage'].get(k, 0)
                if r['error']:
                    progress_print(f'  ✗ 第 {r["page_num"]:>3} 页失败: {r["error"]}')
                else:
                    progress_print(f'  ✓ 第 {r["page_num"]:>3} 页 OCR 完成 ({len(r["content"])} 字)')
            except Exception as e:
                progress_print(f'  ✗ 第 {page_idx:>3} 页异常: {str(e)[:100]}')

            completed += 1
            if completed % 10 == 0 or completed == len(pages_to_process):
                elapsed = time.time() - start_time
                speed = completed / elapsed if elapsed > 0 else 0
                eta = (len(pages_to_process) - completed) / speed if speed > 0 else 0
                progress_print(
                    f'📊 进度: {completed}/{len(pages_to_process)} '
                    f'({100*completed/len(pages_to_process):.1f}%) '
                    f'速度 {speed:.2f} 页/秒 '
                    f'ETA {eta:.0f}秒 '
                    f'tokens: {total_usage["total_tokens"]:,}'
                )

    print()
    print('💾 写 Markdown...')
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f'# OCR 全本（{MODEL}）\n\n')
        f.write(f'> 总页数: {len(pages_to_process)} | tokens: {total_usage["total_tokens"]:,}\n')
        f.write(f'> OCR 时间: {time.strftime("%Y-%m-%d %H:%M:%S")}\n\n')
        f.write('---\n\n')
        for page_num in sorted(results.keys()):
            r = results[page_num]
            if r['error']:
                f.write(f'<!-- 第 {page_num} 页 OCR 失败: {r["error"]} -->\n\n')
                continue
            f.write(f'<!-- page={page_num} -->\n')
            f.write(r['content'])
            f.write('\n\n')

    elapsed = time.time() - start_time
    print()
    print(f'✅ 完成! 输出: {output_path}')
    print(f'   耗时: {elapsed:.1f} 秒 ({elapsed/60:.1f} 分钟)')
    print(f'   tokens: {total_usage["total_tokens"]:,} (输入 {total_usage["prompt_tokens"]:,} + 输出 {total_usage["completion_tokens"]:,})')
    doc.close()


if __name__ == '__main__':
    main()
