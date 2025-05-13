
const container = document.getElementById("container")
const state = {
    packingLevelBoxes: {},
    altPackingStrats: {},
    resFilters: {},
    inputDims: [0, 0, 0],
    inputDimsSorted: [0, 0, 0],
    availableBoxes: [],
    printScale: 7,
}

function gen_checkBoxLabel(id, text, checked, state_collection) {
    const checkboxDiv = document.createElement("span")

    const label = document.createElement("label")
    label.textContent = text
    label.setAttribute("for", id)

    const checkbox = document.createElement("input")
    checkbox.setAttribute("type", "checkbox")
    checkbox.checked = checked
    checkbox.id = id

    state_collection[id] = checked

    function toggle() {
        state_collection[id] = !checkbox.checked    // ~ because the event runs first
        gen_chart()
    }
    label.addEventListener("mouseup", toggle)
    checkbox.addEventListener("mouseup", toggle)
    checkboxDiv.appendChild(checkbox)
    checkboxDiv.appendChild(label)
    return checkboxDiv
}

function gen_packingLevelBoxes() {
    const packingLevelBoxesDiv = document.createElement("div")
    packingLevelBoxesDiv.textContent = "Packing levels: "
    const np_checkBox = gen_checkBoxLabel("npCheckbox", "No Pack/Sell", false, state.packingLevelBoxes)
    const std_checkBox = gen_checkBoxLabel("stdCheckbox", "Standard Pack", true, state.packingLevelBoxes)
    const frag_checkBox = gen_checkBoxLabel("fragCheckbox", "Fragile Pack", false, state.packingLevelBoxes)
    const cust_checkBox = gen_checkBoxLabel("custCheckbox", "Custom Pack", false, state.packingLevelBoxes)
    // const tele_checkBox = gen_checkBoxLabel("teleCheckbox", "Telescope Pack", false, state.packingLevelBoxes)
    packingLevelBoxesDiv.appendChild(np_checkBox)
    packingLevelBoxesDiv.appendChild(std_checkBox)
    packingLevelBoxesDiv.appendChild(frag_checkBox)
    packingLevelBoxesDiv.appendChild(cust_checkBox)
    // packingLevelBoxesDiv.appendChild(tele_checkBox)

    container.appendChild(packingLevelBoxesDiv)
}

function gen_altPackingStrategies() {
    const strategiesDiv = document.createElement("div")
    strategiesDiv.textContent = "Packing Strategies: "
    const normalBox = gen_checkBoxLabel("normalCheckbox", "Normal", true, state.altPackingStrats)
    const cutDownBox = gen_checkBoxLabel("cutDownCheckbox", "Cut Down", false, state.altPackingStrats)
    const telescopeBox = gen_checkBoxLabel("telescopeCheckbox", "Telescoping", false, state.altPackingStrats)
    const cheatingBox = gen_checkBoxLabel("cheatingCheckbox", "Cheating", false, state.altPackingStrats)
    const flatBox = gen_checkBoxLabel("flatCheckbox", "Flattened", false, state.altPackingStrats)

    strategiesDiv.appendChild(normalBox)
    strategiesDiv.appendChild(cutDownBox)
    strategiesDiv.appendChild(telescopeBox)
    strategiesDiv.appendChild(cheatingBox)
    strategiesDiv.appendChild(flatBox)

    container.appendChild(strategiesDiv)
    
}

function gen_configBoxes() {
    const configDiv = document.createElement("div")
    configDiv.textContent = "Result Filter: "
    const showImpossible = gen_checkBoxLabel("showImpossible", "Show impossible boxes", false, state.resFilters)
    const showNoSpace = gen_checkBoxLabel("showNoSpace", "Show no space boxes", false, state.resFilters)
    const showPossible = gen_checkBoxLabel("showPossible", "Show possible boxes", true, state.resFilters)
    const scorePriority = gen_checkBoxLabel("scorePriority", "Sort by score", false, state.resFilters)

    configDiv.appendChild(scorePriority)
    configDiv.appendChild(showImpossible)
    configDiv.appendChild(showNoSpace)
    configDiv.appendChild(showPossible)

    container.appendChild(configDiv)
}

