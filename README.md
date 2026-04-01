# LCM Direct - 直接读取 LCM 数据库

[![OpenClaw Skill](https://img.shields.io/badge/OpenClaw-Skill-blue)](https://openclaw.ai)

直接读取 LCM 数据库，绕过 OpenClaw 工具 bug，支持全文搜索消息和摘要。

## 背景

OpenClaw 的 LCM 工具（`lcm_grep`, `lcm_describe` 等）在 Telegram 渠道会话中存在 bug：
- [#57320](https://github.com/openclaw/openclaw/issues/57320) - Plugin tools not available in channel sessions
- [#50131](https://github.com/openclaw/openclaw/issues/50131) - Plugin tools not inherited by subagents

但 LCM 数据库本身是标准的 SQLite 格式，可以直接查询。

## 数据库位置

`~/.openclaw/lcm.db`

## 安装

```bash
# 克隆到 skills 目录
cd ~/.openclaw/skills
git clone https://github.com/Mubai1124/lcm-direct.git
```

## 使用方法

```bash
# 搜索消息和摘要（综合搜索）
python3 ~/.openclaw/skills/lcm-direct/scripts/lcm_search.py all "关键词"

# 只搜索消息
python3 ~/.openclaw/skills/lcm-direct/scripts/lcm_search.py messages "关键词"

# 只搜索摘要
python3 ~/.openclaw/skills/lcm-direct/scripts/lcm_search.py summaries "关键词"

# 列出所有对话
python3 ~/.openclaw/skills/lcm-direct/scripts/lcm_search.py conversations
```

## 功能

| 功能 | 说明 |
|------|------|
| 消息全文搜索 | 使用 SQLite FTS5 索引 |
| 摘要全文搜索 | 搜索压缩后的对话摘要 |
| 对话列表 | 查看所有对话及消息数量 |
| 综合搜索 | 同时搜索消息和摘要 |

## 数据库结构

| 表 | 说明 |
|---|------|
| conversations | 对话元数据 |
| messages | 原始消息 |
| summaries | 压缩摘要 |
| messages_fts | 消息全文搜索索引 |
| summaries_fts | 摘要全文搜索索引 |

## 输出格式

JSON 格式，包含：
- `type`: message 或 summary
- `id`: 消息/摘要 ID
- `role`: 角色（user/assistant/tool）
- `content`: 内容
- `created_at`: 时间戳
- `session`: 会话标识

## License

MIT
