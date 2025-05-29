import json
import os
import re
from typing import Any, Dict, List, Optional, Union

import yaml
from fastapi import Body, FastAPI, HTTPException, Path, Request, File, UploadFile, Depends
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import aiofiles
import shutil

from lib.auth_middleware import require_store_auth, get_current_store
from lib.auth_manager import (
    init_db, verify_store_password, create_session, 
    create_store_auth, verify_session, delete_session,
    hasAuth as store_has_auth
)

# Initialize the authentication database
init_db()

app = FastAPI()

# Mount static directories
app.mount("/assets", StaticFiles(directory="assets"), name="assets")
app.mount("/lib", StaticFiles(directory="lib"), name="lib")
app.mount("/components", StaticFiles(directory="components"), name="components")

# Define static asset routes for compatibility with existing code
@app.get("/index.js", response_class=HTMLResponse)
async def base_script():
    # Add cache-busting headers
    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    }
    with open("index.js", "r") as f:
        return HTMLResponse(f.read(), media_type="text/javascript", headers=headers)

@app.get("/pricing.js", response_class=HTMLResponse)
async def pricing_script():
    # Serve pricing module from lib/pricing.js
    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    }
    with open("lib/pricing.js", "r") as f:
        return HTMLResponse(f.read(), media_type="text/javascript", headers=headers)

@app.get("/packing.js", response_class=HTMLResponse)
async def packing_script():
    # Serve packing module from lib/packing.js
    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    }
    with open("lib/packing.js", "r") as f:
        return HTMLResponse(f.read(), media_type="text/javascript", headers=headers)

@app.get("/api.js", response_class=HTMLResponse)
async def api_script():
    # Serve api module from lib/api.js
    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    }
    with open("lib/api.js", "r") as f:
        return HTMLResponse(f.read(), media_type="text/javascript", headers=headers)

@app.get("/location.js", response_class=HTMLResponse)
async def location_script():
    # Serve location module from lib/location.js
    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    }
    with open("lib/location.js", "r") as f:
        return HTMLResponse(f.read(), media_type="text/javascript", headers=headers)

@app.get("/favicon.ico", response_class=FileResponse)
async def favicon():
    return FileResponse("assets/favicon.ico")

# Define dynamic routes after static routes
@app.get("/", response_class=HTMLResponse)
async def root():
    # Default route will return 404
    raise HTTPException(status_code=404, detail="Not found")

# Login page route
@app.get("/{store_id}/login", response_class=HTMLResponse)
async def login_page(store_id: str = Path(..., regex=r"^\d{1,4}$")):
    # Check if the store's YAML file exists
    yaml_file = f"stores/store{store_id}.yml"
    if not os.path.exists(yaml_file):
        raise HTTPException(status_code=404, detail=f"Store configuration not found for store {store_id}")
        
    # Load the login HTML
    with open("login.html", "r") as f:
        return HTMLResponse(f.read())

# Catch-all pattern should be last to avoid conflicts
@app.get("/{store_id}", response_class=HTMLResponse)
async def store_page(store_id: str = Path(..., regex=r"^\d{1,4}$")):
    with open("index.html", "r") as f:
        return f.read()

@app.get("/{store_id}/price_editor", response_class=HTMLResponse)
async def price_editor(store_id: str = Path(..., regex=r"^\d{1,4}$")):
    # Check if the store's YAML file exists
    yaml_file = f"stores/store{store_id}.yml"
    if not os.path.exists(yaml_file):
        raise HTTPException(status_code=404, detail=f"Store configuration not found for store {store_id}")

    # Load the price editor HTML
    with open("price_editor.html", "r") as f:
        html_content = f.read()

    # Replace the title to include the store number
    html_content = html_content.replace("Box Price Editor - Store 2", f"Box Price Editor - Store {store_id}")
    
    # Add cache-busting headers with the response
    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    }

    return HTMLResponse(content=html_content, headers=headers)

# New route structure for admin pages - all protected by auth
@app.get("/{store_id}/prices", response_class=HTMLResponse)
async def prices_page(
    store_id: str = Path(..., regex=r"^\d{1,4}$")
):
    # Forward to existing price_editor for now
    # Eventually this will point to admin/prices/index.html
    return await price_editor(store_id)