function gen_dimInputs() {
    const inputDiv = document.createElement("div")

    const inOne = document.createElement("input")
    inOne.setAttribute("placeholder", "x")
    const inTwo = document.createElement("input")
    inTwo.setAttribute("placeholder", "y")
    const inThree = document.createElement("input")
    inThree.setAttribute("placeholder", "z")

    const clearBtn = document.createElement("button")
    clearBtn.textContent = "Clear inputs"
    inputDiv.appendChild(clearBtn)
    clearBtn.addEventListener("mouseup", () => {
        const chartDiv = document.getElementById("chartContainer")
        if (chartDiv) {
            chartDiv.remove()
        }
        inOne.value = ""
        inTwo.value = ""
        inThree.value = ""
        state.inputDims = [0, 0, 0]
        inOne.focus()
    })

    inOne.addEventListener("keyup", (e) => {
        const val = parseInt(e.target.value)
        if (!isNaN(val)) {    
            state.inputDims[0] = val
            state.inputDimsSorted = state.inputDims.toSorted((a, b) => {return b - a}) 
            gen_chart()
        }
    })
    inTwo.addEventListener("keyup", (e) => {
        const val = parseInt(e.target.value)
        if (!isNaN(val)) {
            state.inputDims[1] = val
            state.inputDimsSorted = state.inputDims.toSorted((a, b) => {return b - a}) 
            gen_chart()
        }
    })
    inThree.addEventListener("keyup", (e) => {
        const val = parseInt(e.target.value)
        if (!isNaN(val)) {
            state.inputDims[2] = val
            state.inputDimsSorted = state.inputDims.toSorted((a, b) => {return b - a}) 
            gen_chart()
        }
    })

    inputDiv.appendChild(inOne)
    inputDiv.appendChild(inTwo)
    inputDiv.appendChild(inThree)

    container.appendChild(inputDiv)

}

function gen_html() {
    const infoDiv = document.createElement("div")

    // Clickable help button
    const helpButton = document.createElement("button")
    infoDiv.appendChild(helpButton)
    helpButton.textContent = "Help"
    helpButton.addEventListener("click", () => {
        const helpDiv = document.getElementById("helpDiv")
        if (helpDiv) {
            helpDiv.remove()
        } else {
            const helpDiv = document.createElement("div")
            helpDiv.id = "helpDiv"
            helpDiv.innerHTML =
                `<div>The first row filters which packing levels are shown. </div>
                <div>These levels expect a minimum amount of packing material to be used. In order, they are 0in, 2in, 4in, 6in.</div>
                <div>Packing strategies are the methods used to pack the item. </div>
                <div>Normal - The item is packed normally.</div>
                <div>Telescoping - The item is packed by sticking multiple boxes together telescope style.</div>
                <div>Cheating - The item is packed by rotating the item in the box to take <a href="https://stackoverflow.com/questions/69763451/how-to-get-height-and-width-of-element-when-it-is-rotated">advantage of pythagoras</a></div>
                <div>Flattened - The item (paper) is packed by sliding it into the box and taping up the ends without folding it.</div>
                <div>Sort by score orders the boxes by score (how well the item fits in the box) or price</div>
                <div>A lower score is better because it means there is less "error".</div>
                <div>Next are toggles to filter which recomendation levels should be present</div>
                <div>Impossible - The item is too big for the box</div>
                <div>No space - The item theoretically fits, but there is 0 space left in the box for at least 1 dimension</div>
                <div>Possible - The item fits, but there some packing material space will be sacrificed</div>
                <div>fits - The item fits in the box without any isuses and can be packed as desired (probably with extra space to work with)</div>
                <div>The last row is the input for the dimensions of the item to be packed. (Order doesn't matter) </div>
                `
            helpDiv.style.backgroundColor = "#bbbbbb"
            infoDiv.appendChild(helpDiv)
        }
    })

    // Clickable debug button
    const debugButton = document.createElement("button")
    infoDiv.appendChild(debugButton)
    debugButton.textContent = "Show Debug"
    debugButton.addEventListener("click", () => {
        const debugDiv = document.getElementById("debugDiv")
        if (debugDiv) {
            debugDiv.remove()
        } else {
            const debugDiv = document.createElement("div")
            debugDiv.id = "debugDiv"
            
            const dumpBtn = document.createElement("button")
            dumpBtn.textContent = "Dump state"
            dumpBtn.addEventListener("click", () => {
                // console.log(JSON.stringify(state))
                console.log(state)
            })
            debugDiv.appendChild(dumpBtn)

            const scaleVal = document.createElement("input")
            scaleVal.setAttribute("type", "number")
            scaleVal.value = state.printScale
            scaleVal.addEventListener("change", (e) => {
                const val = parseFloat(e.target.value)
                if (!isNaN(val)) {
                    state.printScale = val
                    gen_chart()
                }
            })
            debugDiv.appendChild(document.createTextNode("Print scale: "))
            debugDiv.appendChild(scaleVal)

            const commentBox = document.createElement("input")
            commentBox.setAttribute("type", "text")
            commentBox.setAttribute("placeholder", "Comment")
            const commentBtn = document.createElement("button")
            commentBtn.textContent = "Send comment"
            commentBtn.addEventListener("click", () => {
                const comment = commentBox.value
                commentBox.value = ""
                if (comment) {
                    fetch("/comments", {
                        method: "POST",
                        body: JSON.stringify({text: comment}),
                        headers: {
                            "Content-Type": "application/json"
                        }
                    })
                }
            })
            debugDiv.appendChild(commentBox)
            debugDiv.appendChild(commentBtn)

            infoDiv.appendChild(debugDiv)
        }
    })
    
    container.appendChild(infoDiv)
    gen_packingLevelBoxes()
    gen_altPackingStrategies()
    gen_configBoxes()
    gen_dimInputs()
}

