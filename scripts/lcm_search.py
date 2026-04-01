#!/usr/bin/env python3
"""
LCM Direct - 直接读取 LCM 数据库

用法：
    python3 lcm_search.py messages "搜索词"
    python3 lcm_search.py summaries "搜索词"
    python3 lcm_search.py all "搜索词"
    python3 lcm_search.py conversations
    python3 lcm_search.py stats
"""

import sqlite3
import sys
import json
from pathlib import Path

DB_PATH = Path.home() / ".openclaw" / "lcm.db"


def get_connection():
    """获取数据库连接"""
    return sqlite3.connect(DB_PATH)


def search_messages(query: str, limit: int = 30):
    """搜索消息"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # FTS5 搜索
        cursor.execute("""
            SELECT m.message_id, m.role, m.content, m.created_at, c.session_key
            FROM messages_fts fts
            JOIN messages m ON fts.rowid = m.message_id
            JOIN conversations c ON m.conversation_id = c.conversation_id
            WHERE messages_fts MATCH ?
            ORDER BY m.created_at DESC
            LIMIT ?
        """, (query, limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "type": "message",
                "id": row[0],
                "role": row[1],
                "content": row[2][:500] + "..." if len(row[2]) > 500 else row[2],
                "created_at": row[3],
                "session": row[4]
            })
        
        return results
    except sqlite3.OperationalError as e:
        return [{"error": str(e)}]
    finally:
        conn.close()


def search_summaries(query: str, limit: int = 20):
    """搜索摘要"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT s.summary_id, s.content, s.earliest_at, s.latest_at, s.depth, c.session_key
            FROM summaries_fts fts
            JOIN summaries s ON fts.rowid = s.summary_id
            JOIN conversations c ON s.conversation_id = c.conversation_id
            WHERE summaries_fts MATCH ?
            ORDER BY s.latest_at DESC
            LIMIT ?
        """, (query, limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "type": "summary",
                "id": row[0],
                "content": row[1][:800] + "..." if len(row[1]) > 800 else row[1],
                "earliest_at": row[2],
                "latest_at": row[3],
                "depth": row[4],
                "session": row[5]
            })
        
        return results
    except sqlite3.OperationalError as e:
        return [{"error": str(e)}]
    finally:
        conn.close()


def search_all(query: str, limit: int = 30):
    """综合搜索"""
    messages = search_messages(query, limit // 2)
    summaries = search_summaries(query, limit // 2)
    
    # 合并并按时间排序
    results = []
    for m in messages:
        if "error" not in m:
            results.append(m)
    for s in summaries:
        if "error" not in s:
            results.append(s)
    
    return results


def list_conversations(limit: int = 50):
    """列出所有对话"""
    conn = get_connection()
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
    
    results = []
    for row in cursor.fetchall():
        results.append({
            "conversation_id": row[0],
            "session_key": row[1],
            "title": row[2],
            "created_at": row[3],
            "updated_at": row[4],
            "message_count": row[5]
        })
    
    conn.close()
    return results


def get_stats():
    """获取数据库统计"""
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    # 消息数
    cursor.execute("SELECT COUNT(*) FROM messages")
    stats["messages"] = cursor.fetchone()[0]
    
    # 摘要数
    cursor.execute("SELECT COUNT(*) FROM summaries")
    stats["summaries"] = cursor.fetchone()[0]
    
    # 对话数
    cursor.execute("SELECT COUNT(*) FROM conversations")
    stats["conversations"] = cursor.fetchone()[0]
    
    # 数据库大小
    db_size = DB_PATH.stat().st_size
    stats["db_size_mb"] = round(db_size / 1024 / 1024, 2)
    
    # 最早和最新消息
    cursor.execute("SELECT MIN(created_at), MAX(created_at) FROM messages")
    row = cursor.fetchone()
    stats["earliest_message"] = row[0]
    stats["latest_message"] = row[1]
    
    conn.close()
    return stats


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "messages":
        if len(sys.argv) < 3:
            print("用法: lcm_search.py messages <搜索词>")
            sys.exit(1)
        query = sys.argv[2]
        results = search_messages(query)
        print(json.dumps(results, ensure_ascii=False, indent=2))
    
    elif command == "summaries":
        if len(sys.argv) < 3:
            print("用法: lcm_search.py summaries <搜索词>")
            sys.exit(1)
        query = sys.argv[2]
        results = search_summaries(query)
        print(json.dumps(results, ensure_ascii=False, indent=2))
    
    elif command == "all":
        if len(sys.argv) < 3:
            print("用法: lcm_search.py all <搜索词>")
            sys.exit(1)
        query = sys.argv[2]
        results = search_all(query)
        print(json.dumps(results, ensure_ascii=False, indent=2))
    
    elif command == "conversations":
        results = list_conversations()
        print(json.dumps(results, ensure_ascii=False, indent=2))
    
    elif command == "stats":
        results = get_stats()
        print(json.dumps(results, ensure_ascii=False, indent=2))
    
    else:
        print(f"未知命令: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
