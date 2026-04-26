import sqlite3
import time
from contextlib import contextmanager
from typing import List, Dict, Optional

DATABASE = "sentences.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sentences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hitokoto TEXT NOT NULL,
                author TEXT NOT NULL,
                commit_from TEXT,
                created_at INTEGER NOT NULL,
                length INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sentence_categories (
                sentence_id INTEGER,
                category_id INTEGER,
                FOREIGN KEY (sentence_id) REFERENCES sentences(id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
                PRIMARY KEY (sentence_id, category_id)
            );
            CREATE INDEX IF NOT EXISTS idx_sentence_category ON sentence_categories(category_id);
        """)
        # 可选：预置默认分类
        conn.execute("INSERT OR IGNORE INTO categories (name) VALUES ('默认分类')")

def _current_timestamp() -> int:
    return int(time.time())

# ---------- 分类操作 ----------
def get_or_create_category(conn, name: str) -> int:
    """获取分类ID，不存在则创建"""
    cur = conn.execute("SELECT id FROM categories WHERE name = ?", (name.strip(),))
    row = cur.fetchone()
    if row:
        return row["id"]
    cur = conn.execute("INSERT INTO categories (name) VALUES (?)", (name.strip(),))
    return cur.lastrowid

def get_all_categories(conn) -> List[str]:
    cur = conn.execute("SELECT name FROM categories ORDER BY name")
    return [row["name"] for row in cur.fetchall()]

def delete_category(conn, name: str) -> bool:
    """删除分类，同时删除所有关联（句子不受影响，只是失去该分类）"""
    cur = conn.execute("DELETE FROM categories WHERE name = ?", (name,))
    return cur.rowcount > 0

# ---------- 句子 CRUD ----------
def add_sentence(conn, hitokoto: str, author: str, categories: List[str], commit_from: str = "web") -> int:
    if not hitokoto.strip():
        raise ValueError("句子内容不能为空")
    if not author or not author.strip():
        author = "默认作者"
    now = _current_timestamp()
    length = len(hitokoto)
    cur = conn.execute("""
        INSERT INTO sentences (hitokoto, author, commit_from, created_at, length)
        VALUES (?, ?, ?, ?, ?)
    """, (hitokoto.strip(), author.strip(), commit_from.strip(), now, length))
    sentence_id = cur.lastrowid

    # 处理分类
    if not categories:
        # 如果没有指定任何分类，则赋予默认分类
        default_id = get_or_create_category(conn, "默认分类")
        conn.execute("INSERT INTO sentence_categories (sentence_id, category_id) VALUES (?, ?)", (sentence_id, default_id))
    else:
        for cat_name in categories:
            if cat_name and cat_name.strip():
                cat_id = get_or_create_category(conn, cat_name.strip())
                conn.execute("INSERT INTO sentence_categories (sentence_id, category_id) VALUES (?, ?)", (sentence_id, cat_id))
    return sentence_id

def update_sentence(conn, sid: int, hitokoto: str, author: str, categories: List[str], commit_from: str) -> bool:
    if not hitokoto.strip():
        raise ValueError("句子内容不能为空")
    if not author or not author.strip():
        author = "默认作者"
    cur = conn.execute("""
        UPDATE sentences SET hitokoto=?, author=?, commit_from=?, length=?
        WHERE id=?
    """, (hitokoto.strip(), author.strip(), commit_from.strip(), len(hitokoto), sid))
    if cur.rowcount == 0:
        return False
    # 更新分类：先删除旧关联，再添加新关联
    conn.execute("DELETE FROM sentence_categories WHERE sentence_id = ?", (sid,))
    if not categories:
        default_id = get_or_create_category(conn, "默认分类")
        conn.execute("INSERT INTO sentence_categories (sentence_id, category_id) VALUES (?, ?)", (sid, default_id))
    else:
        for cat_name in categories:
            if cat_name and cat_name.strip():
                cat_id = get_or_create_category(conn, cat_name.strip())
                conn.execute("INSERT INTO sentence_categories (sentence_id, category_id) VALUES (?, ?)", (sid, cat_id))
    return True

def delete_sentence(conn, sid: int) -> bool:
    cur = conn.execute("DELETE FROM sentences WHERE id=?", (sid,))
    return cur.rowcount > 0

def get_sentence_by_id(conn, sid: int) -> Optional[Dict]:
    cur = conn.execute("SELECT id, hitokoto, author, commit_from, created_at, length FROM sentences WHERE id=?", (sid,))
    row = cur.fetchone()
    if not row:
        return None
    sentence = dict(row)
    # 获取该句子的分类列表
    cur_cat = conn.execute("""
        SELECT c.name FROM categories c
        JOIN sentence_categories sc ON c.id = sc.category_id
        WHERE sc.sentence_id = ?
    """, (sid,))
    sentence["categories"] = [row_cat["name"] for row_cat in cur_cat.fetchall()]
    return sentence

def list_sentences(conn, page: int = 1, limit: int = 20) -> tuple[List[Dict], int]:
    offset = (page - 1) * limit
    cur = conn.execute("""
        SELECT id, hitokoto, author, commit_from, created_at, length
        FROM sentences ORDER BY id DESC LIMIT ? OFFSET ?
    """, (limit, offset))
    items = []
    for row in cur.fetchall():
        s = dict(row)
        # 获取分类
        cur_cat = conn.execute("""
            SELECT c.name FROM categories c
            JOIN sentence_categories sc ON c.id = sc.category_id
            WHERE sc.sentence_id = ?
        """, (s["id"],))
        s["categories"] = [c["name"] for c in cur_cat.fetchall()]
        items.append(s)
    total = conn.execute("SELECT COUNT(*) as cnt FROM sentences").fetchone()["cnt"]
    return items, total

def random_sentence(conn, category: str = None) -> Optional[Dict]:
    """随机获取句子，如果指定category，则获取包含该分类的句子中的随机一条"""
    if category:
        sql = """
            SELECT s.id, s.hitokoto, s.author, s.commit_from, s.created_at, s.length
            FROM sentences s
            JOIN sentence_categories sc ON s.id = sc.sentence_id
            JOIN categories c ON sc.category_id = c.id
            WHERE c.name = ?
            ORDER BY RANDOM() LIMIT 1
        """
        cur = conn.execute(sql, (category.strip(),))
    else:
        sql = "SELECT id, hitokoto, author, commit_from, created_at, length FROM sentences ORDER BY RANDOM() LIMIT 1"
        cur = conn.execute(sql)
    row = cur.fetchone()
    if not row:
        return None
    sentence = dict(row)
    # 获取分类列表（可选，便于前端显示）
    cur_cat = conn.execute("""
        SELECT c.name FROM categories c
        JOIN sentence_categories sc ON c.id = sc.category_id
        WHERE sc.sentence_id = ?
    """, (sentence["id"],))
    sentence["categories"] = [c["name"] for c in cur_cat.fetchall()]
    return sentence

# ---------- 导入导出（适配多分类）----------
def import_sentences(conn, sentences_list: List[dict], replace: bool = False) -> int:
    if replace:
        conn.execute("DELETE FROM sentences")
    count = 0
    for item in sentences_list:
        try:
            hitokoto = item.get("hitokoto", "").strip()
            if not hitokoto:
                continue
            author = item.get("author", "").strip()
            if not author:
                author = "默认作者"
            commit_from = item.get("commit_from", "import")
            created_at = item.get("created_at", _current_timestamp())
            length = item.get("length", len(hitokoto))
            # 分类处理：可能字段叫 categories (list) 或 type (旧格式兼容)
            categories = item.get("categories", [])
            if not categories and "type" in item:
                # 兼容旧的单分类
                categories = [item["type"]]
            cur = conn.execute("""
                INSERT INTO sentences (hitokoto, author, commit_from, created_at, length)
                VALUES (?, ?, ?, ?, ?)
            """, (hitokoto, author, commit_from, created_at, length))
            sid = cur.lastrowid
            # 添加分类
            if not categories:
                default_id = get_or_create_category(conn, "默认分类")
                conn.execute("INSERT INTO sentence_categories (sentence_id, category_id) VALUES (?, ?)", (sid, default_id))
            else:
                for cat_name in categories:
                    if cat_name and cat_name.strip():
                        cat_id = get_or_create_category(conn, cat_name.strip())
                        conn.execute("INSERT INTO sentence_categories (sentence_id, category_id) VALUES (?, ?)", (sid, cat_id))
            count += 1
        except Exception as e:
            # 打印错误以便调试，但继续导入其他
            print(f"导入失败: {e}")
            continue
    return count

def export_all_sentences(conn) -> List[Dict]:
    cur = conn.execute("SELECT id, hitokoto, author, commit_from, created_at, length FROM sentences ORDER BY id")
    sentences = []
    for row in cur.fetchall():
        s = dict(row)
        cur_cat = conn.execute("""
            SELECT c.name FROM categories c
            JOIN sentence_categories sc ON c.id = sc.category_id
            WHERE sc.sentence_id = ?
        """, (s["id"],))
        s["categories"] = [c["name"] for c in cur_cat.fetchall()]
        sentences.append(s)
    return sentences