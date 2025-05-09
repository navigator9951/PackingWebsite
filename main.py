from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
async def root():
    with open("index.html", "r") as f:
        return f.read()

@app.get("/index.js", response_class=HTMLResponse)
async def base_script():
    with open("index.js", "r") as f:
        return HTMLResponse(f.read(), media_type="text/javascript")

@app.get("/favicon.ico", response_class=FileResponse)
async def favicon():
    return FileResponse("favicon.ico")


class Comment(BaseModel):
    text: str

@app.post("/comments")
async def save_comment(comment: Comment):
    with open("comments.txt", "a") as f:
        f.write(comment.text + "\n")