@app.get("/{store_id}/floorplan", response_class=HTMLResponse)
async def floorplan_page(
    store_id: str = Path(..., regex=r"^\d{1,4}$")
):
    # Check if the store's YAML file exists
    yaml_file = f"stores/store{store_id}.yml"
    if not os.path.exists(yaml_file):
        raise HTTPException(status_code=404, detail=f"Store configuration not found for store {store_id}")

    # Load the floorplan HTML
    with open("floorplan.html", "r") as f:
        return HTMLResponse(f.read())

@app.get("/api/store/{store_id}/pricing_mode", response_class=JSONResponse)
async def get_pricing_mode(store_id: str = Path(..., regex=r"^\d{1,4}$")):
    data = load_store_yaml(store_id)
    pricing_mode = data.get("pricing-mode", "standard")
    return {"mode": pricing_mode}

@app.get("/api/store/{store_id}/boxes", response_class=JSONResponse)
async def get_boxes(store_id: str = Path(..., regex=r"^\d{1,4}$")):
    yaml_file = f"stores/store{store_id}.yml"

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

    # Determine pricing mode
    pricing_mode = boxes_data.get("pricing-mode", "standard")

    # Validate each box entry
    for i, box in enumerate(boxes_data["boxes"]):
        if "type" not in box:
            raise HTTPException(status_code=500, detail=f"Box at index {i} missing 'type' field")
        if "dimensions" not in box or not isinstance(box["dimensions"], list) or len(box["dimensions"]) != 3:
            raise HTTPException(status_code=500, detail=f"Box at index {i} has invalid 'dimensions' (must be list of 3 numbers)")
        
        # Validate pricing data based on pricing mode
        if pricing_mode == "standard":
            if "prices" not in box or not isinstance(box["prices"], list) or len(box["prices"]) != 4:
                raise HTTPException(status_code=500, detail=f"Box at index {i} has invalid 'prices' (must be list of 4 numbers)")
            
            if "itemized-prices" in box:
                raise HTTPException(status_code=500, detail=f"Box at index {i} has 'itemized-prices' but store is in standard pricing mode")
        else:  # itemized pricing mode
            if "itemized-prices" not in box or not isinstance(box["itemized-prices"], dict):
                raise HTTPException(status_code=500, detail=f"Box at index {i} missing 'itemized-prices' (must be an object)")
            
            # Validate required itemized pricing fields
            required_fields = ["box-price", "standard-materials", "standard-services", 
                              "fragile-materials", "fragile-services", 
                              "custom-materials", "custom-services"]
            
            for field in required_fields:
                if field not in box["itemized-prices"]:
                    raise HTTPException(status_code=500, detail=f"Box at index {i} missing required field '{field}' in itemized-prices")
            
            if "prices" in box:
                raise HTTPException(status_code=500, detail=f"Box at index {i} has 'prices' but store is in itemized pricing mode")
        
        if box["type"] == "CustomBox" and "open_dim" not in box:
            raise HTTPException(status_code=500, detail=f"Box at index {i} is CustomBox but missing 'open_dim' field")

        # Optional fields validation
        if "supplier" in box and not isinstance(box["supplier"], str):
            raise HTTPException(status_code=500, detail=f"Box at index {i} has invalid 'supplier' (must be a string)")
        if "model" in box and not isinstance(box["model"], str):
            raise HTTPException(status_code=500, detail=f"Box at index {i} has invalid 'model' (must be a string)")
        # Location must be a dictionary, string, or empty/missing
        if "location" in box:
            # Handle None or empty value by converting to empty dict
            if box["location"] is None:
                box["location"] = {}
                
            # Check type
            if not isinstance(box["location"], (str, dict)):
                raise HTTPException(status_code=500, detail=f"Box at index {i} has invalid 'location' (must be a dictionary or string)")
                
            # If location is a dict, validate its structure
            if isinstance(box["location"], dict):
                location = box["location"]
                
                # If coords are present, validate them
                if "coords" in location and location["coords"] is not None:
                    coords = location["coords"]
                    if not isinstance(coords, list) or len(coords) != 2:
                        raise HTTPException(status_code=500, detail=f"Box at index {i} has invalid 'location.coords' (must be a list of 2 numbers)")
                    if not all(isinstance(coord, (int, float)) for coord in coords):
                        raise HTTPException(status_code=500, detail=f"Box at index {i} has invalid coordinate values (must be numbers)")
                        
                # We don't use labels anymore, but if present should be a string
                if "label" in location and location["label"] is not None and not isinstance(location["label"], str):
                    raise HTTPException(status_code=500, detail=f"Box at index {i} has invalid 'location.label' (must be a string)")
        if "alternate_depths" in box:
            if not isinstance(box["alternate_depths"], list):
                raise HTTPException(status_code=500, detail=f"Box at index {i} has invalid 'alternate_depths' (must be a list of numbers)")
            for depth in box["alternate_depths"]:
                if not isinstance(depth, (int, float)):
                    raise HTTPException(status_code=500, detail=f"Box at index {i} has invalid value in 'alternate_depths' (must be numbers)")

    return boxes_data