function gen_chart() {
    let chartDiv = document.getElementById("chartContainer")
    if (chartDiv) {
        chartDiv.remove()
    }
    chartDiv = document.createElement("div")
    chartDiv.id = "chartContainer"
    const table = document.createElement("table")
    const header = document.createElement("tr")
    for (const text of ["Tightness (Extra Volume)", "Box Dims", "Pack Level", "Price", "Recomendation", "Pack Strategy", "Comments"]) {
        const th = document.createElement("th")
        th.textContent = text
        header.appendChild(th)
    };
    table.appendChild(header)

    const checkBoxState = {     // Provides a mapping from boxResult generation to the checkboxes
        "No Pack": state.packingLevelBoxes["npCheckbox"],
        "Standard Pack": state.packingLevelBoxes["stdCheckbox"],
        "Fragile Pack": state.packingLevelBoxes["fragCheckbox"],
        "Custom Pack": state.packingLevelBoxes["custCheckbox"],
        "Normal": state.altPackingStrats["normalCheckbox"],
        "Cut Down": state.altPackingStrats["cutDownCheckbox"],
        "Telescoping": state.altPackingStrats["telescopeCheckbox"],
        "Cheating": state.altPackingStrats["cheatingCheckbox"],
        "Flattened": state.altPackingStrats["flatCheckbox"],
        "fits": true,
        "possible": state.resFilters["showPossible"],
        "no space": state.resFilters["showNoSpace"],
        "impossible": state.resFilters["showImpossible"],
    }
    const boxResultCollection = []
    for (const box of state.availableBoxes) {
        const boxResults = box.gen_boxResults()

        // console.log(boxResults)
        for (const packingLevel of Object.keys(boxResults)) {
            if (checkBoxState[packingLevel]) {
                for (const packingStrategy of Object.keys(boxResults[packingLevel])) {
                    if (checkBoxState[packingStrategy]) {
                        if (checkBoxState[boxResults[packingLevel][packingStrategy].recomendationLevel]) {
                            boxResultCollection.push(boxResults[packingLevel][packingStrategy])
                        }
                    }
                }

            }
        }
    }
    if (state.resFilters["scorePriority"]) {
        boxResultCollection.sort((a, b) => {return (a.score * 1000 + a.price) - (b.score * 1000 + b.price)})    // Use other as a tie breaker
    } else {
        boxResultCollection.sort((a, b) => {return (a.price * 1000 + a.score) - (b.price * 1000 + b.score)})
    }
    if (boxResultCollection.length == 0) {
        const noResults = document.createElement("div")
        noResults.textContent = "No results found"
        noResults.style.fontSize = "1vw"
        noResults.style.margin = "10px"
        chartDiv.appendChild(noResults)
        container.appendChild(chartDiv)
        return
    }
    for (const result of boxResultCollection) {
        const row = document.createElement("tr")
        const score = document.createElement("td")
        score.style.padding = "2px"
        score.textContent = result.score
        const boxDims = document.createElement("td")
        boxDims.textContent = `[${result.dimensions[0]}, ${result.dimensions[1]}, ${result.dimensions[2]}]`
        const packLevel = document.createElement("td")
        if (result.packLevel == "No Pack") {
            packLevel.textContent = "Box"
        } else {
            packLevel.textContent = result.packLevel
        }
        const price = document.createElement("td")
        price.textContent = result.price.toFixed(2)
        const recomendation = document.createElement("td")
        recomendation.textContent = result.recomendationLevel
        const strategy = document.createElement("td")
        strategy.textContent = result.strategy
        const comment = document.createElement("td")
        comment.textContent = result.comment

        row.appendChild(score)
        row.appendChild(boxDims)
        row.appendChild(packLevel)
        row.appendChild(price)
        row.appendChild(recomendation)
        row.appendChild(strategy)
        row.appendChild(comment)

        // printing
        const printBtn = document.createElement("button")
    
        printBtn.textContent = "Print"
        printBtn.addEventListener("click", () => {
            var frame = document.createElement('iframe');
            frame.srcdoc = 
            `<html>
                <head><title>Print</title>
                <style>
                    div {
                        font-size: ${state.printScale}vw;
                    }
                    span {
                        margin-left: 10vw;
                    }
                </style>
                </head>
                <body onload="window.print()">
                <div>
                    Original Box dimensions: <br>
                    <span>${boxDims.outerHTML}</span> <br>
                    Packing level: <br>
                    <span>${packLevel.outerHTML}</span> <br>
                    Packing strategy: <br>
                    <span>${strategy.outerHTML}</span> <br>
                    Price: $${price.outerHTML} <br> 
                    Recomendation: <br>
                    <span>${recomendation.outerHTML}</span> <br>
                    Comments: ${comment.outerHTML} <br>
                </div>
                </body>
            </html>`;
            document.body.appendChild(frame);
            setTimeout(() => {
                frame.remove();
            }, 1000);
        })
        row.appendChild(printBtn)

        table.appendChild(row)
    }
    chartDiv.appendChild(table)
    container.appendChild(chartDiv)
}

