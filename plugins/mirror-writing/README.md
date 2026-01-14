# Mirror Writing 插件

自媒体短视频文案创作助手，基于多层Serendipity联想的内容创作系统。

## 安装

```bash
claude --plugin-dir ./mirror-writing
```

## 使用

### 一键创作
```bash
/mirror-writing:create 职场沟通技巧
```

### 单独功能
```bash
/mirror-writing:index     # 索引知识库
/mirror-writing:profile   # 生成创作者画像
```

## 工作流程

```
阶段2：任务分析 → 阶段3：关键词发散 → (可选)阶段3B：深挖 → 阶段4：文案生成
```

- 阶段3B：等待60秒确认，超时跳过
- 阶段4：等待60秒设置参数，超时使用默认（60秒×10个）

## 目录结构

```
.mirror-writing/
├── sessions/           # 会话隔离目录
│   └── {session_id}/   # 每次创作独立会话
│       ├── task.json
│       ├── keywords.md
│       └── outputs.md
├── _index.json         # 全局索引
└── profile.md          # 全局画像
```
