#!/usr/bin/env python
"""
    Arbalet - ARduino-BAsed LEd Table
    Lights Hero - Guitar Hero/Frets-on-fire like game

    In this app, a lane is one of the 5 colored lanes (vertical), a line
    corresponds to a specific timestamp, an intersection between a line and
    a lane is a cell that can have different states: background, marker,
    active, bump.

    Class SongReader reads a song in the fretsonfire format line-by-line.
    Class LightsHero is the main controller
    Class Renderer renders the grid on the table

    Copyright 2015 Yoan Mollard - Arbalet project - http://github.com/arbalet-project
    License: GPL version 3 http://www.gnu.org/licenses/gpl.html
"""
from time import time
from os import path
from SongReader import SongReader
from SoundManager import SoundManager
from UserHits import UserHits
from arbasdk import Arbapp, Arbapixel, Rate


class Renderer():
    """
    This class renders the game on Arbalet
    """
    def __init__(self, model, grid, bottom_bar, table_height, num_lanes, table_width):
        self.model = model
        self.grid = grid
        self.bar = bottom_bar
        self.height = table_height
        self.width = table_width
        self.num_lanes = num_lanes
        self.colors = ['darkgreen', 'darkred', 'orange', 'navy', 'deeppink']
        self.intensity = {'background': 0.05, 'marker': 0.03, 'active': 0.9}
        self.flash_color = False  # Boolean giving a "burning" impression

    def update_view(self):
        self.model.lock()
        # Big area of coming notes
        for lane in range(self.num_lanes):
            for chunk_lane in range(self.width/self.num_lanes):
                w = lane*self.width/self.num_lanes + chunk_lane
                for h in range(self.height-1): # -1 in order not to update the bottom bar
                    if self.grid[h][lane]=='bump':
                        color = Arbapixel((100, 100, 100)) + Arbapixel(self.colors[lane])
                    else:
                        color = Arbapixel(self.colors[lane])*self.intensity[self.grid[h][lane]]
                    self.model.set_pixel(h, w, color)

        # Bottom bar of present notes
        for lane in range(self.num_lanes):
            if self.bar[lane]=='hit' and self.flash_color or self.bar[lane]=='idle':
                # To make the note "burning" we alternate white/color when self.colors[lane]=='hit'
                color = self.colors[lane]
            else:
                color = 'white'
            for chunk_lane in range(self.width/self.num_lanes):
                w = lane*self.width/self.num_lanes + chunk_lane
                self.model.set_pixel(self.height-1, w, color)
        self.model.unlock()
        self.flash_color = not self.flash_color

class LightsHero(Arbapp):
    def __init__(self, num_lanes, path, level, speed):
        Arbapp.__init__(self)
        self.num_lanes = num_lanes
        self.score = 0
        self.speed = float(speed)
        self.rate = Rate(self.speed)
        self.grid = [['background']*num_lanes for h in range(self.height)] # The coming notes (last line included even if it will overwritten by the bottom bar)
        self.bar = ['idle']*num_lanes # The bottom bar, idle = not pressed, hit = pressed during a note, pressed = pressed outside a note

        # Threads creation and starting
        self.renderer = Renderer(self.model, self.grid, self.bar, self.height, num_lanes, self.width)
        self.reader = SongReader(path, num_lanes, level, speed)
        self.sound = SoundManager(path)
        self.hits = UserHits(self.num_lanes)

    def next_line(self):
        # Delete the last line leaving the grid
        # Note : The bottom bar will overwrite the last line but the latter needs to be kept to draw the bottom bar
        for l in range(self.height-1, 0, -1):
            for w in range(self.num_lanes):
                self.grid[l][w] = self.grid[l-1][w]

        # Ask for a new line to the song reader and fill the top of the grid with it
        new_line = self.reader.read()
        for lane in range(self.num_lanes):
            self.grid[0][lane] = new_line[lane]

    def process_user_hits(self):
        """
        Read user inputs, update the bottom bar with key states and warn the UserHits class to update the score
        """
        for lane in range(self.num_lanes):
            must_press = self.grid[self.height-1][lane] == 'active' or self.grid[self.height-1][lane] == 'bump'
            pressed = self.hits.get_pressed_keys()[lane]
            if must_press and pressed:
                status = 'hit'
            elif pressed:
                status = 'pressed'
            else:
                status = 'idle'
            self.bar[lane] = status

            # warn the user hits class whether the note has to be played
            self.hits.set_note(lane, self.grid[self.height-1][lane] in ['bump', 'active'])

    def display_score(self):
        levels = [15, 40, 60, 80, 90, 101]
        sentences = ["did you really play?", "you need to practice...", "I'm pretty sure you can do better...",
                    "that's a fair score!", "awesome, you're a master!", "incredible, did you cheat?"]
        colors = ['darkred', 'orange', 'gold', 'yellowgreen', 'green', 'white']
        score = int((100.*self.hits.score)/self.hits.max_score)

        for i, level in enumerate(levels):
            if score<level:
                sentence = sentences[i]
                color = colors[i]
                break

        print "You scored", score, '% with', self.hits.score, 'hits over', self.hits.max_score

        if self.hits.score>0:
            self.model.write("You scored {}%, {}".format(score, sentence), color)

    def run(self):
        countdown = self.height # Countdown triggered after Midi's EOF
        start = time()

        # We loop while the end countdown is not timed out
        # it starts decreasing only when EOF is returned by the song reader
        while countdown>0:
            self.next_line()
            self.process_user_hits()
            self.renderer.update_view()

            if self.reader.eof:
                countdown -= 1

            # delayed sound playing while the first notes are reaching the bottom bar
            if not self.sound.started and time()-start > (self.height-2)/self.speed:
                self.sound.start()

            self.rate.sleep()
        self.display_score()


song = path.join(path.dirname(__file__), 'songs', 'Feelings')
t = LightsHero(num_lanes=5, path=song, level='expert', speed=15)
t.start()
