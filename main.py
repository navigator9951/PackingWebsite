from fastapi import FastAPI, HTTPException, Path, Body, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Union, Optional, Any
import yaml
import os
import re
import json

app = FastAPI()

# Define static asset routes first to prevent conflicts with dynamic routes
@app.get("/index.js", response_class=HTMLResponse)
async def base_script():
    with open("index.js", "r") as f:
        return HTMLResponse(f.read(), media_type="text/javascript")

@app.get("/favicon.ico", response_class=FileResponse)
async def favicon():
    return FileResponse("favicon.ico")

# Define dynamic routes after static routes
@app.get("/", response_class=HTMLResponse)
async def root():
    # Default route will return 404
    raise HTTPException(status_code=404, detail="Not found")

@app.get("/{store_id}", response_class=HTMLResponse)
async def store_page(store_id: str = Path(..., regex=r"^\d{1,4}$")):
    with open("index.html", "r") as f:
        return f.read()

@app.get("/{store_id}/price_editor", response_class=HTMLResponse)
async def price_editor(store_id: str = Path(..., regex=r"^\d{1,4}$")):
    # Check if the store's YAML file exists
    yaml_file = f"store{store_id}.yml"
    if not os.path.exists(yaml_file):
        raise HTTPException(status_code=404, detail=f"Store configuration not found for store {store_id}")

    # Load the price editor HTML
    with open("price_editor.html", "r") as f:
        html_content = f.read()

    # Replace the title to include the store number
    html_content = html_content.replace("Box Price Editor - Store 2", f"Box Price Editor - Store {store_id}")

    return html_content