class BoxResult {
    constructor(dimensions, packLevel, price, recomendationLevel, comment, score, strategy) {
        this.dimensions = dimensions    // Box dims
        this.packLevel = packLevel  // Packing level
        this.price = price  // Selection price
        this.recomendationLevel = recomendationLevel    // fits vs possible vs no space vs impossible
        this.comment = comment  // Might be needed to explain the status?
        this.score = score  // How good is the fit?
        this.strategy = strategy  // What packing strategy was used?
    }
}

class Box {
    constructor(dimensions, open_dim, prices) {
        // dimensions: [int, int, int] -> What are the dimensions of the box
        // open_dim: int -> Along which dimension does the box open (for tele)
        // prices: [np_float, sp_float, fp_float, cp_float] -> price for each packing level
        const open_dim_val = dimensions[open_dim]
        this.dimensions = dimensions.toSorted((a, b) => b - a)     // Just to presort by size
        this.open_dim = this.dimensions.findIndex((e) => {return e == open_dim_val})
        this.prices = prices
        this.packingLevelNames = ["No Pack", "Standard Pack", "Fragile Pack", "Custom Pack"]
        this.altPackingNames = ["Normal", "Telescoping", "Cheating", "Flattened"]
        this.packingOffsets = {
            "No Pack": 0,
            "Standard Pack": 2,
            "Fragile Pack": 4,
            "Custom Pack": 6
        }

        this.openLength = this.dimensions[this.open_dim] 
        if (this.open_dim == 0) {
            this.largerConstraint = this.dimensions[1]
            this.smallerConstraint = this.dimensions[2]
        } else if (this.open_dim == 1) {
            this.largerConstraint = this.dimensions[0]
            this.smallerConstraint = this.dimensions[2]
        } else {
            this.largerConstraint = this.dimensions[0]
            this.smallerConstraint = this.dimensions[1]
        }
        this.flapLength = this.smallerConstraint / 2

        // this.debug = this.largerConstraint == 6 && this.smallerConstraint == 6 && this.openLength == 49
        this.debug = false
        this.debugState = null
    }

