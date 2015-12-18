import argparse
import pygame, sys
from pygame.locals import *
import random
from arbasdk import Arbapp, Rate


#Number of frames per second
FPS = 10

###Sets size of grid
WINDOWWIDTH = 15
WINDOWHEIGHT = 10

#Determine number of cells in horizonatl and vertical plane
CELLWIDTH = 15
CELLHEIGHT = 10


class GoL(Arbapp):
    def __init__(self, argparser):
        Arbapp.__init__(self, argparser)
        self.BG_COLOR = 'black'
        self.DEAD_COLOR = 'white'
        self.LIVING_COLOR = 'green'
        pygame.init()
        self.FPSCLOCK = pygame.time.Clock()
        self.lifeDict = self.blankGrid() # creates library and Populates to match blank grid
        self.lifeDict = self.startingGridRandom() # Assign random life

    #Sets all cells as dead (0)
    def blankGrid(self):
        gridDict = {}
        #creates dictionary for all cells
        for y in range (CELLHEIGHT):
            for x in range (CELLWIDTH):
                gridDict[x,y] = 0 #Sets cells as dead
        return gridDict

    def run(self):
        rate = Rate(2.0)

        # #Colours the live cells, blanks the dead
        # for item in self.lifeDict:
        #     with self.model:
        #         self.colourGrid(item)

        while True: #main game loop
            #runs a tick
            self.lifeDict = self.tick()

            #Colours the live cells, blanks the dead
            for item in self.lifeDict:
                with self.model:
                    self.colourGrid(item)

            rate.sleep()

    #Colours the cells green for life and white for no life
    def colourGrid(self, item):
        x = item[0]
        y = item[1]
        if self.lifeDict[item] == 0:
            self.model.set_pixel(x, y, self.DEAD_COLOR)
        if self.lifeDict[item] == 1:
            self.model.set_pixel(x, y, self.LIVING_COLOR)
        return None

    #Assigns a 0 or a 1 to all cells
    def startingGridRandom(self):
        for item in self.lifeDict:
            self.lifeDict[item] = random.randint(0,1)
        return self.lifeDict

    #Determines how many alive neighbours there are around each cell
    def getNeighbours(self, item):
        neighbours = 0
        for x in range (-1,2):
            for y in range (-1,2):
                checkCell = (item[0]+x,item[1]+y)
                if checkCell[0] < CELLWIDTH  and checkCell[0] >=0:
                    if checkCell [1] < CELLHEIGHT and checkCell[1]>= 0:
                        if self.lifeDict[checkCell] == 1:
                            if x == 0 and y == 0: # negate the central cell
                                neighbours += 0
                            else:
                                neighbours += 1
        return neighbours

    #determines the next generation by running a 'tick'
    def tick(self):
        newTick = {}
        for item in self.lifeDict:
            #get number of neighbours for that item
            numberNeighbours = self.getNeighbours(item)
            if self.lifeDict[item] == 1: # For those cells already alive
                if numberNeighbours < 2: # kill under-population
                    newTick[item] = 0
                elif numberNeighbours > 3: #kill over-population
                    newTick[item] = 0
                else:
                    newTick[item] = 1 # keep status quo (life)
            elif self.lifeDict[item] == 0:
                if numberNeighbours == 3: # cell reproduces
                    newTick[item] = 1
                else:
                    newTick[item] = 0 # keep status quo (death)
        return newTick


if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Game of Life')

    app = GoL(parser)
    app.start()
    app.close("end of app")
