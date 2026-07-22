# -*- coding: utf-8 -*-
"""
概念卡提炼脚本（GLM-5.2 纯文本模型）

把 OCR 出的章节 Markdown，按章节喂给 GLM-5.2，每章输出 3-5 张概念卡。
概念卡含：概念名 / 定义 / 书中原文 / 应用建议 / 关联章节 wikilink。

用法:
  export ZHIPU_API_KEY="你的Key"
  python scripts/extract_concepts.py \
    --chapters-dir ./output/章节 \
    --output-dir ./output/概念 \
    --book-name "你的书名"

设计:
- 走 GLM-5.2 纯文本模型（不要用视觉模型做概念提炼）
- 并发 5 → 失败章自动重试
- JSON 宽松解析（处理截断 + 嵌套引号）
- 输出带 wikilink 的 Obsidian 概念卡 .md
"""
import os, sys, json, time, argparse, re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

import urllib.request, urllib.error

# ============ 配置 ============
API_KEY = os.environ.get('ZHIPU_API_KEY')
if not API_KEY:
    print('❌ 环境变量 ZHIPU_API_KEY 未设置')
    sys.exit(1)

API_URL = os.environ.get('ZHIPU_API_URL', 'https://open.bigmodel.cn/api/coding/paas/v4/chat/completions')
MODEL = os.environ.get('ZHIPU_TEXT_MODEL', 'glm-5.2')
CONCURRENCY = 5
MAX_RETRIES = 3
TIMEOUT = 90

PROMPT_TEMPLATE = """你是中文书籍阅读理解专家。从下面这一章提炼 3 个核心概念卡，只输出 JSON 数组:

每张卡:
- concept: 2-8 字
- definition: 80-120 字
- source_quote: 20-60 字
- application: 60-100 字
- related_chapters: ["[[第N章_章名]]"]

只输出 JSON 数组，不要任何解释文字。

章节:
{chapter_text}
"""

PROGRESS_LOCK = Lock()


def call_glm(prompt, retries=MAX_RETRIES):
    payload = {"model": MODEL, "messages": [{"role": "user", "content": prompt}],
               "max_tokens": 4000, "temperature": 0.3}
    for i in range(retries):
        try:
            req = urllib.request.Request(API_URL, data=json.dumps(payload).encode(),
                headers={'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                result = json.loads(r.read())
                return result['choices'][0]['message'].get('content', ''), result.get('usage', {})
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(5)
                continue
            elif e.code >= 500:
                time.sleep(2)
                continue
            return '', {'error': f'HTTP {e.code}: {e.read().decode()[:200]}'}
        except Exception as e:
            if i < retries - 1:
                time.sleep(2)
                continue
            return '', {'error': str(e)[:200]}
    return '', {'error': 'max retries'}


def parse_concepts(content):
    """宽松解析 — 处理 JSON 截断 + 嵌套引号"""
    m = re.search(r'```json\s*(\[.*?\])\s*```', content, re.DOTALL)
    json_str = m.group(1) if m else (re.search(r'(\[.*\])', content, re.DOTALL) or [None, None])[1]
    if not json_str:
        return None
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # 截断修复: 找最后一个 },
        last = json_str.rfind('},')
        if last > 0:
            try:
                return json.loads(json_str[:last+1] + ']')
            except:
                pass
        last = json_str.rfind('}')
        if last > 0:
            try:
                return json.loads(json_str[:last+1] + ']')
            except:
                pass
    return None


def extract_chapter_info(md_path):
    text = md_path.read_text(encoding='utf-8')
    title = ''
    for line in text.splitlines():
        if line.startswith('title:'):
            title = line.split(':', 1)[1].strip()
            break
    parts = text.split('---', 2)
    body = parts[2].strip() if len(parts) >= 3 else text
    return title, body


def write_concept_cards(concepts, chapter_num, chapter_title, output_dir, book_name):
    written = []
    for i, c in enumerate(concepts, 1):
        concept_name = c.get('concept', f'概念{i}').strip()
        if not concept_name:
            continue
        safe_name = re.sub(r'[\\/:*?"<>|\r\n]', '', concept_name)[:30]
        fname = f'第{chapter_num:02d}章_{safe_name}.md'
        out_path = output_dir / fname
        related_links = '\n'.join([f'- {link}' for link in c.get('related_chapters', [])])
        front = f'''---
title: {concept_name}
type: concept
book: {book_name}
source_chapter: 第{chapter_num}章 {chapter_title}
tags: [概念, {book_name}]
---

# {concept_name}

> 来源: 第 {chapter_num} 章《{chapter_title}》

## 定义

{c.get('definition', '（未提供）')}

## 书中原文

> {c.get('source_quote', '（未提供）')}

## 应用建议

{c.get('application', '（未提供）')}

## 关联章节

{related_links if related_links else '- [[0_总览|总览]]'}
'''
        out_path.write_text(front, encoding='utf-8')
        written.append((fname, c))
    return written


def main():
    parser = argparse.ArgumentParser(description='章节 Markdown → 概念卡（GLM-5.2）')
    parser.add_argument('--chapters-dir', required=True, help='章节 .md 所在目录')
    parser.add_argument('--output-dir', required=True, help='概念卡输出目录')
    parser.add_argument('--book-name', required=True, help='书名（用于 frontmatter）')
    parser.add_argument('--concurrency', type=int, default=CONCURRENCY)
    args = parser.parse_args()

    chapters_dir = Path(args.chapters_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    chapter_files = sorted(chapters_dir.glob('第*章_*.md'))
    if not chapter_files:
        print('❌ 没找到章节文件（期望 第N章_XXX.md 格式）')
        return

    print(f'📚 找到 {len(chapter_files)} 个章节')
    all_written = []
    total_usage = {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}

    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = {}
        for f in chapter_files:
            ch_num_match = re.search(r'第(\d+)章', f.name)
            if not ch_num_match:
                continue
            ch_num = int(ch_num_match.group(1))
            title, body = extract_chapter_info(f)
            if len(body) < 500:
                continue
            prompt = PROMPT_TEMPLATE.format(chapter_text=body[:18000])
            futures[executor.submit(call_glm, prompt)] = (ch_num, title)

        completed = 0
        for future in as_completed(futures):
            ch_num, ch_title = futures[future]
            content, usage = future.result()
            if usage and 'error' not in usage:
                for k in total_usage:
                    total_usage[k] += usage.get(k, 0)
            if not content:
                with PROGRESS_LOCK:
                    print(f'  ✗ 第{ch_num:02d}章 GLM 失败: {usage.get("error", "?")}')
                continue
            concepts = parse_concepts(content)
            if not concepts:
                with PROGRESS_LOCK:
                    print(f'  ✗ 第{ch_num:02d}章 parse fail')
                continue
            written = write_concept_cards(concepts, ch_num, ch_title, output_dir, args.book_name)
            all_written.extend(written)
            with PROGRESS_LOCK:
                print(f'  ✓ 第{ch_num:02d}章《{ch_title}》→ {len(written)} 张')

            completed += 1
            if completed % 5 == 0:
                with PROGRESS_LOCK:
                    print(f'📊 进度 {completed}/{len(futures)} tokens: {total_usage["total_tokens"]:,}')

    print(f'\n✅ 完成: {len(all_written)} 张概念卡 / tokens {total_usage["total_tokens"]:,}')
    print(f'📂 {output_dir}')


if __name__ == '__main__':
    main()