    static NormalBox(dimensions, prices) {
        // Assumes the last dimension is the open dimension (should be the smallest one)
        return new Box(dimensions, 2, prices)
    }

    pushDebug(val) {
        this.debugState = this.debug
        this.debug = val
    }

    popDebug() {
        this.debug = this.debugState
        this.debugState = null
    }

    boxSpace(boxDims, itemDims) {
        // itemDims: [x, y, z] -> dimensions of the item to be packed
        // How much space between box and item(s) based on passed dimensions
        return [boxDims[0] - itemDims[0], boxDims[1] - itemDims[1], boxDims[2] - itemDims[2]]
    }

    calcScore(extraSpace) {
        // space: [x, y, z] -> space in each dimension in the box
        // expected space: int -> how much space each dimension should have
        // TODO: See if it makes sense to pass the packing level
        return extraSpace[0] ** 2 + extraSpace[1] ** 2 + extraSpace[2] ** 2 
    }

    getPrice(packingLevel) {
        // packingLevel: str -> packing level to be used
        // returns: float -> price of the box
        return this.prices[this.packingLevelNames.findIndex(e => e == packingLevel)]
    }

    // Return the verdict on whether what the calculated offsets are in terms of feasibility
    // offsets: [x, y, z] -> space in each dimension in the box
    // packingLevel: str -> packing level to be used
    // returns: str -> "impossible", "no space", "possible", "fits"
    calcRecomendation(offsets, packingLevel) {
        const lowestDim = Math.min(...offsets)
        if (lowestDim < 0) {
            return "impossible"
        } else if (lowestDim == 0 && packingLevel != "No Pack") {
            return "no space"
        } else if (lowestDim > 0 && lowestDim < this.packingOffsets[packingLevel]) {
            return "possible"
        }
        return "fits"
    }

    gen_normalBoxResults(packingLevel) {
        // Handle normal boxes
        const offsetSpace = this.boxSpace(this.dimensions, state.inputDimsSorted)
        return new BoxResult(this.dimensions, packingLevel, this.getPrice(packingLevel), 
            this.calcRecomendation(offsetSpace, packingLevel), "", this.calcScore(offsetSpace), "Normal")
    }

    gen_cutDownBoxResults(packingLevel) {
        // Handle cut down boxes
        let bestScore = 1000000
        let bestResult = null
        for (const openInputIndex of [0, 1, 2]) {
            const largerInput = Math.max(state.inputDimsSorted[(openInputIndex + 1) % 3], state.inputDimsSorted[(openInputIndex + 2) % 3])
            const smallerInput = Math.min(state.inputDimsSorted[(openInputIndex + 1) % 3], state.inputDimsSorted[(openInputIndex + 2) % 3])
            const testOffset = [
                this.largerConstraint - largerInput,
                this.smallerConstraint - smallerInput,
                Math.min(this.packingOffsets[packingLevel], this.openLength - state.inputDimsSorted[openInputIndex])
            ]
            const score = this.calcScore(testOffset)
            if (score < bestScore) {
                bestScore = score
                bestResult = new BoxResult(this.dimensions, packingLevel, this.getPrice(packingLevel), this.calcRecomendation(testOffset, packingLevel),
                    `Expected dims: [${this.largerConstraint}, ${this.smallerConstraint}, ${Math.min(this.openLength, state.inputDimsSorted[openInputIndex] + this.packingOffsets[packingLevel])}]`, score, "Cut Down")
            }
        }
        return bestResult
    }

    nextLevel(packingLevel) {   // I don't like this out here, but then I don't have to deal with `this` scoping
        const index = this.packingLevelNames.findIndex(e => e == packingLevel)
        return this.packingLevelNames[Math.min(index + 1, this.packingLevelNames.length - 1)]
    }

