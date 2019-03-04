#imported libraries

#Graphics and game library
import pygame
from pygame.locals import *

#used to generate random numbers for randomised mazes
import random

#Library used to save to and load from a file for maze class objects
import shelve

#Main class sets up game board and handles most general functions
class Main:

    #static method to force a variable to have a value between a minimum and maximum
    @staticmethod
    def clamp(number, min, max):
        if max != None:
            if number > max:
                number = max
        if min != None:
            if number < min:
                number = min
        return number

    #Methods to select a function for the "update maze" button
    def chooseBestFirst(self):
        self.cancelAction(self)
        self.activeButton = ("solve", "bestFirst")

    def chooseBreadthFirst(self):
        self.cancelAction(self)
        self.activeButton = ("solve", "breadthFirst")

    def chooseDijkstra(self):
        self.cancelAction(self)
        self.activeButton = ("solve", "dijkstra")

    def chooseDepthFirst(self):
        self.cancelAction(self)
        self.activeButton = ("generate", "depthFirst")

    def choosekruskul(self):
        self.cancelAction(self)
        self.activeButton = ("generate", "kruskul")

    def chooseDivision(self):
        self.cancelAction(self)
        self.activeButton = ("generate", "division")
    ###

    #used whenever play/pause button is pressed
    #starts either Solve.solve function or Generate.generate function depending on what is selected
    def updateMaze(self):
        if self.activeRoutine[0] == "solve":
            Solve.solveUpdate(Solve)
        elif self.activeRoutine[0] == "generate":
            Generate.update(Generate)

    #cancels current action and resets class variables so that they can be started again
    def cancelAction(self):
        Solve.open = {}
        Solve.closed = {}
        Solve.path = {}
        Solve.solveTarget = None
        Solve.start = None

        Generate.sizeX = 0
        Generate.sizeY = 0
        Generate.cellStack = []
        Generate.walls = []
        Generate.sets = {}
        Generate.start = None
        Generate.end = None
        Generate.sectors = None

        self.activeButton = (None, None)
        self.activeRoutine = (None, None)

        Main.startPos = None
        Main.endPos = None

    #Loads save file from shelve file amd sets the gameboards cell array (Maze.cells) to it
    def load(self):
        if Mouse.repeat(Mouse):
            cellArray = shelve.open("saveFile.db")
            if "save" in cellArray:
                Maze.cells = cellArray["save"]
            cellArray.close()

    #Opens save file and shelves the cell array of the gameboard to a part of the file called "save"
    def save(self):
        if Mouse.repeat(Mouse):
            cellArray = shelve.open("saveFile.db")
            cellArray["save"] = Maze.cells
            cellArray.close()

    #sets up gameBoard by first loading a premade default file for cellArray or creating one if it doesnt exist
    #then calling scalemaze function to make sure the maze can be drawn
    def setup(self):
        Button.buttonSetup(Button)

        cellArray = shelve.open("saveFile.db")
        if "default" in cellArray:
            Maze.cells = cellArray["default"]
        else:
            Maze.generateCells(Maze)
            cellArray["default"] = Maze.cells
        cellArray.close()
        Maze.scaleMaze(Maze)

    #initial set up of class variables for class "Main"
    activeButton = (None, None)
    activeRoutine = (None, None)

    startPos = (None, None)
    endPos = (None, None)

    spaceX = 183
    spaceY = 15
    minDisplayWidth = 650
    minDisplayHeight = 365
    displayWidth = 650
    displayHeight = 450

    end = False