# Helper function to load and validate YAML
def load_store_yaml(store_id: str):
    yaml_file = f"stores/store{store_id}.yml"

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


    return boxes_data

# Helper function to save YAML data
def save_store_yaml(store_id: str, data: dict):
    yaml_file = f"stores/store{store_id}.yml"

    try:
        # Custom YAML writing to maintain the desired format
        with open(yaml_file, "w") as f:
            # Write pricing mode if present
            if "pricing-mode" in data:
                f.write(f"pricing-mode: {data['pricing-mode']}\n")
            
            f.write("boxes:\n")

            # Determine pricing mode
            pricing_mode = data.get("pricing-mode", "standard")

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

                # Write prices or itemized-prices based on pricing mode
                if pricing_mode == "standard" and "prices" in box:
                    # Safely format prices with square brackets and commas, no spaces
                    if isinstance(box['prices'], list) and len(box['prices']) == 4:
                        # Validate prices are numeric and in reasonable range
                        prices = [float(p) if isinstance(p, (int, float)) and 0 <= p <= 10000 else 0 for p in box['prices']]
                        prices_str = str(prices).replace(" ", "")
                        f.write(f"    prices: {prices_str}\n")
                    else:
                        f.write(f"    prices: [0.0,0.0,0.0,0.0]\n")
                elif pricing_mode == "itemized" and "itemized-prices" in box:
                    # Write itemized prices
                    ip = box["itemized-prices"]
                    f.write(f"    itemized-prices:\n")
                    f.write(f"      box-price: {ip.get('box-price', 0)}\n")
                    f.write(f"      standard-materials: {ip.get('standard-materials', 0)}\n")
                    f.write(f"      standard-services: {ip.get('standard-services', 0)}\n")
                    f.write(f"      fragile-materials: {ip.get('fragile-materials', 0)}\n")
                    f.write(f"      fragile-services: {ip.get('fragile-services', 0)}\n")
                    f.write(f"      custom-materials: {ip.get('custom-materials', 0)}\n")
                    f.write(f"      custom-services: {ip.get('custom-services', 0)}\n")

                # Add location if present
                if store_id == "1" and "location" not in box:
                    # Skip location field for store1 if not present to maintain legacy format
                    pass
                else:
                    location = box.get('location', {})
                    
                    # Handle empty or None locations - skip entirely
                    if location is None or (isinstance(location, dict) and not location):
                        # Skip empty locations completely
                        pass
                    # Handle dictionary with coords
                    elif isinstance(location, dict) and 'coords' in location and location['coords']:
                        # Start location section
                        f.write(f"    location:\n")
                        
                        coords = location['coords']
                        # Ensure coords are floats and valid
                        if isinstance(coords, list) and len(coords) == 2:
                            x = float(coords[0]) if isinstance(coords[0], (int, float)) else 0
                            y = float(coords[1]) if isinstance(coords[1], (int, float)) else 0
                            f.write(f"      coords: [{x}, {y}]\n")
                    # Handle legacy string locations (skip completely)
                    elif isinstance(location, str) and location.strip():
                        # Skip legacy string locations
                        pass

                f.write("\n")

        return True
    except Exception as e:
        print(f"Error saving YAML: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving YAML: {str(e)}")