@app.get("/api/store/{store_id}/boxes", response_class=JSONResponse)
async def get_boxes(store_id: str = Path(..., regex=r"^\d{1,4}$")):
    yaml_file = f"store{store_id}.yml"

    if not os.path.exists(yaml_file):
        error_msg = f"Store configuration file not found at {yaml_file}"
        print(f"Error: {error_msg}")
        raise HTTPException(status_code=404, detail=error_msg)

    with open(yaml_file, "r") as f:
        try:
            boxes_data = yaml.safe_load(f)
        except Exception as e:
            print(f"YAML parsing error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"YAML parsing error: {str(e)}")

    # Validate the structure of the YAML data
    if not boxes_data or "boxes" not in boxes_data or not isinstance(boxes_data["boxes"], list):
        error_msg = "Invalid YAML structure: must contain a 'boxes' list"
        print(f"Error: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

    # Validate each box entry
    for i, box in enumerate(boxes_data["boxes"]):
        if "type" not in box:
            raise HTTPException(status_code=500, detail=f"Box at index {i} missing 'type' field")
        if "dimensions" not in box or not isinstance(box["dimensions"], list) or len(box["dimensions"]) != 3:
            raise HTTPException(status_code=500, detail=f"Box at index {i} has invalid 'dimensions' (must be list of 3 numbers)")
        if "prices" not in box or not isinstance(box["prices"], list) or len(box["prices"]) != 4:
            raise HTTPException(status_code=500, detail=f"Box at index {i} has invalid 'prices' (must be list of 4 numbers)")
        if box["type"] == "CustomBox" and "open_dim" not in box:
            raise HTTPException(status_code=500, detail=f"Box at index {i} is CustomBox but missing 'open_dim' field")

        # Optional fields validation
        if "supplier" in box and not isinstance(box["supplier"], str):
            raise HTTPException(status_code=500, detail=f"Box at index {i} has invalid 'supplier' (must be a string)")
        if "model" in box and not isinstance(box["model"], str):
            raise HTTPException(status_code=500, detail=f"Box at index {i} has invalid 'model' (must be a string)")
        if "location" in box and not isinstance(box["location"], str):
            raise HTTPException(status_code=500, detail=f"Box at index {i} has invalid 'location' (must be a string)")
        if "alternate_depths" in box:
            if not isinstance(box["alternate_depths"], list):
                raise HTTPException(status_code=500, detail=f"Box at index {i} has invalid 'alternate_depths' (must be a list of numbers)")
            for depth in box["alternate_depths"]:
                if not isinstance(depth, (int, float)):
                    raise HTTPException(status_code=500, detail=f"Box at index {i} has invalid value in 'alternate_depths' (must be numbers)")

    return boxes_data


# Helper function to load and validate YAML
def load_store_yaml(store_id: str):
    yaml_file = f"store{store_id}.yml"

    if not os.path.exists(yaml_file):
        error_msg = f"Store configuration file not found at {yaml_file}"
        print(f"Error: {error_msg}")
        raise HTTPException(status_code=404, detail=error_msg)

    with open(yaml_file, "r") as f:
        try:
            boxes_data = yaml.safe_load(f)
        except Exception as e:
            print(f"YAML parsing error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"YAML parsing error: {str(e)}")

    # Validate the structure of the YAML data
    if not boxes_data or "boxes" not in boxes_data or not isinstance(boxes_data["boxes"], list):
        error_msg = "Invalid YAML structure: must contain a 'boxes' list"
        print(f"Error: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

    # Set default editable flag if not present
    if "editable" not in boxes_data:
        boxes_data["editable"] = False

    return boxes_data

# Helper function to save YAML data
def save_store_yaml(store_id: str, data: dict):
    yaml_file = f"store{store_id}.yml"

    try:
        # Custom YAML writing to maintain the desired format
        with open(yaml_file, "w") as f:
            # Write editable flag at the top level
            editable = data.get("editable", False)
            f.write(f"editable: {str(editable).lower()}\n")

            f.write("boxes:\n")

            # Write each box in a nice format
            for box in data["boxes"]:
                # Always write the type
                f.write(f"  - type: {box['type']}\n")

                # Handle supplier field
                if store_id == "1" and "supplier" not in box:
                    # Skip supplier field for store1 if not present to maintain legacy format
                    pass
                else:
                    supplier = box.get('supplier', 'Unknown')
                    f.write(f"    supplier: {supplier}\n")

                # Handle model field
                if store_id == "1" and "model" not in box:
                    # Skip model field for store1 if not present to maintain legacy format
                    pass
                else:
                    model = box.get('model', f"Unknown-{box['dimensions'][0]}-{box['dimensions'][1]}-{box['dimensions'][2]}")
                    f.write(f"    model: \"{model}\"\n")

                # Safely format dimensions with square brackets and commas, no spaces
                # Use a safer approach to prevent YAML injection
                if isinstance(box['dimensions'], list) and len(box['dimensions']) == 3:
                    dimensions = [float(d) if isinstance(d, (int, float)) else 0 for d in box['dimensions']]
                    dimensions_str = str(dimensions).replace(" ", "")
                    f.write(f"    dimensions: {dimensions_str}\n")
                else:
                    f.write(f"    dimensions: [0,0,0]\n")

                # Add alternate_depths if present
                if "alternate_depths" in box and isinstance(box['alternate_depths'], list):
                    # Validate depths are numeric and reasonable
                    alt_depths = [float(d) if isinstance(d, (int, float)) and 0 <= d <= 100 else 0 for d in box['alternate_depths']]
                    alt_depths_str = str(alt_depths).replace(" ", "")
                    f.write(f"    alternate_depths: {alt_depths_str}\n")

                # Safely format prices with square brackets and commas, no spaces
                if isinstance(box['prices'], list) and len(box['prices']) == 4:
                    # Validate prices are numeric and in reasonable range
                    prices = [float(p) if isinstance(p, (int, float)) and 0 <= p <= 10000 else 0 for p in box['prices']]
                    prices_str = str(prices).replace(" ", "")
                    f.write(f"    prices: {prices_str}\n")
                else:
                    f.write(f"    prices: [0.0,0.0,0.0,0.0]\n")

                # Add location if present
                if store_id == "1" and "location" not in box:
                    # Skip location field for store1 if not present to maintain legacy format
                    pass
                else:
                    # Sanitize location to prevent YAML injection
                    location = box.get('location', '')
                    if location and isinstance(location, str):
                        # Escape quotes and sanitize
                        location = location.replace('"', '\\"').replace('\n', ' ').replace(':', '_')
                        # Limit length
                        location = location[:50]
                    else:
                        location = ""
                    f.write(f"    location: \"{location}\"\n")

                f.write("\n")

        return True
    except Exception as e:
        print(f"Error saving YAML: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving YAML: {str(e)}")

# Define box sections based on model patterns
def get_box_section(model: str):
    if any(model.endswith(suffix) for suffix in ["C-UPS", "C", "Cube"]):
        return "CUBE BOXES"
    elif any(x in model for x in ["X 4", "X 3", "X 6", "J-11", "J-14", "J-15", "J-16", "SHIRTB"]):
        return "FLAT & SMALL BOXES"
    elif any(x in model for x in ["J-20", "WREATH", "ST-6", "MIR-3", "MIR-8"]):
        return "MEDIUM BOXES"
    elif any(x in model for x in ["J-64", "SUITCASE", "VCR", "24 X 18 X 18"]):
        return "LARGE BOXES"
    else:
        return "SPECIALTY BOXES"

# Get boxes formatted for the editor with sections
@app.get("/api/store/{store_id}/boxes_with_sections", response_class=JSONResponse)
async def get_boxes_with_sections(store_id: str = Path(..., regex=r"^\d{1,4}$")):
    data = load_store_yaml(store_id)
    result = []

    for box in data["boxes"]:
        # Handle legacy format (missing model and location)
        model = box.get("model", f"Unknown-{len(box['dimensions'])}-{box['dimensions'][0]}-{box['dimensions'][1]}-{box['dimensions'][2]}")

        # Use a placeholder section for boxes without model
        if "model" in box:
            section = get_box_section(model)
        else:
            section = "UNKNOWN BOXES"

        dimensions_str = " × ".join(str(d) for d in box["dimensions"])

        result.append({
            "section": section,
            "model": model,
            "dimensions": dimensions_str,
            "box_price": box["prices"][0],
            "standard": box["prices"][1],
            "fragile": box["prices"][2],
            "custom": box["prices"][3],
            "location": box.get("location", "???")
        })

    # Sort by section and then by model
    result.sort(key=lambda x: (x["section"], x["model"]))

    return result

# Get a single box by model
@app.get("/api/store/{store_id}/box/{model}", response_class=JSONResponse)
async def get_box_by_model(
    store_id: str = Path(..., regex=r"^\d{1,4}$"),
    model: str = Path(...)):

    data = load_store_yaml(store_id)

    for box in data["boxes"]:
        # Handle legacy format and compare with the provided model
        box_model = box.get("model", f"Unknown-{len(box['dimensions'])}-{box['dimensions'][0]}-{box['dimensions'][1]}-{box['dimensions'][2]}")

        if box_model == model:
            # For legacy boxes, ensure all fields exist
            if "model" not in box:
                box["model"] = box_model
            if "supplier" not in box:
                box["supplier"] = "Unknown"
            if "location" not in box:
                box["location"] = "???"

            return box

    raise HTTPException(status_code=404, detail=f"Box with model {model} not found")

# Define the request model for price updates with CSRF protection
class PriceUpdateRequest(BaseModel):
    changes: Dict[str, Dict[str, float]]
    csrf_token: str

# Update prices for multiple boxes
@app.post("/api/store/{store_id}/update_prices", response_class=JSONResponse)
async def update_prices(
    store_id: str = Path(..., regex=r"^\d{1,4}$"),
    update_data: PriceUpdateRequest = Body(...)):

    # Extract data from the request
    changes = update_data.changes

    # Validate CSRF token - normally you would check against a server-stored token
    # This is a simple check to ensure the token is present
    if not update_data.csrf_token or len(update_data.csrf_token) < 10:
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    data = load_store_yaml(store_id)

    # Check if the store is editable
    if not data.get("editable", False):
        raise HTTPException(status_code=403, detail="This store is not editable. Set 'editable: true' in the store YAML file to enable editing.")

    updated_count = 0

    # Update prices for each box in the changes dict
    for box in data["boxes"]:
        # Get the actual model or generate a default one for legacy boxes
        box_model = box.get("model", f"Unknown-{len(box['dimensions'])}-{box['dimensions'][0]}-{box['dimensions'][1]}-{box['dimensions'][2]}")

        if box_model in changes:
            price_changes = changes[box_model]

            for index, new_price in price_changes.items():
                idx = int(index)
                # Validate price - must be a positive number within a reasonable range
                if 0 <= idx < 4 and isinstance(new_price, (int, float)) and 0 <= new_price <= 10000:
                    box["prices"][idx] = new_price
                    updated_count += 1
                else:
                    raise HTTPException(status_code=400, detail=f"Invalid price value: {new_price}. Prices must be between 0 and 10000.")

            # If this is a legacy box and we're updating it, add the model field
            # so we can reference it again in the future
            if "model" not in box:
                box["model"] = box_model

    # Save the updated YAML file while preserving the editable flag
    save_store_yaml(store_id, data)

    return {"message": f"Updated {updated_count} prices successfully"}

class Comment(BaseModel):
    text: str

# Check if a store is editable
@app.get("/api/store/{store_id}/is_editable", response_class=JSONResponse)
async def is_store_editable(store_id: str = Path(..., regex=r"^\d{1,4}$")):
    data = load_store_yaml(store_id)
    return {"editable": data.get("editable", False)}

@app.post("/comments")
async def save_comment(comment: Comment):
    with open("comments.txt", "a") as f:
        f.write(comment.text + "\n")