#Class contains game board data, draws game board and allows user interaction with the game board
class Maze:

    #method to initialise cell objects for the game board with default inactive wall state and place holder values for generating and solving mazes. And a unique coordinate
    def __init__(self, x, y):
        self.active = True
        self.coords = (x, y)

        self.hCost = 0
        self.gCost = 0
        self.fCost = 0
        self.parent = None

        self.set = None

    #mouse wheel changes the size of cells when drawn to give the effect of zooming in
    #middle mouse changes the start point when rendering the game board to give the effect of panning around
    def zoom(self):
        if Mouse.repeat(Mouse):
            if Mouse.scrollUp:
                self.cellSize = Main.clamp(self.cellSize + 1, 8, 240)
            elif Mouse.scrollDown:
                self.cellSize = Main.clamp(self.cellSize - 1, 8, 240)
                self.startX = Main.clamp(self.startX, 0, self.cellSize * self.size - (self.sizeX - self.borderSize))
                self.startY = Main.clamp(self.startY, 0, self.cellSize * self.size - (self.sizeY - self.borderSize))
        
        if Mouse.middle and Mouse.mouseDown:
            self.startX = Main.clamp(self.startX - (Mouse.relMousePos[0]), 0, self.cellSize * self.size - (self.sizeX - self.borderSize))
            self.startY = Main.clamp(self.startY - (Mouse.relMousePos[1]), 0, self.cellSize * self.size - (self.sizeY - self.borderSize))

            self.scaleMaze(self)

    #decides which action to perform when the game board is clicked on
    #if mouse is scrolling it will call interact maze, if mouse is clicking and there is an algorithm active it will allow user to choose start/end point.
    #if no algorithm is active maze interact will be called
    def pressMaze(self):
        if Mouse.scrollUp or Mouse.scrollDown or Mouse.middle:
            self.mazeInteract(self)
            
        elif Main.activeButton[0] == "generate":
            Generate.generateStart(Generate)

        elif Main.activeButton[0] == "solve":
            Solve.solveStart(Solve)

        else:
            self.mazeInteract(self)

    #called when mouse clicks on game board
    #Will place or remove walls from cells or call maze zoom if mouse is scrolling
    def mazeInteract(self):
        if Mouse.right:
            coord = Mouse.clickToCoord(Mouse)
            self.cells[coord[0]][coord[1]].active = True
        elif Mouse.left:
            coord = Mouse.clickToCoord(Mouse)
            self.cells[coord[0]][coord[1]].active = False

        elif Mouse.middle or Mouse.scrollDown or Mouse.scrollUp:
            self.zoom(self)

    #Initialises 2d array of cells to make game board
    def generateCells(self):
        self.cells = []
        for i in range(self.size):
            self.cells.append([])
            for j in range(self.size):
                self.cells[i].append(Maze(i, j))

    #Called when game board is zoomed or window resized
    #moves start point for maze display method and changes size of game board to ensure perfect fit
    def scaleMaze(self):
        self.sizeX = Main.displayWidth - Main.spaceX
        self.sizeY = Main.displayHeight - Main.spaceY
        self.startX = Main.clamp(self.startX, 0, self.cellSize * self.size - (self.sizeX - self.borderSize))
        self.startY = Main.clamp(self.startY, 0, self.cellSize * self.size - (self.sizeY - self.borderSize))

    #finds range of cells to be drawn in a frame
    def findCoordRange(self):
        firstXCoord = (self.startX // self.cellSize)
        firstYCoord = (self.startY // self.cellSize)
        lastXcoord = Main.clamp(((self.startX + Maze.sizeX) // self.cellSize), None, self.size - 1)
        lastYcoord = Main.clamp(((self.startY + Maze.sizeY) // self.cellSize), None, self.size - 1)

        return firstXCoord, firstYCoord, lastXcoord, lastYcoord

    #called once per frame, draws cells, gridlines and border on gameboard
    def displayMaze(self):
        pygame.draw.rect(gameDisplay, blue, (0, 0, Maze.sizeX + self.borderSize, Maze.sizeY + self.borderSize)) #border square
        pygame.draw.rect(gameDisplay, grey, (self.borderSize, self.borderSize, Maze.sizeX - self.borderSize, Maze.sizeY - self.borderSize)) #grey backround color for empty cells
        firstX, firstY, lastX, lastY = self.findCoordRange(self) #called to find range of cells to draw
        offSetX = self.cellSize - (self.startX % self.cellSize)
        offSetY = self.cellSize - (self.startY % self.cellSize)

        #x1, y1 used as start point for current cell to draw. x2, y2 used as end point for current cell to draw.
        #after each cell draw x1/y1 becomes x2/y2 and x2/y2 += cell size
        x1 = self.borderSize
        y1 = self.borderSize
        x2 = offSetX
        y2 = offSetY

        #nested for loop used to draw cells
        for i in range(firstX, lastX + 1):
            for j in range(firstY, lastY + 1):
                if not self.cells[i][j].active:
                    gameDisplay.fill(black , (x1, y1, x2, y2))
                elif (i, j) == Main.startPos:
                    gameDisplay.fill(yellow, (x1, y1, x2, y2))
                elif (i, j) == Main.endPos:
                    gameDisplay.fill(yellow, (x1, y1, x2, y2))

                elif (i, j) in Solve.path:
                    gameDisplay.fill(cyan, (x1, y1, x2, y2))
                elif (i, j) in Solve.open:
                    gameDisplay.fill(green, (x1, y1, x2, y2))
                elif (i, j) in Solve.closed:
                    gameDisplay.fill(red, (x1, y1, x2, y2))

                y1 += y2
                y2 = self.cellSize
                if y2 + y1 > Maze.sizeY:
                    y2 = Maze.sizeY - y1
            x1 += x2
            x2 = self.cellSize
            if x2 + x1 > Maze.sizeX:
                x2 = Maze.sizeX - x1
            y1 = self.borderSize
            y2 = self.cellSize - (self.startY % self.cellSize)
        x1 = self.borderSize
        x2 = self.sizeX - 1
        y1 = self.borderSize + offSetY

        #while loop used to draw gridlines
        while y1 <= self.sizeY:
            pygame.draw.line(gameDisplay, black, (x1, y1), (x2, y1), 1)
            y1 += self.cellSize
        x1 = self.borderSize + offSetX
        y1 = self.borderSize
        y2 = self.sizeY - 1
        while x1 <= self.sizeX:
            pygame.draw.line(gameDisplay, black, (x1, y1), (x1, y2), 1)
            x1 += self.cellSize

    #Initial setup for maze class wide variables
    cells = []
    size = 500 #size of gameboard (500*500 cells)

    sizeX = 0
    sizeY = 0
    startX = 0
    startY = 0

    cellSize = 25
    borderSize = 15

#class contains algorithms and setup method for generating mazes onto the gameboard
class Generate:

    #initialisation of random division method for maze generation
    #Division generate method creates box of empty cells with walls surrounding them.
    #stack sectors created containing single sector in the box of empty cells
    def divisionGenerate(self):
        for x in range(self.sizeX):
            x += self.start[0]
            for y in range(self.sizeY):
                y += self.start[1]
                if x == Main.clamp(x, self.start[0] + 1, self.end[0] - 1) and y == Main.clamp(y,self.start[1] + 1, self.end[1] - 1):
                    Maze.cells[x][y].active = True
                else:
                    Maze.cells[x][y].active = False

        self.start[0] += 1
        self.end[0] += -1
        self.start[1] += 1
        self.end[1] += -1
        self.sizeX += -2
        self.sizeY += -2

        self.sectors = [(self.sizeX, self.sizeY , (self.start[0], self.start[1]))]

    #called once per frame while algorithm is selected and play button is held down
    #splits first sector in sectors stack into 4 seperate sectors with dividing walls between each sector unless sector has a width or height of 1
    def divisionUpdate(self):
        if len(self.sectors) != 0:
            sectorWidth = self.sectors[0][0]
            sectorHeight = self.sectors[0][1]
            sectorStart = self.sectors[0][2]

            if sectorWidth > 1 and sectorHeight > 1:
                dividePoint = (sectorStart[0] + random.randint(1, sectorWidth // 2) * 2 - 1,
                               sectorStart[1] + random.randint(1, sectorHeight // 2) * 2 - 1)

                for i in range(sectorWidth):
                    Maze.cells[sectorStart[0] + i][dividePoint[1]].active = False

                for i in range(sectorHeight):
                    Maze.cells[dividePoint[0]][sectorStart[1] + i].active = False

                newSectorWidths = (dividePoint[0] - sectorStart[0], sectorWidth - (dividePoint[0] - sectorStart[0]) - 1)
                newSectorHeights = (dividePoint[1] - sectorStart[1], sectorHeight - (dividePoint[1] - sectorStart[1]) - 1)
                newSectorStartsX = (sectorStart[0], dividePoint[0] + 1)
                newSectorStartsY = (sectorStart[1], dividePoint[1] + 1)

                holesToMake = []
                holesToMake.append((sectorStart[0] + (random.randint(1, (newSectorWidths[0] // 2) + 1) * 2 - 2),dividePoint[1]))
                holesToMake.append((dividePoint[0] + (random.randint(1, (newSectorWidths[1] // 2) + 1) * 2 - 1),dividePoint[1]))
                holesToMake.append((dividePoint[0],sectorStart[1] + (random.randint(1, (newSectorHeights[0] // 2) + 1) * 2 - 2)))
                holesToMake.append((dividePoint[0],dividePoint[1] + (random.randint(1, (newSectorHeights[1] // 2) + 1) * 2 - 1)))

                del holesToMake[random.randint(0,3)]
                for hole in holesToMake:
                    Maze.cells[hole[0]][hole[1]].active = True

                del self.sectors[0]
                self.sectors.append((newSectorWidths[0], newSectorHeights[0], (newSectorStartsX[0], newSectorStartsY[0])))
                self.sectors.append((newSectorWidths[0], newSectorHeights[1], (newSectorStartsX[0], newSectorStartsY[1])))
                self.sectors.append((newSectorWidths[1], newSectorHeights[0], (newSectorStartsX[1], newSectorStartsY[0])))
                self.sectors.append((newSectorWidths[1], newSectorHeights[1], (newSectorStartsX[1], newSectorStartsY[1])))
            else:
                del self.sectors[0]
                self.divisionUpdate(self)
        else:
            Main.activeRoutine = (None, None)
            print("done")

    #initialisation of kruskul maze generation algorithm
    #creates box of wall cells
    #Creates shuffled stack of wall coordinates
    #dictionary of maze cell coordinates with the cell coordinate and data as the key
    def kruskulGenerate(self):
        for x in range(self.sizeX):
            x += self.start[0]
            for y in range(self.sizeY):
                y += self.start[1]
                Maze.cells[x][y].active = False

        self.start[0] += 1
        self.end[0] += -1
        self.start[1] += 1
        self.end[1] += -1
        self.sizeX += - 2
        self.sizeY += - 2

        for y in range(self.sizeY):
            if y % 2 == 0:
                for x in range(self.sizeX):
                    if x % 2 == 0:
                        key = str(len(self.sets))
                        self.sets[key] = [(x, y)]
                        Maze.cells[x + self.start[0]][y + self.start[1]].set = key
                    else:
                        self.walls.append(((x, y), (1, 0)))
            else:
                for x in range((self.sizeX // 2) + 1):
                    self.walls.append(((x * 2, y), (0, 1)))
        random.shuffle(self.walls)

    #called once per frame while algorithm is selected and play button is held down
    #checks first wall in wall stack, if both cells adjacent to the wall are in seperate sets, the wall is removed and sets merged
    def kruskulUpdate(self):
        if len(self.walls) != 0:
            wall = self.walls[0]
            cell1 = Maze.cells[wall[0][0] + wall[1][0] + self.start[0]][wall[0][1] + wall[1][1] + self.start[1]]
            cell2 = Maze.cells[wall[0][0] - wall[1][0] + self.start[0]][wall[0][1] - wall[1][1] + self.start[1]]
            if cell1.set != cell2.set:
                Maze.cells[wall[0][0] + self.start[0]][wall[0][1] + self.start[1]].active = True
                cell1.active = True
                cell2.active = True
                for coord in self.sets[cell2.set]:
                    self.sets[cell1.set].append(coord)
                    Maze.cells[coord[0] + self.start[0]][coord[1] + self.start[1]].set = cell1.set
            del self.walls[0]
        else:
            Main.activeRoutine = (None, None)
            print("done")

    #initialisation method for depth first maze generation algorithm
    #creates box of wall cells and appends starting cell to cell stack
    def depthFirstGenerate(self):
        for x in range(self.sizeX):
            x += self.start[0]
            for y in range(self.sizeY):
                y += self.start[1]
                Maze.cells[x][y].active = False

        self.start[0] += 1
        self.end[0] += -1
        self.start[1] += 1
        self.end[1] += -1

        self.cellStack = [self.start]

    #called once per frame while algorithm is selected and play button is held down
    #checks first cell in cells stack, if univisited cell adjacent to current cell, connect both cells and append new cell to cell stack
    def depthFirstUpdate(self):
        if len(self.cellStack) > 0:
            currentCell = self.cellStack[0]
            Maze.cells[currentCell[0]][currentCell[1]].active = True
            found = False

            random.shuffle(self.orthDirections)
            pointer = 0

            while found == False and pointer < 4:
                direction = self.orthDirections[pointer]
                pointer += 1
                nextCellX = currentCell[0] + (direction[0] * 2)
                nextCellY = currentCell[1] + (direction[1] * 2)

                if not ((nextCellX < self.start[0]) or (nextCellY < self.start[1]) or (nextCellX > self.end[0]) or (nextCellY > self.end[1])):
                    nextCellCoords = (nextCellX, nextCellY)
                    if Maze.cells[nextCellCoords[0]][nextCellCoords[1]].active == False:
                        found = True
                        Maze.cells[currentCell[0] + direction[0]][currentCell[1] + direction[1]].active = True
                        self.cellStack.insert(0, nextCellCoords)
                        currentCell = self.cellStack[0]

            #removes cell from stack if no unvisited cells found
            if pointer > 3:
                self.cellStack.pop(0)
        else:
            Main.activeRoutine = (None, None)
            print("finished")

    #called when start and end coords are both chosen by user and generate algorithm is active
    #chooses a maze generation algorithm to start
    def generate(self):
        self.sizeX = self.end[0] - self.start[0] + 1
        self.sizeY = self.end[1] - self.start[1] + 1
        if Main.activeRoutine[1] == "depthFirst":
            self.depthFirstGenerate(self)
        elif Main.activeRoutine[1] == "kruskul":
            self.kruskulGenerate(self)
        elif Main.activeRoutine[1] == "division":
            self.divisionGenerate(self)

    #called when play button is pressed and generate algorithm is active
    #calls algorithm update depending on which is active
    def update(self):
        if Main.activeRoutine[1] == "depthFirst":
            self.depthFirstUpdate(self)
        elif Main.activeRoutine[1] == "kruskul":
            self.kruskulUpdate(self)
        elif Main.activeRoutine[1] == "division":
            self.divisionUpdate(self)

    #called when game board is clicked and generate algorithm is active
    #places start and end nodes for generating a maze when mouse clicks
    def generateStart(self):
        if Mouse.left:
            coords = Mouse.clickToCoord(Mouse)
            self.start = [coords[0],coords[1]]
            Main.startPos = (coords[0],coords[1])
        elif Mouse.right:
            coords = Mouse.clickToCoord(Mouse)
            self.end = [coords[0],coords[1]]
            Main.endPos = (coords[0],coords[1])

        #moves start and end nodes if placement is invalid (wrong way round or wrong size)
        if self.start != None and self.end != None:
            if self.start[0] > self.end[0]:
                temp = self.start[0]
                self.start[0] = self.end[0]
                self.end[0] = temp
            if self.start[1] > self.end[1]:
                temp = self.start[1]
                self.start[1] = self.end[1]
                self.end[1] = temp

            if (self.end[0] - self.start[0]) % 2 == 1:
                self.end[0] += -1
            if (self.end[1] - self.start[1]) % 2 == 1:
                self.end[1] += -1

            Main.activeRoutine = Main.activeButton
            Main.activeButton = (None, None)
            Main.startPos = None
            Main.endPos = None
            self.generate(self)

    #Maze generation initial variable set up
    directions = ((1, 0), (0, -1), (-1, 0), (0, 1), (1, 1), (1, -1), (-1, -1), (-1, 1))
    orthDirections = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    sizeX = 0
    sizeY = 0

    cellStack = []

    walls = []
    sets = {}

    start = None
    end = None

    sectors = None

#class contains algorithms and setup method for pathfinding and solving mazes on the game board
class Solve:

    #retraces path using cell parent coordinates when pathfinding algorithm finds target
    def retracePath(self):
        while True:
            self.path[self.solveTarget] = self.solveTarget
            parent = Maze.cells[self.solveTarget[0]][self.solveTarget[1]].parent
            if parent != None:
                self.solveTarget = parent
            else:
                break

    #gets euclidian distance between two nodes
    def getDistance(self, cell, end):
        disX = abs(cell[0] - end[0])
        disY = abs(cell[1] - end[1])

        if (disX > disY):
            return int((14 * disY) + (10 * (disX - disY)))
        else:
            return int((14 * disX) + (10 * (disY - disX)))

    #initalisation method for dijksta search
    #adds start cell to open set
    def dijkstraSearch(self):
        self.closed = {}
        self.open = {}
        self.open[self.start] = 0

        self.dijkstraUpdate(self)

    #called once per frame while algorithm is selected and play button is held down
    #chooses cell in open set with lowest euclidian distance to start node as current cell
    #adds adjacent cells to open set and calculates each neibours distance to start node unless neigbour is target cell
    def dijkstraUpdate(self):
        end = self.solveTarget
        lowest = None
        currentCost = float("inf")
        if len(self.open) != 0:
            for cell in self.open:
                if self.open[cell] < currentCost:
                    lowest = cell

                    currentCost = self.open[cell]

            current = Maze.cells[lowest[0]][lowest[1]]
            self.closed[current.coords] = lowest
            del self.open[lowest]

            if current.coords == end:
                print("Found")
                Main.activeRoutine = (None, None)
                self.retracePath(self)
                return

            for direction in self.directions:
                if Main.clamp(current.coords[0] + direction[0], 0, Maze.size - 1) == current.coords[0] + direction[0] and Main.clamp(current.coords[1] + direction[1], 0, Maze.size - 1) == current.coords[1] + direction[1]:
                    if Maze.cells[current.coords[0] + direction[0]][current.coords[1]].active == True and Maze.cells[current.coords[0]][current.coords[1] + direction[1]].active == True:
                        neigbour = Maze.cells[current.coords[0] + direction[0]][current.coords[1] + direction[1]]
                    else:
                        continue
                else:
                    continue
                if neigbour.active == False or neigbour.coords in self.closed:
                    continue

                newCostToNeighbour = currentCost + self.getDistance(self, current.coords, neigbour.coords)
                if neigbour.coords in self.open:
                    if newCostToNeighbour < self.open[neigbour.coords]:
                        self.open[neigbour.coords] = newCostToNeighbour
                        neigbour.parent = current.coords
                else:
                    self.open[neigbour.coords] = newCostToNeighbour
                    neigbour.parent = current.coords

        else:
            Main.activeRoutine = (None, None)
            print("Not found")

    #initialisation of breadth first search algorithm
    #adds start node to open set
    def breadthFirstSearch(self):
        self.closed = {self.start: Maze.cells[self.start[0]][self.start[1]]}
        self.open = [self.start]

        self.breadthFirstUpdate(self)

    #called once per frame while algorithm is selected and play button is held down
    #chooses first cell in open cell stack as current cell
    #adds adjacent cells to open set and calculates each neibours distance to start node unless neigbour is target cell
    def breadthFirstUpdate(self):
        if len(self.open) != 0:
            current = Maze.cells[self.open[0][0]][self.open[0][1]]
            end = self.solveTarget

            del self.open[0]

            if current.coords == end:
                Main.activeRoutine = (None, None)
                print("Found")
                self.retracePath(self)
                return

            for direction in self.directions:
                if Main.clamp(current.coords[0] + direction[0], 0, Maze.size - 1) == current.coords[0] + direction[0] and Main.clamp(current.coords[1] + direction[1], 0, Maze.size - 1) == current.coords[1] + direction[1]:
                    if Maze.cells[current.coords[0] + direction[0]][current.coords[1]].active == True and Maze.cells[current.coords[0]][current.coords[1] + direction[1]].active == True:
                        neigbour = Maze.cells[current.coords[0] + direction[0]][current.coords[1] + direction[1]]
                    else:
                        continue
                else:
                    continue
                if neigbour.active == False or neigbour.coords in self.closed:
                    continue

                neigbour.parent = current.coords
                self.open.append(neigbour.coords)
                self.closed[neigbour.coords] = neigbour
        else:
            print("not found")
            Main.activeRoutine = (None, None)

    #initialisation of best first search algorithm
    #adds start cell to open set
    def bestFirstSearch(self):
        self.closed = {}
        self.open = {}
        self.open[self.start] = Maze.cells[int(self.start[0])][int(self.start[1])]

        self.bestFirstUpdate(self)

    #called once per frame while algorithm is selected and play button is held down
    #uses cell with lowest fcost and hcost as current cell (fcost = euclidian distance to end node (hcost) + real calculated distance to start node (gcost))
    #adds adjacent cells to open set and calculates each neibours new gcost and fcost node unless neigbour is target cell
    def bestFirstUpdate(self):
        end = self.solveTarget
        if len(self.open) != 0:
            lowestKey = None
            lowest = float("inf")
            for key in self.open:
                self.open[key].fCost = self.open[key].hCost + self.open[key].gCost
                if self.open[key].fCost < lowest:
                    lowest = self.open[key].fCost
                    lowestKey = key
                elif self.open[key].hCost < self.open[lowestKey].hCost and self.open[key].fCost == self.open[lowestKey].fCost:
                    lowestKey = key
            currentCoords = lowestKey
            current = Maze.cells[currentCoords[0]][currentCoords[1]]
            self.closed[current.coords] = current
            del self.open[current.coords]
            if current.coords == end:
                Main.activeRoutine = (None, None)
                print("Found")
                self.retracePath(self)
                return

            for direction in self.directions:
                if Main.clamp(current.coords[0] + direction[0],0,Maze.size - 1) == current.coords[0] + direction[0] and Main.clamp(current.coords[1] + direction[1],0,Maze.size - 1) == current.coords[1] + direction[1]:
                    if Maze.cells[current.coords[0] + direction[0]][current.coords[1]].active == True and Maze.cells[current.coords[0]][current.coords[1] + direction[1]].active == True:
                        neigbour = Maze.cells[current.coords[0] + direction[0]][current.coords[1] + direction[1]]
                    else:
                        continue
                else:
                    continue
                if neigbour.active == False or neigbour.coords in self.closed:
                    continue

                newCostToNeighbour = current.gCost + self.getDistance(self, current.coords, neigbour.coords)
                if newCostToNeighbour < neigbour.gCost or neigbour.coords not in self.open:
                    neigbour.gCost = newCostToNeighbour
                    neigbour.hCost = self.getDistance(self, neigbour.coords, end)
                    neigbour.parent = current.coords
                    if neigbour not in self.open:
                        self.open[neigbour.coords] = neigbour
        else:
            Main.activeRoutine = (None, None)
            print("Not found")

    #called when play button is pressed and generate algorithm is active
    #calls algorithm update depending on which is active
    def solveUpdate(self):
        if Main.activeRoutine[1] == "dijkstra":
            self.dijkstraUpdate(self)
        elif Main.activeRoutine[1] == "bestFirst":
            self.bestFirstUpdate(self)
        elif Main.activeRoutine[1] == "breadthFirst":
            self.breadthFirstUpdate(self)

    #called when start and end coords are both chosen by user and solve algorithm is active
    #chooses a path finding algorithm to start
    def solve(self):
        Maze.cells[int(self.start[0])][int(self.start[1])].parent = None

        if Main.activeRoutine[1] == "dijkstra":
            self.dijkstraSearch(self)
        elif Main.activeRoutine[1] == "bestFirst":
            self.bestFirstSearch(self)
        elif Main.activeRoutine[1] == "breadthFirst":
            self.breadthFirstSearch(self)

    #called when game board is clicked and solve algorithm is active
    #places start and target nodes for path finding when mouse clicks
    def solveStart(self):
        if Mouse.left:
            coords = Mouse.clickToCoord(Mouse)
            self.start = (coords[0], coords[1])
            Main.startPos = (coords[0], coords[1])
        elif Mouse.right:
            coords = Mouse.clickToCoord(Mouse)
            self.solveTarget = (coords[0], coords[1])
            Main.endPos = (coords[0], coords[1])
        if self.start != None and self.solveTarget != None:
            Main.activeRoutine = Main.activeButton
            Main.activeButton = (None, None)
            self.solve(self)

    #initialisation for solve class wide variables
    open = {}
    closed = {}
    path = {}
    solveTarget = None
    start = None
    directions = ((1,0), (0,-1), (-1,0), (0,1), (1,1), (1,-1), (-1,-1), (-1,1))


#Class used to display and manage on screen buttons
#detects when mouse clicks or hovers over a button
#calls functions when buttons are pressed
#game board is given a button however it does not scale in the same way or have an image or color to display
class Button:


    #initialisation method for button objects
    #buttons contain start/end coord, size value, relative position to game board, image or color to display and a function to perform when pressed
    #static x and static y determine if button is fixed or can move depending on size of game board and progmam window
    def __init__(self, startX, startY, buttonWidth, buttonHeight, actionDown,activeColour,inactiveColour,parametres,toggleColour,staticX,staticY):
        self.startFromMaze = [startX - Maze.sizeX,startY - Maze.sizeY]
        self.start = [startX, startY]
        self.size = [buttonHeight, buttonWidth]
        self.end = [self.start[0] + buttonWidth, self.start[1] + buttonHeight]
        self.actionDown = actionDown
        self.active = False
        self.activeColour = activeColour
        self.inactiveColour = inactiveColour
        self.toggleColour = toggleColour
        self.parametres = parametres
        self.staticX = staticX
        self.staticY = staticY

    #method to detect if mouse is hovering over a button
    #if mouse is hovering over a button, button is given active color and active button is set to the button key
    def findButton(self):
        mousePos = pygame.mouse.get_pos()
        for i in self.buttons:
            button = self.buttons[i]
            if mousePos[0] == Main.clamp(mousePos[0], button.start[0], button.end[0]):
                if mousePos[1] == Main.clamp(mousePos[1], button.start[1], button.end[1]):
                    if self.activeButton != None:
                        self.buttons[self.activeButton].active = False
                    button.active = True
                    self.activeButton = i
                    return
                else:
                    button.active = False
            if self.activeButton != None:
                self.buttons[self.activeButton].active = False
                self.activeButton = None

    #displays buttons on screen using button images
    def displayButtons(self):
        for i in self.buttons:
            button = self.buttons[i]
            if isinstance(button.activeColour, str): #detects if button is file name of an image
                if button.active:
                    gameDisplay.blit(self.images[button.activeColour],button.start)
                else:
                    gameDisplay.blit(self.images[button.inactiveColour], (button.start))

    #rescales buttons when program window is resized
    #buttons move and resize based on size of game board as to keep symetric with a uniform distance between each other
    def scaleButtons(self):
        for i in self.buttons:
            if i != "maze":
                button = self.buttons[i]
                if not button.staticX:
                    button.start = [Maze.borderSize + Maze.sizeX + button.startFromMaze[0],button.start[1]]
                    button.end = [button.start[0] + button.size[0], button.end[1]]
                if not button.staticY:
                    button.start = [button.start[0], Maze.borderSize + Maze.sizeX + button.startFromMaze[1]]
                    button.end = [button.end[0], button.start[1] + button.size[1]]
            else:
                button = self.buttons[i]
                button.size = [Maze.sizeX, Maze.sizeY]
                button.end = [button.start[0] + button.size[0], button.start[1] + button.size[1]]

    #loads button images onto buttons
    def getImages(self):
        for i in self.buttons:
            button = self.buttons[i]
            if isinstance(button.activeColour, str): #detects if color variable is an image
                self.images[button.activeColour] = pygame.image.load(button.activeColour)
                self.images[button.inactiveColour] = pygame.image.load(button.inactiveColour)

    #initialisation of all buttons used in program
    #calls __init__ method for button class for each button and calls getImages to load images
    def buttonSetup(self):
        self.buttons["maze"] = Button(Maze.borderSize, Maze.borderSize, Maze.sizeX, Maze.sizeY, Maze.pressMaze, None, None, Maze, None, True, True)

        self.buttons["bestFirst"] = Button(Maze.sizeX + 10, 5, 64, 64, Main.chooseBestFirst, "bfsa.jpg", "bfsia.jpg", Main, blue, False, True)
        self.buttons["breadthFirst"] = Button(Maze.sizeX + 10, 74, 64, 64, Main.chooseBreadthFirst, "brfsa.jpg", "brfsia.jpg", Main, blue, False, True)
        self.buttons["dijkstra"] = Button(Maze.sizeX + 10, 143, 64, 64, Main.chooseDijkstra, "dsa.jpg", "dsia.jpg", Main, blue, False, True)

        self.buttons["depthFirst"] = Button(Maze.sizeX + 94, 5, 64, 64, Main.chooseDepthFirst, "dfa.jpg", "dfia.jpg", Main, blue, False, True)
        self.buttons["kruskul"] = Button(Maze.sizeX + 94, 74, 64, 64, Main.choosekruskul, "ka.jpg", "kia.jpg", Main, blue, False, True)
        self.buttons["division"] = Button(Maze.sizeX + 94, 143, 64, 64, Main.chooseDivision, "da.jpg", "dia.jpg", Main, blue, False, True)

        self.buttons["updateMaze"] = Button(Maze.sizeX + 10, 227, 64, 64, Main.updateMaze, "updatea.jpg", "updateia.jpg", Main, blue, False, True)
        self.buttons["cancelAction"] = Button(Maze.sizeX + 94, 227, 64, 64, Main.cancelAction, "cancela.jpg", "cancelia.jpg", Main, blue, False, True)

        self.buttons["saveGame"] = Button(Maze.sizeX + 10, 296, 64, 64, Main.save, "sa.jpg", "sia.jpg", Maze, blue, False, True)
        self.buttons["loadGame"] = Button(Maze.sizeX + 94, 296, 64, 64, Main.load, "la.jpg", "lia.jpg", Maze, blue, False, True)

        self.getImages(Button)

    #initialisation for button class wide variables
    buttons = {}
    images = {}
    activeButton = None

#class to handle detection of mouse movement and mouse inputs
class Mouse:

    #converts mouse pixel coordinate to game board cell coordinate when game board is clicked
    def clickToCoord(self):
        x = (Maze.startX + self.absMousePos[0] - Maze.borderSize) // Maze.cellSize
        y = (Maze.startY + self.absMousePos[1] - Maze.borderSize) // Maze.cellSize
        x = Main.clamp(x,0,Maze.size - 1)
        y = Main.clamp(y, 0, Maze.size -1)

        return (x, y)

    #detects which mouse button is pressed when mouse down is detected
    def getMouseDown(self, button):
        if button == 1:
            self.left = True
        elif button == 2:
            self.middle = True
        elif button == 3:
            self.right = True
        elif button == 4:
            self.scrollUp = True
        elif button == 5:
            self.scrollDown = True

    #resets mouse button when button is released
    def getMouseUp(self, button):
        if button == 1:
            self.left = False
        elif button == 2:
            self.middle = False
        elif button == 3:
            self.right = False
        elif button == 4:
            self.scrollUp = False
        elif button == 5:
            self.scrollDown = False

    #detects if mouse button has been held down for more than one frame as to stop unintended button spamming
    def repeat(self):
        if self.repeats:
            self.repeats = False
            return True
        else:
            return False

    #initialisation of mouse class wide variables
    left = False
    middle = False
    right = False
    scrollDown = False
    scrollUp = False

    repeats = True
    mouseDown = False

    relMousePos = None
    absMousePos = None

#initialisation of global pygame variables and main setup
gameDisplay = pygame.display.set_mode((Main.minDisplayWidth, Main.minDisplayHeight),RESIZABLE) #pygame program window
pygame.display.set_caption("Maze Game")
fps = float("inf") #frames per second
clock = pygame.time.Clock()

#predefined rgb colors
black = (0,0,0)
grey = (200,200,200)
red = (255,0,0)
blue = (0,0,255)
green =(0,255,0)
white = (255,255,255)
yellow = (255,255,0)
cyan = (5,155,255)

Main.setup(Main)

#main while loop, called once per frame
while not Main.end:

    #gets pygame events
    for event in pygame.event.get():

        #terminates if exit button pressed
        if event.type == pygame.QUIT:
            Main.end = True

        #detects when mouse button is released and resets mouse down variables
        if event.type == pygame.MOUSEBUTTONUP:
            Mouse.getMouseUp(Mouse,event.dict["button"])
            Mouse.mouseDown = False

        #detects when mouse button pressed and sets mouse down variables depending on which button is pressed
        #calls zoom if scroll wheel used
        #mouse.repeats for spam detection
        if event.type == pygame.MOUSEBUTTONDOWN:
            Mouse.getMouseDown(Mouse,event.dict["button"])
            if event.dict["button"] == 4 or 5:
                Maze.zoom(Maze)
            Mouse.mouseDown = True
            Mouse.repeats = True

        #calls every time program window resized
        #rescales window, game board and button size and positions
        if event.type == VIDEORESIZE:
            Main.displayWidth = Main.clamp(event.dict['size'][0], Main.minDisplayWidth, None)
            Main.displayHeight = Main.clamp(event.dict['size'][1], Main.minDisplayHeight, None)
            gameDisplay = pygame.display.set_mode((Main.displayWidth, Main.displayHeight),RESIZABLE)
            gameDisplay.fill(white)
            Maze.scaleMaze(Maze)
            Button.scaleButtons(Button)

    #updates game boarc display
    Maze.displayMaze(Maze)

    #displays buttons and detects button press actions
    Button.findButton(Button)
    Button.displayButtons(Button)
    if Button.activeButton != None:
        if Mouse.mouseDown == True:
            Button.buttons[Button.activeButton].actionDown(Button.buttons[Button.activeButton].parametres)

    #displays updated frame on the screen by replacing old pixels
    pygame.display.update()

    #gets mouse movement
    Mouse.relMousePos = pygame.mouse.get_rel()
    Mouse.absMousePos = pygame.mouse.get_pos()

    #gives time between frames for event detection, program would otherwise freeze in an infinite unpausing loop
    clock.tick(fps)

#exit
pygame.quit()
quit()