    gen_telescopingBoxResults(packingLevel) {

        // Handle Telescoping boxes
        const minLength = state.inputDimsSorted[0] + this.packingOffsets[packingLevel]
        const largerOffset = this.largerConstraint - state.inputDimsSorted[1]
        const smallerOffset = this.smallerConstraint - state.inputDimsSorted[2]
        const score = this.calcScore([largerOffset, smallerOffset, 0])
        const endBoxLength = this.openLength + this.flapLength
        const centerBoxLength = endBoxLength + this.flapLength
        const centerRemaining = minLength - 2 * endBoxLength
        let centerBoxes = 0
        if (centerRemaining > 0) {
            centerBoxes = Math.ceil(centerRemaining / centerBoxLength)
        }
        const totalBoxes = 2 + centerBoxes
        // TODO one box should be next level
        const totalCost = this.getPrice(packingLevel) * (totalBoxes - 1) + this.getPrice(this.nextLevel(packingLevel))
        return new BoxResult(this.dimensions, packingLevel,
            totalCost, this.calcRecomendation([largerOffset, smallerOffset, this.packingOffsets[packingLevel]], packingLevel),
            `Expected dims: [${minLength}, ${this.largerConstraint}, ${this.smallerConstraint}] with ${totalBoxes} boxes`, score, "Telescoping")
    }

    gen_cheatingBoxResults(packingLevel) {
        function calcRotatedSize(outerHight, outerWidth, innerHight, innerWidth) {
            const angle = Math.atan(outerWidth / outerHight)
            // Not sure if the angle is correct or needs to be inverted
            // I think there is an assumption that the height is the larger dimension
            const rotatedHight = Math.sin(angle) * innerWidth + Math.cos(angle) * innerHight
            const rotatedWidth = Math.cos(angle) * innerWidth + Math.sin(angle) * innerHight
            return [rotatedHight, rotatedWidth]
        }

        // Handle cheating boxes
        let bestScore = 1000000
        let bestResult = null
        for (const normalIndex of [0, 1, 2]) {
            const largerDim = Math.max(this.dimensions[(normalIndex + 1) % 3], this.dimensions[(normalIndex + 2) % 3])
            const smallerDim = Math.min(this.dimensions[(normalIndex + 1) % 3], this.dimensions[(normalIndex + 2) % 3])
            const largerInput = Math.max(state.inputDimsSorted[(normalIndex + 1) % 3], state.inputDimsSorted[(normalIndex + 2) % 3])
            const smallerInput = Math.min(state.inputDimsSorted[(normalIndex + 1) % 3], state.inputDimsSorted[(normalIndex + 2) % 3])
            const rotatedSize = calcRotatedSize(largerDim, smallerDim, largerInput, smallerInput)
            const newInputDims = [0, 0, 0]
            newInputDims[normalIndex] = state.inputDimsSorted[normalIndex]
            newInputDims[(normalIndex + 1) % 3] = rotatedSize[0]
            newInputDims[(normalIndex + 2) % 3] = rotatedSize[1]
            const boxOffset = this.boxSpace(this.dimensions, newInputDims)
            const score = this.calcScore(boxOffset)
            if (score < bestScore) {
                bestScore = score
                bestResult = new BoxResult(this.dimensions, packingLevel, this.getPrice(packingLevel), this.calcRecomendation(boxOffset, packingLevel),
                    `Internal dims: [${newInputDims[0].toFixed(1)}, ${newInputDims[1].toFixed(1)}, ${newInputDims[2].toFixed(1)}]`, score, "Cheating")
            }
        }
        return bestResult
    }

