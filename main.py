from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import json
import database as db

@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield

app = FastAPI(lifespan=lifespan, title="多分类句子API")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

# ---------- API ----------
@app.get("/api/random")
async def random_sentence(category: str = Query(None, description="分类名")):
    with db.get_db() as conn:
        sentence = db.random_sentence(conn, category)
    if not sentence:
        raise HTTPException(404, "没有找到符合条件的句子")
    return sentence

@app.get("/api/sentences")
async def list_sentences(page: int = 1, limit: int = 20):
    with db.get_db() as conn:
        items, total = db.list_sentences(conn, page, min(limit, 100))
    return {"total": total, "page": page, "items": items}

@app.post("/api/sentences")
async def add_sentence(data: dict):
    hitokoto = data.get("hitokoto")
    author = data.get("author")
    categories = data.get("categories", [])
    commit_from = data.get("commit_from", "web")
    if not hitokoto or not author:
        raise HTTPException(400, "hitokoto 和 author 不能为空")
    with db.get_db() as conn:
        sid = db.add_sentence(conn, hitokoto, author, categories, commit_from)
        conn.commit()
        new_sentence = db.get_sentence_by_id(conn, sid)
        return new_sentence

@app.put("/api/sentences/{sid}")
async def update_sentence(sid: int, data: dict):
    hitokoto = data.get("hitokoto")
    author = data.get("author")
    categories = data.get("categories", [])
    commit_from = data.get("commit_from")
    if not all([hitokoto, author, commit_from is not None]):
        raise HTTPException(400, "缺少必要字段")
    with db.get_db() as conn:
        ok = db.update_sentence(conn, sid, hitokoto, author, categories, commit_from)
        if not ok:
            raise HTTPException(404, "句子不存在")
        conn.commit()
        updated = db.get_sentence_by_id(conn, sid)
        return updated

@app.delete("/api/sentences/{sid}")
async def delete_sentence(sid: int):
    with db.get_db() as conn:
        ok = db.delete_sentence(conn, sid)
        if not ok:
            raise HTTPException(404, "句子不存在")
        conn.commit()
    return {"status": "deleted"}

@app.get("/api/categories")
async def get_categories():
    with db.get_db() as conn:
        categories = db.get_all_categories(conn)
    return {"categories": categories}

@app.post("/api/categories")
async def add_category(name: str):
    with db.get_db() as conn:
        db.get_or_create_category(conn, name)
        conn.commit()
    return {"status": "created", "name": name}

@app.delete("/api/categories/{name}")
async def delete_category(name: str):
    with db.get_db() as conn:
        ok = db.delete_category(conn, name)
        conn.commit()
        if not ok:
            raise HTTPException(404, "分类不存在")
    return {"status": "deleted"}

@app.post("/api/import")
async def import_sentences(file: UploadFile = File(...), replace: bool = Form(False)):
    content = await file.read()
    try:
        data = json.loads(content)
        if not isinstance(data, list):
            raise ValueError
    except:
        raise HTTPException(400, "文件必须是 JSON 数组")
    with db.get_db() as conn:
        count = db.import_sentences(conn, data, replace)
        conn.commit()
    return {"imported": count}

@app.get("/api/export")
async def export_sentences():
    with db.get_db() as conn:
        all_sentences = db.export_all_sentences(conn)
    return JSONResponse(content=all_sentences, headers={
        "Content-Disposition": "attachment; filename=sentences.json"
    })