# -*- coding: utf-8 -*-
"""
批量把概念卡里的完整路径 wikilink 改成短路径

Obsidian Graph View 解析短路径 wikilink 更稳定。
完整路径 [[30_书籍阅读/书名/概念/第12章_三篮分类法]] 在 Obsidian 解析时
偶发节点识别失败；改成短路径 [[第12章_三篮分类法]] 后连接数提升 ~13%。

用法:
  python scripts/shorten_wikilinks.py --vault-dir ./your-vault --book-name "你的书名"
"""
import re
import argparse
from pathlib import Path


def shorten_wikilinks_in_file(file_path):
    text = file_path.read_text(encoding='utf-8')
    original = text

    # 概念卡长路径 → 短路径
    text = re.sub(
        r'\[\[30_书籍阅读/[^/]+/概念/第\d+章_[^|\]]+\|',
        lambda m: '[[' + m.group(0).split('/概念/')[1].split('|')[0] + '|',
        text
    )
    text = re.sub(
        r'\[\[30_书籍阅读/[^/]+/概念/第\d+章_[^\]]+\]\]',
        lambda m: '[[' + m.group(0).split('/概念/')[1].rstrip(']') + ']]',
        text
    )

    # 章节卡长路径 → 短路径
    text = re.sub(
        r'\[\[30_书籍阅读/[^/]+/章节/第\d+章_[^|\]]+\|',
        lambda m: '[[' + m.group(0).split('/章节/')[1].split('|')[0] + '|',
        text
    )
    text = re.sub(
        r'\[\[30_书籍阅读/[^/]+/章节/第\d+章_[^\]]+\]\]',
        lambda m: '[[' + m.group(0).split('/章节/')[1].rstrip(']') + ']]',
        text
    )

    # 总览长路径 → 短路径
    text = re.sub(r'\[\[30_书籍阅读/[^/]+/0_总览\|', '[[0_总览|', text)
    text = re.sub(r'\[\[30_书籍阅读/[^/]+/0_总览\]\]', '[[0_总览]]', text)

    if text != original:
        file_path.write_text(text, encoding='utf-8')
        return True
    return False


def main():
    parser = argparse.ArgumentParser(description='wikilink 长路径 → 短路径（提升 Graph View 稳定性）')
    parser.add_argument('--vault-dir', required=True, help='ObsidianVault 根目录')
    parser.add_argument('--book-name', required=True, help='书名目录名（30_书籍阅读/ 下的）')
    args = parser.parse_args()

    book_dir = Path(args.vault_dir) / '30_书籍阅读' / args.book_name

    if not book_dir.exists():
        print(f'目录不存在: {book_dir}')
        return

    concept_dir = book_dir / '概念'
    if not concept_dir.exists():
        print(f'概念目录不存在: {concept_dir}')
        return

    changed = 0
    total = 0
    for f in concept_dir.glob('*.md'):
        total += 1
        if shorten_wikilinks_in_file(f):
            changed += 1

    print(f'处理 {total} 张概念卡，修改 {changed} 张')


if __name__ == '__main__':
    main()