# Define box sections based on model patterns or box type
def get_box_section(model: str, box_type: str = None):
    # First try to categorize based on model if it exists
    if model and model.strip():
        if any(model.endswith(suffix) for suffix in ["C-UPS", "C", "Cube"]):
            return "CUBE"
        elif any(x in model for x in ["X 4", "X 3", "X 6", "J-11", "J-14", "J-15", "J-16", "SHIRTB"]):
            return "FLAT & SMALL"
        elif any(x in model for x in ["J-20", "WREATH", "ST-6", "MIR-3", "MIR-8"]):
            return "MEDIUM"
        elif any(x in model for x in ["J-64", "SUITCASE", "VCR", "24 X 18 X 18"]):
            return "LARGE"
        else:
            return "SPECIALTY"
            
    # If no model or couldn't categorize, use box type
    if box_type:
        if box_type == "NormalBox":
            return "NORMAL"
        elif box_type == "CustomBox":
            return "CUSTOM"
            
    # Fallback
    return "OTHER"

# Get boxes formatted for the editor with sections
@app.get("/api/store/{store_id}/boxes_with_sections", response_class=JSONResponse)
async def get_boxes_with_sections(store_id: str = Path(..., regex=r"^\d{1,4}$")):
    data = load_store_yaml(store_id)
    result = []
    
    # Determine pricing mode
    pricing_mode = data.get("pricing-mode", "standard")

    for box in data["boxes"]:
        # Handle legacy format (missing model and location)
        model = box.get("model", f"Unknown-{len(box['dimensions'])}-{box['dimensions'][0]}-{box['dimensions'][1]}-{box['dimensions'][2]}")

        # Get section based on model or box type
        box_type = box.get("type")
        section = get_box_section(model, box_type)
        
        # Only print debug info for store1
        if store_id == "1":
            print(f"Store1 - Model: {model}, Type: {box_type}, Section: {section}")

        dimensions_str = "x".join(str(d) for d in box["dimensions"])
        
        # Process based on pricing mode
        if pricing_mode == "standard":
            prices = box.get("prices", [0, 0, 0, 0])
            box_data = {
                "section": section,
                "model": model,
                "dimensions": dimensions_str,
                "box_price": prices[0],
                "standard": prices[1],
                "fragile": prices[2],
                "custom": prices[3],
                "location": box.get("location", "???"),
                "pricing_mode": "standard"
            }
        else:  # itemized pricing mode
            ip = box.get("itemized-prices", {})
            
            # Calculate totals for each level
            box_price = ip.get("box-price", 0)
            standard_total = box_price + ip.get("standard-materials", 0) + ip.get("standard-services", 0)
            fragile_total = box_price + ip.get("fragile-materials", 0) + ip.get("fragile-services", 0) 
            custom_total = box_price + ip.get("custom-materials", 0) + ip.get("custom-services", 0)
            
            box_data = {
                "section": section,
                "model": model,
                "dimensions": dimensions_str,
                "box_price": box_price,
                "standard_materials": ip.get("standard-materials", 0),
                "standard_services": ip.get("standard-services", 0),
                "standard_total": standard_total,
                "fragile_materials": ip.get("fragile-materials", 0),
                "fragile_services": ip.get("fragile-services", 0),
                "fragile_total": fragile_total,
                "custom_materials": ip.get("custom-materials", 0),
                "custom_services": ip.get("custom-services", 0),
                "custom_total": custom_total,
                "location": box.get("location", "???"),
                "pricing_mode": "itemized"
            }

        result.append(box_data)

    # Sort by section and then by model
    result.sort(key=lambda x: (x["section"], x["model"]))

    return result

# Get all boxes at once (bulk endpoint)
@app.get("/api/store/{store_id}/all_boxes", response_class=JSONResponse)
async def get_all_boxes(store_id: str = Path(..., regex=r"^\d{1,4}$")):
    data = load_store_yaml(store_id)
    
    # Add model field to all boxes that don't have it
    for box in data["boxes"]:
        if "model" not in box:
            box["model"] = f"Unknown-{len(box['dimensions'])}-{box['dimensions'][0]}-{box['dimensions'][1]}-{box['dimensions'][2]}"
    
    return {"pricing_mode": data.get("pricing-mode", "standard"), "boxes": data["boxes"]}

