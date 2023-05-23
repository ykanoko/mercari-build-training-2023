import os
import hashlib
import json
import logging
import pathlib
import sqlite3
# import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
logger = logging.getLogger("uvicorn")
logger.level = logging.INFO
path_items = pathlib.Path(__file__).parent.resolve() / "data/items.json"
path_images = pathlib.Path(__file__).parent.resolve() / "images"
path_db_items = pathlib.Path(__file__).parent.resolve() / "../db/mercari.sqlite3"
origins = [os.environ.get('FRONT_URL', 'http://localhost:3000')]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
#ファイル（mercari.sqlite3）の作成
# con = sqlite3.connect(path_db_items)
# cur = con.cursor()
# cur.execute(
#     'CREATE TABLE items (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, category_id INTEGER, image_filename TEXT)'
# )
# cur.execute('CREATE TABLE category (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)')
# con.close()

ENCODING = "utf-8"


@app.get("/")
def root():
    return {"message": "Hello, world!"}


@app.post("/items")
def add_item(name: str = Form(...), category: str = Form(...), image: UploadFile = File(...)):
    logger.info(f"Receive item: {name}")
    #画像の保存
    content = image.file.read()
    file_name = hashlib.sha256(content).hexdigest() + '.jpg'
    path_file = str(path_images) + '/' + file_name
    with open(path_file, 'w+b') as f:
        f.write(content)
        # shutil.copyfileobj(image.file, f)

    con = sqlite3.connect(path_db_items)
    cur = con.cursor()

    try:
        res = cur.execute("SELECT id FROM category WHERE name = ? ", (category, ))
        category_id = res.fetchone()[0]
    except:
        cur.execute('INSERT INTO category (name) VALUES (?)', (category, ))
        category_id = cur.lastrowid
    cur.execute('INSERT INTO items (name, category_id, image_filename) VALUES (?, ?, ?)',
                (name, category_id, file_name))
    con.commit()
    con.close()
    return {"message": f"item received: {name}"}


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


@app.get("/items")
def get_items():
    con = sqlite3.connect(path_db_items)
    con.row_factory = dict_factory
    # con.row_factory = sqlite3.Row
    cur = con.cursor()
    #確認用
    res = cur.execute("SELECT * FROM items")
    print('items', res.fetchall())
    res = cur.execute("SELECT * FROM category")
    print('category', res.fetchall())
    res = cur.execute(
        "SELECT items.id, items.name, category.name AS category, items.image_filename FROM items INNER JOIN category ON items.category_id = category.id"
    )
    data = res.fetchall()
    data = {"items": data}
    con.commit()
    con.close()
    return data


@app.get("/items/{item_id}")
def get_items(item_id):
    con = sqlite3.connect(path_db_items)
    con.row_factory = dict_factory
    cur = con.cursor()
    res = cur.execute(
        "SELECT items.id, items.name, category.name AS category, items.image_filename FROM items INNER JOIN category ON items.category_id = category.id WHERE items.id = ?",
        (item_id, ))
    data = res.fetchone()
    if data == []:
        raise HTTPException(status_code=404, detail="item not found.")
    con.commit()
    con.close()
    return data


@app.get("/search")
def search_items(keyword: str):
    con = sqlite3.connect(path_db_items)
    con.row_factory = dict_factory
    cur = con.cursor()
    res = cur.execute(
        "SELECT items.id, items.name, category.name AS category, items.image_filename FROM items INNER JOIN category ON items.category_id = category.id WHERE items.name LIKE ?",
        ('%' + keyword + '%', ))
    data = res.fetchall()
    if data == []:
        raise HTTPException(status_code=404, detail="item not found.")
    data = {"items": data}
    con.commit()
    con.close()
    return data


@app.get("/image/{image_filename}")
async def get_image(image_filename):
    # Create image path
    image = path_images / image_filename

    if not image_filename.endswith(".jpg"):
        raise HTTPException(status_code=400, detail="Image path does not end with .jpg")

    if not image.exists():
        logger.debug(f"Image not found: {image}")
        image = path_images / "default.jpg"

    return FileResponse(image)
