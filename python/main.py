import os
import json
import logging
import pathlib
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
logger = logging.getLogger("uvicorn")
logger.level = logging.INFO
images = pathlib.Path(__file__).parent.resolve() / "images"
origins = [os.environ.get('FRONT_URL', 'http://localhost:3000')]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

PATH_ITEMS = "./data/items.json"
ENCODING = "utf-8"


@app.get("/")
def root():
    return {"message": "Hello, world!"}


@app.post("/items")
def add_item(name: str = Form(...), category: str = Form(...)):
    logger.info(f"Receive item: {name}")
    try:
        #ファイルが存在する場合
        with open(PATH_ITEMS, 'r', encoding=ENCODING) as f:
            data = json.load(f)
            data['items'].append({"name": name, "category": category})
    except FileNotFoundError:
        #ファイルが存在しない場合
        print("File not found.")
        data = {"items": [{"name": name, "category": category}]}
    try:
        with open(PATH_ITEMS, 'w', encoding=ENCODING) as f:
            json.dump(data, f)
    except Exception as error:
        print(error)
    return {"message": f"item received: {name}"}


@app.get("/items")
def get_items():
    try:
        with open(PATH_ITEMS, 'r', encoding=ENCODING) as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="items not found.")


@app.get("/image/{image_filename}")
async def get_image(image_filename):
    # Create image path
    image = images / image_filename

    if not image_filename.endswith(".jpg"):
        raise HTTPException(status_code=400, detail="Image path does not end with .jpg")

    if not image.exists():
        logger.debug(f"Image not found: {image}")
        image = images / "default.jpg"

    return FileResponse(image)