# Get a single box by model
@app.get("/api/store/{store_id}/box/{model}", response_class=JSONResponse)
async def get_box_by_model(
    store_id: str = Path(..., regex=r"^\d{1,4}$"),
    model: str = Path(...)):

    data = load_store_yaml(store_id)
    pricing_mode = data.get("pricing-mode", "standard")

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
                
            # Add pricing mode to the response
            box["pricing_mode"] = pricing_mode
            
            return box

    raise HTTPException(status_code=404, detail=f"Box with model {model} not found")

# Define the request model for price updates with CSRF protection
class PriceUpdateRequest(BaseModel):
    changes: Dict[str, Dict[str, float]]
    csrf_token: str

# Define the request model for itemized price updates
class ItemizedPriceUpdateRequest(BaseModel):
    changes: Dict[str, Dict[str, float]]
    csrf_token: str

# Update prices for multiple boxes (standard pricing mode)
@app.post("/api/store/{store_id}/update_prices", response_class=JSONResponse)
async def update_prices(
    store_id: str = Path(..., regex=r"^\d{1,4}$"),
    update_data: PriceUpdateRequest = Body(...),
    auth_store_id: str = Depends(get_current_store)):

    # Extract data from the request
    changes = update_data.changes

    # Validate CSRF token - normally you would check against a server-stored token
    # This is a simple check to ensure the token is present
    if not update_data.csrf_token or len(update_data.csrf_token) < 10:
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    data = load_store_yaml(store_id)
    
    # Check pricing mode
    pricing_mode = data.get("pricing-mode", "standard")
    if pricing_mode != "standard":
        raise HTTPException(status_code=400, detail="This endpoint is for standard pricing mode only. Use /update_itemized_prices for itemized pricing.")

    # Authentication check is handled by the auth_store_id dependency

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

    # Save the updated YAML file
    save_store_yaml(store_id, data)

    return {"message": f"Updated {updated_count} prices successfully"}

# Update itemized prices for multiple boxes (itemized pricing mode)
@app.post("/api/store/{store_id}/update_itemized_prices", response_class=JSONResponse)
async def update_itemized_prices(
    store_id: str = Path(..., regex=r"^\d{1,4}$"),
    update_data: ItemizedPriceUpdateRequest = Body(...),
    auth_store_id: str = Depends(get_current_store)):

    # Extract data from the request
    changes = update_data.changes

    # Validate CSRF token - normally you would check against a server-stored token
    # This is a simple check to ensure the token is present
    if not update_data.csrf_token or len(update_data.csrf_token) < 10:
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    data = load_store_yaml(store_id)
    
    # Check pricing mode
    pricing_mode = data.get("pricing-mode", "standard")
    if pricing_mode != "itemized":
        raise HTTPException(status_code=400, detail="This endpoint is for itemized pricing mode only. Use /update_prices for standard pricing.")

    # Authentication check is handled by the auth_store_id dependency

    updated_count = 0

    # Update prices for each box in the changes dict
    for box in data["boxes"]:
        # Get the actual model or generate a default one for legacy boxes
        box_model = box.get("model", f"Unknown-{len(box['dimensions'])}-{box['dimensions'][0]}-{box['dimensions'][1]}-{box['dimensions'][2]}")

        if box_model in changes:
            price_changes = changes[box_model]
            
            # Ensure itemized-prices exists
            if "itemized-prices" not in box:
                box["itemized-prices"] = {
                    "box-price": 0,
                    "standard-materials": 0,
                    "standard-services": 0,
                    "fragile-materials": 0,
                    "fragile-services": 0,
                    "custom-materials": 0,
                    "custom-services": 0
                }

            # Apply changes to appropriate fields
            for field, new_price in price_changes.items():
                # Validate price - must be a positive number within a reasonable range
                if isinstance(new_price, (int, float)) and 0 <= new_price <= 10000:
                    box["itemized-prices"][field] = new_price
                    updated_count += 1
                else:
                    raise HTTPException(status_code=400, detail=f"Invalid price value: {new_price}. Prices must be between 0 and 10000.")

            # If this is a legacy box and we're updating it, add the model field
            # so we can reference it again in the future
            if "model" not in box:
                box["model"] = box_model

    # Save the updated YAML file
    save_store_yaml(store_id, data)

    return {"message": f"Updated {updated_count} itemized prices successfully"}

class Comment(BaseModel):
    text: str

@app.post("/comments")
async def save_comment(comment: Comment):
    with open("comments.txt", "a") as f:
        f.write(comment.text + "\n")

