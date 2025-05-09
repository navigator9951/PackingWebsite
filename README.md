# PackingSite
Put in the measured dimensions of something to be packed, and it spits out optimal ways to pack it.
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
Because this wasn't a super serious project of mine, I didn't put too much effort into the structure of the site in order to try to keep it simple. At the bottom of `index.js` there is a list of boxes. To create a new box, the inputs are `new Box([Dimensions, large to small], which dimension has the opening, [NoPack price, Standard price, Fragile pack price, Custom pack price])`. `Box.NormalBox` is the same as above but assumes the smallest/last dimension is the one that opens   

## Run it
Simply run `docker compose up` in the same directory, and it should start the server. By default it binds host port `5893` because I run multiple lightweight servers behind NGINX and the port doesn't collide with anything else I run.

Because docker mounts the current directory as a volume inside of the container, any edits to `index.js` show up instantly, and any comments sent to `comments.txt` can be read and deleted from the host system. To disable the comments, remove the `/comments` path from `main.py` and restart the container.

## Comments
For simplicity and speed most of the choices here were intentional.
- FastApi for a super simple backend that lets me save comments
- A single html + js file because I didn't want to deal with the bloat that comes from working with typescript.

# License
Standard MIT, but send an email over to `qrqi47rmikk@airmail.cc` (from any email you want) if you end up using this program. Something like "I'm using it." is fine. I'm just curious to see if anyone ends up using it.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
