# Obsidian 知识图谱 + Graph View 配置指南

> 配套 `book-deep-analysis` SKILL.md Step 7

## 知识图谱主载体 = Graph View

**Graph View（Ctrl+G）是知识图谱的主载体，不是 Canvas。**

Canvas（.canvas 文件）在某些环境下反复渲染失败（即使 JSON 完美、节点 ID 唯一、坐标合法）。Graph View 通过短路径 wikilink 自动构建，更稳定。

## 配置步骤

### 1. Obsidian vault 目录结构
```
你的vault/
└── 30_书籍阅读/
    └── 书名/
        ├── 0_总览.md
        ├── 章节/
        │   ├── 第01章_xxx.md
        │   └── ...
        └── 概念/
            ├── 第01章_概念A.md
            └── ...
```

### 2. wikilink 规范
- **概念卡之间互链**：用短路径 `[[第12章_概念名]]`
- **概念卡 → 总览**：用 `[[0_总览]]` 或 `[[0_总览|总览]]`
- **不要用完整路径** `[[30_书籍阅读/书名/概念/第12章_概念名]]`

### 3. 打开 Graph View
`Ctrl+G` → 左侧筛选 → 选择本书的文件夹 → 可看到所有概念卡的互链网络。

### 4. 推荐插件
- **Smart Connections** —— AI 辅助找相关概念
- **Dataview** —— 按标签/类型查询卡片

## 效果基线

| 指标 | 数据（81 张概念卡） |
|---|---|
| 节点数 | 81 |
| 卡→卡连接 | 728（短路径）vs 646（完整路径） |
| 孤立节点 | 0 |
| 平均连接数 | ~9/卡 |

## 常见问题

### Q: Graph View 节点太多看不清？
A: 用 Graph View 左侧筛选，按文件夹过滤。或按标签过滤（只看 `type: concept`）。

### Q: 概念卡之间的连接不够多？
A: 检查 wikilink 是否用短路径。跑 `shorten_wikilinks.py` 转换。完整路径版本 Obsidian 解析不稳定。

### Q: 外部写入 .md 后 Obsidian 不刷新？
A: 完全退出 Obsidian 再重新打开。外部写入会触发 Obsidian 缓存卡死。

### Q: Canvas 能用吗？
A: 可以做辅助可视化，但**不要作为唯一交付**。Canvas 在某些环境下渲染不稳定。
