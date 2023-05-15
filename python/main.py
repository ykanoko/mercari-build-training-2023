import os
import hashlib
import json
import logging
import pathlib
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
logger = logging.getLogger("uvicorn")
logger.level = logging.INFO
path_items = pathlib.Path(__file__).parent.resolve() / "data/items.json"
path_images = pathlib.Path(__file__).parent.resolve() / "images"
origins = [os.environ.get('FRONT_URL', 'http://localhost:3000')]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

ENCODING = "utf-8"


@app.get("/")
def root():
    return {"message": "Hello, world!"}


@app.post("/items")
async def add_item(name: str = Form(...), category: str = Form(...), image: UploadFile = File(...)):
    logger.info(f"Receive item: {name}")
    #画像の保存
    content = image.file.read()
    image_filename = hashlib.sha256(content).hexdigest() + '.jpg'
    path_file = str(path_images) + '/' + image_filename
    with open(path_file, 'w+b') as f:
        f.write(content)
        # shutil.copyfileobj(image.file, f)

    #name, categoryの保存
    try:
        #ファイルが存在する場合
        with open(path_items, 'r', encoding=ENCODING) as f:
            data = json.load(f)
            data['items'].append({
                "name": name,
                "category": category,
                "image_filename": image_filename
            })
    except FileNotFoundError:
        #ファイルが存在しない場合
        print("File not found.")
        data = {"items": [{"name": name, "category": category, "image_filename": image_filename}]}
    with open(path_items, 'w', encoding=ENCODING) as f:
        json.dump(data, f)

    return {"message": f"item received: {name}"}


@app.get("/items")
def get_items():
    try:
        with open(path_items, 'r', encoding=ENCODING) as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="items not found.")


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