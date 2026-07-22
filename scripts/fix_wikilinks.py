# -*- coding: utf-8 -*-
"""
概念卡 wikilink 修复脚本

自动跑 4 步修复（Obsidian wikilink 常见问题）:
1. wikilink 里的半角冒号 → 全角冒号（匹配章节文件名）
2. ../章节/ 相对路径 → 30_书籍阅读/<书名>/章节/ 绝对路径
3. 占位符死链 [[02_章节目录]] → [[0_总览|回到总览]]
4. [[第0章]] fallback → [[0_总览|总览]]

用法:
  python scripts/fix_wikilinks.py \
    --concepts-dir ./output/概念 \
    --chapters-dir ./output/章节 \
    --book-name "你的书名"
"""
import re
import argparse
from pathlib import Path


def fix_wikilinks_in_file(f, chapters_dir, book_name):
    text = f.read_text(encoding='utf-8')
    original = text

    # 1. wikilink 里的半角冒号 → 全角冒号
    text = re.sub(r'(\[\[[^\]]*?第\d+章_[^|\]]*?):', r'\1：', text)

    # 2. 相对路径 → 绝对路径
    text = re.sub(r'\[\[\.\./章节/([^\]]+?)\|',
                   rf'[[30_书籍阅读/{book_name}/章节/\1|', text)
    text = re.sub(r'\[\[\.\./章节/([^\]]+?)\]\]',
                   rf'[[30_书籍阅读/{book_name}/章节/\1]]', text)

    # 3. 章节目录占位符
    text = re.sub(r'\[\[\d+_章节目录(?:\|[^\]]*)?\]\]',
                  rf'[[30_书籍阅读/{book_name}/0_总览|回到总览]]', text)
    text = re.sub(r'\[\[回到章节\]\]',
                  rf'[[30_书籍阅读/{book_name}/0_总览|回到总览]]', text)

    # 4. 第0章 fallback
    text = text.replace('[[第0章]]', f'[[30_书籍阅读/{book_name}/0_总览|总览]]')
    text = text.replace('[[第0章|]]', f'[[30_书籍阅读/{book_name}/0_总览|总览]]')

    if text != original:
        f.write_text(text, encoding='utf-8')
        return True
    return False


def main():
    parser = argparse.ArgumentParser(description='修复概念卡里的 wikilink（4 步）')
    parser.add_argument('--concepts-dir', required=True, help='概念卡 .md 目录')
    parser.add_argument('--chapters-dir', required=True, help='章节 .md 目录')
    parser.add_argument('--book-name', required=True, help='书名目录名')
    args = parser.parse_args()

    concepts_dir = Path(args.concepts_dir)
    chapters_dir = Path(args.chapters_dir)

    fixed = 0
    for f in concepts_dir.glob('第*章_*.md'):
        if fix_wikilinks_in_file(f, chapters_dir, args.book_name):
            fixed += 1

    print(f'修复 {fixed} 张概念卡的 wikilinks')
    print(f'📂 {concepts_dir}')
    print('\n验证步骤:')
    print('  如果你有 Obsidian vault 验证脚本，跑一下确认 0 断链')


if __name__ == '__main__':
    main()
