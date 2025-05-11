from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel
import yaml
import os

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

@app.get("/api/boxes", response_class=JSONResponse)
async def get_boxes():
    yaml_file = "boxes.yml"

    if not os.path.exists(yaml_file):
        error_msg = f"Box configuration file not found at {yaml_file}"
        print(f"Error: {error_msg}")
        raise Exception(error_msg)

    with open(yaml_file, "r") as f:
        try:
            boxes_data = yaml.safe_load(f)
        except Exception as e:
            print(f"YAML parsing error: {str(e)}")
            raise Exception(f"YAML parsing error: {str(e)}")

    # Validate the structure of the YAML data
    if not boxes_data or "boxes" not in boxes_data or not isinstance(boxes_data["boxes"], list):
        error_msg = "Invalid YAML structure: must contain a 'boxes' list"
        print(f"Error: {error_msg}")
        raise Exception(error_msg)

    # Validate each box entry
    for i, box in enumerate(boxes_data["boxes"]):
        if "type" not in box:
            raise Exception(f"Box at index {i} missing 'type' field")
        if "dimensions" not in box or not isinstance(box["dimensions"], list) or len(box["dimensions"]) != 3:
            raise Exception(f"Box at index {i} has invalid 'dimensions' (must be list of 3 numbers)")
        if "prices" not in box or not isinstance(box["prices"], list) or len(box["prices"]) != 4:
            raise Exception(f"Box at index {i} has invalid 'prices' (must be list of 4 numbers)")
        if box["type"] == "CustomBox" and "open_dim" not in box:
            raise Exception(f"Box at index {i} is CustomBox but missing 'open_dim' field")

    return boxes_data


class Comment(BaseModel):
    text: str

@app.post("/comments")
async def save_comment(comment: Comment):
    with open("comments.txt", "a") as f:
        f.write(comment.text + "\n")