# Authentication API Models
class LoginRequest(BaseModel):
    password: str
    remember_me: bool = False

class TokenResponse(BaseModel):
    token: str
    
# Authentication API endpoints
@app.post("/api/store/{store_id}/login", response_model=TokenResponse)
async def login(
    store_id: str = Path(..., regex=r"^\d{1,4}$"),
    login_data: LoginRequest = Body(...)
):
    # Check if store exists
    yaml_file = f"stores/store{store_id}.yml"
    if not os.path.exists(yaml_file):
        raise HTTPException(status_code=404, detail=f"Store not found: {store_id}")
    
    # Check if store has authentication enabled
    if not store_has_auth(store_id):
        raise HTTPException(status_code=400, detail=f"Authentication not enabled for store {store_id}")
    
    # Verify password
    if not verify_store_password(store_id, login_data.password):
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Create session (token)
    token_duration = 30 * 24 if login_data.remember_me else 24  # 30 days or 24 hours
    token = create_session(store_id, hours=token_duration)
    
    return {"token": token}

@app.get("/api/store/{store_id}/verify")
async def verify_token(
    store_id: str = Path(..., regex=r"^\d{1,4}$"),
    auth_store_id: str = Depends(get_current_store)
):
    # get_current_store dependency will raise appropriate exceptions
    # We only need to check the store_id matches
    if auth_store_id != store_id:
        raise HTTPException(status_code=403, detail=f"Token is not valid for store {store_id}")
    
    return {"verified": True, "store_id": store_id}

@app.get("/api/store/{store_id}/has-auth")
async def check_has_auth(store_id: str = Path(..., regex=r"^\d{1,4}$")):
    # Check if the store's YAML file exists
    yaml_file = f"stores/store{store_id}.yml"
    if not os.path.exists(yaml_file):
        raise HTTPException(status_code=404, detail=f"Store not found: {store_id}")
    
    # Check if auth is enabled
    has_auth = store_has_auth(store_id)
    
    return {"hasAuth": has_auth}

@app.post("/api/store/{store_id}/logout")
async def logout(
    store_id: str = Path(..., regex=r"^\d{1,4}$"),
    token: str = Depends(get_current_store)
):
    # Delete the session token
    delete_session(token)
    
    return {"message": "Logged out successfully"}

# Floorplan endpoints
@app.get("/api/store/{store_id}/floorplan", response_class=FileResponse)
async def get_floorplan(store_id: str = Path(..., regex=r"^\d{1,4}$")):
    # Check for existing floorplan files in expected formats
    floorplan_dir = "assets/floorplans"
    extensions = ['.png', '.jpg', '.jpeg', '.svg']
    
    for ext in extensions:
        # Check for simplified naming convention
        patterns = [
            f"store{store_id}_floor{ext}",
            f"store{store_id}_floor1{ext}",  # Legacy support
            f"store{store_id}{ext}"          # Legacy support
        ]
        
        for pattern in patterns:
            file_path = os.path.join(floorplan_dir, pattern)
            if os.path.exists(file_path):
                return FileResponse(
                    file_path,
                    media_type=f"image/{ext[1:]}" if ext != '.svg' else "image/svg+xml",
                    headers={"Cache-Control": "max-age=3600"}
                )
    
    # No floorplan found
    raise HTTPException(status_code=404, detail=f"No floorplan found for store {store_id}")