    gen_flattenedBoxResults(packingLevel) {
        // Handle Flattened boxes
        const flatBoxLength = this.openLength + this.flapLength * 2
        const flatBoxWidth = this.smallerConstraint + this.largerConstraint
        const largerOffset = Math.max(flatBoxLength, flatBoxWidth) - state.inputDimsSorted[0] - this.packingOffsets[packingLevel]
        const smallerOffset = Math.min(flatBoxLength, flatBoxWidth) - state.inputDimsSorted[1] - this.packingOffsets[packingLevel]
        const heightOffset = 1 - state.inputDimsSorted[2]
        const offsets = [largerOffset, smallerOffset, heightOffset]
        const recomendation = this.calcRecomendation(offsets, packingLevel) == "impossible" ? "impossible" : "fits"     // If the user wants to see flat, then it should be impossible or not
        return new BoxResult(this.dimensions, packingLevel, this.getPrice(packingLevel), recomendation,
            `Expected dims: [${flatBoxLength}, ${flatBoxWidth}, ${1}]`, this.calcScore(offsets), "Flattened")
    }

    gen_boxResults() {
        // Based on current state
        if (this.debug) {
            console.log("---Gen box results---")
        }
        const result = {}
        for (const packingLevel of this.packingLevelNames) {
            result[packingLevel] = {}

            // TODO Could check for which alt packing strategies are selected and only calculate those
            result[packingLevel]["Normal"] = this.gen_normalBoxResults(packingLevel)

            result[packingLevel]["Cut Down"] = this.gen_cutDownBoxResults(packingLevel)
            
            result[packingLevel]["Telescoping"] = this.gen_telescopingBoxResults(packingLevel)

            result[packingLevel]["Cheating"] = this.gen_cheatingBoxResults(packingLevel)

            result[packingLevel]["Flattened"] = this.gen_flattenedBoxResults(packingLevel)

        }            

        return result
    }
}

// Load boxes from API
async function load_boxes() {
    try {
        const response = await fetch('/api/boxes')
            .catch(networkError => {
                console.error("Network error:", networkError);
                throw new Error(`Network error: ${networkError.message}. Make sure the server is running.`);
            });

        if (!response.ok) {
            const errorText = await response.text();
            console.error(`Server responded with status ${response.status}:`, errorText);
            throw new Error(`Server error: ${response.status} - ${errorText}`);
        }

        const data = await response.json();
        const boxes = [];

        if (data.boxes && Array.isArray(data.boxes)) {
            data.boxes.forEach(boxData => {
                let box;

                if (boxData.type === 'NormalBox') {
                    box = Box.NormalBox(boxData.dimensions, boxData.prices);
                } else if (boxData.type === 'CustomBox') {
                    box = new Box(boxData.dimensions, boxData.open_dim, boxData.prices);
                } else {
                    console.warn(`Skipping box with unknown type: ${boxData.type}`);
                    return; // Skip unknown box types
                }

                boxes.push(box);
            });
        } else {
            console.error("Invalid data format received from server");
            throw new Error("Invalid box data format from server");
        }

        return boxes;
    } catch (error) {
        console.error("Error loading boxes:", error);
        throw error;
    }
}


// Initialize the app
async function initialize() {
    gen_html();

    try {
        state.availableBoxes = await load_boxes();
        gen_chart();
    } catch (error) {
        console.error("Error loading boxes:", error);

        // Create a user-friendly error message
        const container = document.getElementById("container");

        // Clear any existing content
        while (container.firstChild) {
            container.removeChild(container.firstChild);
        }

        const errorDiv = document.createElement("div");
        errorDiv.style.padding = "20px";
        errorDiv.style.margin = "20px";
        errorDiv.style.backgroundColor = "#ffdddd";
        errorDiv.style.border = "1px solid #ff0000";
        errorDiv.style.borderRadius = "5px";

        const errorTitle = document.createElement("h2");
        errorTitle.textContent = "Error Loading Boxes";
        errorTitle.style.color = "#cc0000";
        errorDiv.appendChild(errorTitle);

        const errorMessage = document.createElement("p");
        errorMessage.textContent = error.message;
        errorDiv.appendChild(errorMessage);

        const errorHelp = document.createElement("p");
        errorHelp.innerHTML = `<b>Troubleshooting tips:</b>
        <ul>
            <li>Check that the FastAPI server is running</li>
            <li>Verify that the boxes.yml file exists and is properly formatted</li>
            <li>Check the server logs for more details</li>
        </ul>`;
        errorDiv.appendChild(errorHelp);

        container.appendChild(errorDiv);
    }
}

// Execute initialization immediately - no need to wait for DOMContentLoaded as script is already deferred
initialize();