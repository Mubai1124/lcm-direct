---
name: lcm-direct
description: >
  直接读取 LCM 数据库（绕过 OpenClaw 工具 bug），支持全文搜索消息和摘要。
  当需要搜索历史对话、查找特定内容时使用。
metadata:
  openclaw:
    homepage: ""
---

# LCM Direct - 直接读取 LCM 数据库

## 背景

OpenClaw 的 LCM 工具（lcm_grep, lcm_describe 等）在 Telegram 渠道会话中存在 bug（#57320, #50131），
但 LCM 数据库本身是标准的 SQLite 格式，可以直接查询。

## 数据库位置

`~/.openclaw/lcm.db`

## 数据库结构

| 表 | 行数 | 用途 |
|---|------|------|
| conversations | 84 | 对话元数据 |
| messages | 34,507 | 原始消息 |
| summaries | 662 | 压缩摘要 |
| messages_fts | 34,507 | 消息全文搜索索引 |
| summaries_fts | 662 | 摘要全文搜索索引 |

## 工具函数

### 1. 搜索消息（全文搜索）

```python
def search_messages(query, limit=20):
    """
    在消息全文搜索索引中搜索
    """
    import sqlite3
    conn = sqlite3.connect('/home/YangYishuo/.openclaw/lcm.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT m.message_id, m.role, m.content, m.created_at, c.session_key
        FROM messages_fts fts
        JOIN messages m ON fts.rowid = m.message_id
        JOIN conversations c ON m.conversation_id = c.conversation_id
        WHERE messages_fts MATCH ?
        ORDER BY m.created_at DESC
        LIMIT ?
    """, (query, limit))
    
    results = cursor.fetchall()
    conn.close()
    return results
```

### 2. 搜索摘要（全文搜索）

```python
def search_summaries(query, limit=20):
    """
    在摘要全文搜索索引中搜索
    """
    import sqlite3
    conn = sqlite3.connect('/home/YangYishuo/.openclaw/lcm.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT s.summary_id, s.content, s.earliest_at, s.latest_at, s.depth, c.session_key
        FROM summaries_fts fts
        JOIN summaries s ON fts.rowid = s.summary_id
        JOIN conversations c ON s.conversation_id = c.conversation_id
        WHERE summaries_fts MATCH ?
        ORDER BY s.latest_at DESC
        LIMIT ?
    """, (query, limit))
    
    results = cursor.fetchall()
    conn.close()
    return results
```

### 3. 获取对话消息

```python
def get_conversation_messages(conversation_id, limit=100, offset=0):
    """
    获取指定对话的消息
    """
    import sqlite3
    conn = sqlite3.connect('/home/YangYishuo/.openclaw/lcm.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT message_id, role, content, token_count, created_at
        FROM messages
        WHERE conversation_id = ?
        ORDER BY seq DESC
        LIMIT ? OFFSET ?
    """, (conversation_id, limit, offset))
    
    results = cursor.fetchall()
    conn.close()
    return results
```

### 4. 列出所有对话

```python
def list_conversations(limit=50):
    """
    列出所有对话
    """
    import sqlite3
    conn = sqlite3.connect('/home/YangYishuo/.openclaw/lcm.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT c.conversation_id, c.session_key, c.title, c.created_at, c.updated_at,
               COUNT(m.message_id) as message_count
        FROM conversations c
        LEFT JOIN messages m ON c.conversation_id = m.conversation_id
        GROUP BY c.conversation_id
        ORDER BY c.updated_at DESC
        LIMIT ?
    """, (limit,))
    
    results = cursor.fetchall()
    conn.close()
    return results
```

### 5. 综合搜索（消息 + 摘要）

```python
def search_all(query, limit=30):
    """
    同时搜索消息和摘要
    """
    import sqlite3
    conn = sqlite3.connect('/home/YangYishuo/.openclaw/lcm.db')
    cursor = conn.cursor()
    
    results = []
    
    # 搜索消息
    try:
        cursor.execute("""
            SELECT 'message' as type, m.message_id, m.role, m.content, m.created_at, c.session_key
            FROM messages_fts fts
            JOIN messages m ON fts.rowid = m.message_id
            JOIN conversations c ON m.conversation_id = c.conversation_id
            WHERE messages_fts MATCH ?
            ORDER BY m.created_at DESC
            LIMIT ?
        """, (query, limit))
        results.extend(cursor.fetchall())
    except:
        pass
    
    # 搜索摘要
    try:
        cursor.execute("""
            SELECT 'summary' as type, s.summary_id, s.content, s.earliest_at, s.latest_at, c.session_key
            FROM summaries_fts fts
            JOIN summaries s ON fts.rowid = s.summary_id
            JOIN conversations c ON s.conversation_id = c.conversation_id
            WHERE summaries_fts MATCH ?
            ORDER BY s.latest_at DESC
            LIMIT ?
        """, (query, limit))
        results.extend(cursor.fetchall())
    except:
        pass
    
    conn.close()
    return results
```

## CLI 工具

```bash
# 搜索消息
python3 ~/.openclaw/skills/lcm-direct/scripts/lcm_search.py messages "翻译"

# 搜索摘要
python3 ~/.openclaw/skills/lcm-direct/scripts/lcm_search.py summaries "MyGO"

# 综合搜索
python3 ~/.openclaw/skills/lcm-direct/scripts/lcm_search.py all "错误"

# 列出对话
python3 ~/.openclaw/skills/lcm-direct/scripts/lcm_search.py conversations
```

## 使用示例

在对话中：

```
用户：帮我搜索之前关于 HandyGram 的讨论
助手：[调用 search_all("HandyGram")，返回结果]
```

## 注意事项

1. 数据库可能有 WAL 文件，确保数据库一致性
2. 全文搜索使用 SQLite FTS5 语法
3. 大量结果时注意性能