@app.post("/api/store/{store_id}/floorplan")
async def upload_floorplan(
    store_id: str = Path(..., regex=r"^\d{1,4}$"),
    file: UploadFile = File(...),
    auth_store_id: str = Depends(get_current_store)
):
    # Validate file type
    allowed_types = ["image/png", "image/jpeg", "image/jpg", "image/svg+xml"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
        )
    
    # Check file size (5MB limit)
    MAX_SIZE = 5 * 1024 * 1024  # 5MB
    contents = await file.read()
    if len(contents) > MAX_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: 5MB, uploaded: {len(contents) / 1024 / 1024:.2f}MB"
        )
    
    # Determine file extension
    extension = ""
    if file.content_type == "image/png":
        extension = ".png"
    elif file.content_type in ["image/jpeg", "image/jpg"]:
        extension = ".jpg"
    elif file.content_type == "image/svg+xml":
        extension = ".svg"
    
    # Remove any existing floorplans for this store
    floorplan_dir = "assets/floorplans"
    existing_files = os.listdir(floorplan_dir)
    for existing_file in existing_files:
        if existing_file.startswith(f"store{store_id}"):
            os.remove(os.path.join(floorplan_dir, existing_file))
    
    # Save the new floorplan with simplified naming
    filename = f"store{store_id}_floor{extension}"
    file_path = os.path.join(floorplan_dir, filename)
    
    # Save file asynchronously
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(contents)
    
    # Clear all location coordinates for this store
    data = load_store_yaml(store_id)
    locations_cleared = 0
    
    for box in data["boxes"]:
        if "location" in box:
            # Remove location completely instead of setting to empty dict
            del box["location"]
            locations_cleared += 1
    
    # Save the updated YAML if any locations were cleared
    if locations_cleared > 0:
        save_store_yaml(store_id, data)
    
    return {
        "message": f"Floorplan uploaded successfully for store {store_id}",
        "filename": filename,
        "size": len(contents),
        "content_type": file.content_type,
        "locations_cleared": locations_cleared
    }

# Get all box locations for mapping
@app.get("/api/store/{store_id}/box-locations", response_class=JSONResponse)
async def get_box_locations(store_id: str = Path(..., regex=r"^\d{1,4}$")):
    data = load_store_yaml(store_id)
    
    locations = []
    for box in data["boxes"]:
        model = box.get("model", f"Unknown-{len(box['dimensions'])}-{box['dimensions'][0]}-{box['dimensions'][1]}-{box['dimensions'][2]}")
        
        location_data = {
            "model": model,
            "dimensions": box["dimensions"],
            "type": box.get("type", "NormalBox")
        }
        
        # Get location data
        if "location" in box and isinstance(box["location"], dict) and "coords" in box["location"] and box["location"]["coords"]:
            # Standard dictionary format with valid coords
            location_data["coords"] = box["location"]["coords"]
            # We're not using labels anymore, but maintain API compatibility with empty string
            location_data["label"] = ""
        elif "location" in box and isinstance(box["location"], str) and box["location"].strip():
            # For backwards compatibility, but we'll return empty label
            location_data["label"] = ""
            location_data["coords"] = None
        else:
            # No location, empty location or invalid location
            location_data["label"] = ""
            location_data["coords"] = None
            
        locations.append(location_data)
    
    return locations

# Update box locations (bulk)
class LocationUpdateRequest(BaseModel):
    changes: Dict[str, Union[Dict[str, Any], None]]
    csrf_token: str

@app.post("/api/store/{store_id}/update-locations", response_class=JSONResponse)
async def update_locations(
    store_id: str = Path(..., regex=r"^\d{1,4}$"),
    update_data: LocationUpdateRequest = Body(...),
    auth_store_id: str = Depends(get_current_store)):
    
    # Validate CSRF token
    if not update_data.csrf_token or len(update_data.csrf_token) < 10:
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
    
    data = load_store_yaml(store_id)
    
    # Authentication check is handled by the auth_store_id dependency
    
    updated_count = 0
    
    # Update locations for each box in the changes dict
    for box in data["boxes"]:
        box_model = box.get("model", f"Unknown-{len(box['dimensions'])}-{box['dimensions'][0]}-{box['dimensions'][1]}-{box['dimensions'][2]}")
        
        if box_model in update_data.changes:
            location_change = update_data.changes[box_model]
            
            if location_change is None:
                # Clear location by removing it completely
                if "location" in box:
                    del box["location"]
            else:
                # Make sure changes are in dictionary format
                if isinstance(location_change, dict):
                    # Standard dictionary format
                    if "coords" not in location_change or not location_change["coords"]:
                        # No coordinates case - remove location
                        if "location" in box:
                            del box["location"]
                    else:
                        # Full location with coordinates
                        box["location"] = {
                            "coords": location_change["coords"]
                        }
                else:
                    # If non-dictionary was sent (shouldn't happen), remove location
                    if "location" in box:
                        del box["location"]
            
            updated_count += 1
    
    # Save the updated YAML file
    save_store_yaml(store_id, data)
    
    return {"message": f"Updated {updated_count} locations successfully"}