# PackingSite

Put in the measured dimensions of something to be packed, and it spits out optimal ways to pack it. Supports multiple stores with different box inventories.

## How to Use it

### Packing Levels:

- No Pack: Don't require any extra space for packing.
- Standard Pack: Try to find box that adds 2 inches to each dimension (1 inch on every side).
- Fragile Pack: Same but 4 inches.
- Custom Pack: Same but 6 inches.

### Packing Strategies

- Normal: Pack like normal; Wrap item in bubble wrap, put in box, close box.
- Cut Down: Same as before, but the open dimension of the box gets cut down until it exactly matches the packing level.
- Telescoping: Stack and tape multiple of the same box on top of each other to create an extra long box. Flaps are included in the box count calculation.
- Cheating: Tries rotating the item along each dimension to see if it fits inside a smaller box by taking advantage of the Pythagorean theorem. [Visual](https://stackoverflow.com/questions/69963451/how-to-get-height-and-width-of-element-when-it-is-rotated)
- Flattened: Instead of using a box to make a box, instead keep it flat and tape up the ends and gaps to create an oversized envelope. The assumption is that something like a poster goes in here. Max allowed height is 1 inch

### Result Filter

- Sort by Score: By default sorts by packing price where tightness score is a tiebreaker. Toggling checkbox swaps price and tightness importance
- Impossible Boxes: The item is physically to big to put into the box. Mainly for debugging, but may show why certain boxes have been excluded.
- No space: Options that have a dimension with 0 inches of extra space. This means it's technically possible to put an item in without any form of packing material. Disabled by default because poor practice + any mismeasurement may result with a box that is impossible to fit.
- Possible Boxes: These boxes can hold the item, but some packing will be sacrificied in at least one dimension. This adds some leniency to the boxes available.
- Fits: The item can be properly wraped and put into the box. There may be extra space for additional void fill. (Not actually an option. Always enabled)

### Table Columns

- Tightness: How much space the box has to fill with void fill. 0 = the box is the same size as the item. Calculated via summing dimensionOffset^2.
- Box Dims: The box this entry is based on.
- Pack Level: Pack Level.
- Price: Price of box at packing level using packing strategy.
- Recomendation: How much the site recomends the row combination. Options include Impossible, No Space, Possible, Fits.
- Pack Strategy: Pack strategy.
- Comments: Some strategies add some additional information that may be useful. For example, Cut Down and Telescoping list the new heights so that CMS has a more accurate numbers and the packer knows what's going on.
- Print: Formats the row in a thermal label printer friendly format. It has all the needed info for the packer to do their job.

### Debug Button

Shows some extra things for debugging/settings

- Dump State: Logs the current state object into the console.
- Print Scale: Changes the size of the text in the print menu. Font size is currently based on screen size.
- Comment: Sends a message to the backend on any isuses or comments. Intended to let the maintainer know whether there are any mistakes (prices or boxes info) and correct them when possible.

## Customize it

The application supports multiple stores, each with its own box inventory. Box definitions are stored in separate YAML files named `store{id}.yml`, where `{id}` is the store number (e.g., `store1.yml`, `store2.yml`).

Each store file has the following format:

```yaml
pricing-mode: standard # Choose between 'standard' or 'itemized' pricing mode
editable: true # Whether box prices can be edited through the web interface

boxes:
  # For normal boxes (where the third dimension (z) is assumed to be the opening):
  - type: NormalBox
    supplier: ABC # Optional supplier information
    model: "06C-UPS" # Model identifier (also optional, but at some point we'll probably REALLY want to use this!)
    dimensions: [x, y, z] # Dimensions - the code assumes z is the opening side for "normal" boxes
    prices: [nopack_price, standard_price, fragile_price, custom_price] # Standard pricing format
    location: "A1" # Optional location information.  Any arbitrary string to help the user find the box.

  # For normal boxes with itemized pricing:
  - type: NormalBox
    supplier: ABC
    model: "08C-UPS"
    dimensions: [x, y, z]
    itemized-prices: # Itemized pricing format
      box-price: 4.24 # Base price of the box
      standard-materials: 1.0 # Material cost for standard packing
      standard-services: 2.0 # Service cost for standard packing
      fragile-materials: 3.0 # Material cost for fragile packing
      fragile-services: 2.0 # Service cost for fragile packing
      custom-materials: 4.0 # Material cost for custom packing
      custom-services: 3.0 # Service cost for custom packing
    location: "A2"

  # For custom boxes (where you need to specify the opening dimension):
  - type: CustomBox
    supplier: ABC
    model: "CustomBox-1"
    dimensions: [x, y, z] # Dimensions in descending order
    open_dim: 0 # Index of the opening dimension (0, 1, or 2)
    prices: [nopack_price, standard_price, fragile_price, custom_price] # Can also use itemized-prices format
    location: "B2"
```

To add, remove, or modify boxes, edit the appropriate store YAML file. To add a new store, create a new `store{id}.yml` file following the format above.

## Run it

Simply run `docker compose up` in the same directory, and it should start the server. By default it binds host port `5893` because I run multiple lightweight servers behind NGINX and the port doesn't collide with anything else I run.

Docker configuration notes:

- The store YAML files (`store*.yml`) are included in the Docker volume mount, so you can edit box configurations without rebuilding
- Any comments sent to `comments.txt` can be read and deleted from the host system

To disable the comments, remove the `/comments` path from `main.py` and restart the container.

## Pricing Modes

The application supports two pricing modes:

1. **Standard Pricing Mode**: Uses a simple array of 4 values for box prices at different packing levels:

   - `[nopack_price, standard_price, fragile_price, custom_price]`

2. **Itemized Pricing Mode**: Breaks down each price into box cost, materials, and services for more detailed pricing:
   - `box-price`: Base cost of the box
   - `standard-materials`, `standard-services`: Materials and service costs for standard packing
   - `fragile-materials`, `fragile-services`: Materials and service costs for fragile packing
   - `custom-materials`, `custom-services`: Materials and service costs for custom packing

To specify the pricing mode for a store, add the `pricing-mode` field at the top of the store YAML file:

```yaml
pricing-mode: standard # or 'itemized'
```

## Price Editor

Each store has a price editor accessed via `/{store_id}/price_editor`. The price editor interface will adapt based on the pricing mode:

- **Standard Mode**: Shows a simple table with box price, standard, fragile, and custom prices
- **Itemized Mode**: Shows a more detailed table breaking down each price into box price, materials, and services

The price editor will only allow updates if the store has `editable: true` set in its YAML file.

## URL Routes and Endpoints

- `/{store_id}` - Access the main packing calculator for a specific store (e.g., `/1` for store 1)
- `/{store_id}/price_editor` - Access the price editor for a specific store
- `/api/store/{store_id}/boxes` - API endpoint to get all boxes for a store
- `/api/store/{store_id}/boxes_with_sections` - API endpoint to get boxes organized by sections
- `/api/store/{store_id}/pricing_mode` - Get the current pricing mode for a store
- `/api/store/{store_id}/is_editable` - Check if a store's prices can be edited
- `/api/store/{store_id}/update_prices` - Update prices in standard pricing mode
- `/api/store/{store_id}/update_itemized_prices` - Update prices in itemized pricing mode

## Comments

For simplicity and speed most of the choices here were intentional.

- FastApi for a super simple backend that lets me save comments. We are now also using it for some CRUD to update prices and to handle multiple stores.
- Starting to modularize a tiny bit. Still trying to KISS

# License

Standard MIT, but send an email over to `qrqi47rmikk@airmail.cc` (from any email you want) if you end up using this program. Something like "I'm using it." is fine. I'm just curious to see if anyone ends up using it.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
