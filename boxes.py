import os
import random
import pygame
import math
import threading
import numpy
from rtmaii import rtmaii
import sys

os.environ["SDL_VIDEO_CENTERED"] = "1"

screen_size = 600

screen = pygame.display.set_mode((screen_size, screen_size))
pygame.display.set_caption("Example RTMA")


class Box(object):
    """ Circle Class for creating an output file that users can use for future spectrogram data.

        Attributes:
            - id (int): Unique Id for a box
            - neighbours (list): All the other boxes within the screen
            - y (int): The y co-odrinate of the box
            - x (int): The x co-odrinate of the box
            - width (int): The width of the box
            - height (int): The height of the box
            - speedX (int): The speed of the box in x-axis
            - speedY (int): The speed of the box in y-axis
            - colour (list): The RGB values of the boxes colour
            - bkgColour (list): THe background colour
    """

    def __init__(self, id, otherObjs):
        self.id = id
        self.neighbours = otherObjs
        self.y = random.randint(50, 550)
        self.x = random.randint(50, 550)
        self.width = 50
        self. height = 50
        self.speedX = random.randint(1, 2)
        self.speedY = random.randint(1, 2)
        self.colour = (0,0,0)
        self.bkgColour = (255,255,255)


        self.rect =  pygame.rect.Rect((self.x, self.y, self.width, self.height))

    def untangle(self):
    """ 
    
    This function untangles boxes which become intertwined and makes boxes opposite directions

    """
        for i in range(0, len(self.neighbours)):
            if(self.rect.contains(self.neighbours[i])):
                self.speedY = self.speedY * -1
                self.speedX = self.speedX * -1
                self.neighbours[i].speedY = self.neighbours[i].speedY * -1
                self.neighbours[i].speedX = self.neighbours[i].speedX * -1

    
    def collision(self):
    """ 
    
    This function detects collision between boxes and makes respective boxes move opposite directions

    """
        for i in range(0, len(self.neighbours)):
            if(self.rect.colliderect(self.neighbours[i])):
                self.speedY = self.speedY * -1
                self.speedX = self.speedX * -1
                self.neighbours[i].speedY = self.neighbours[i].speedY * -1
                self.neighbours[i].speedX = self.neighbours[i].speedX * -1

    def move(self):
    """ 
    
    This function updates the coordinates of the boxes

    """
        self.y = self.y + self.speedY
        self.x = self.x + self.speedX

        if(self.y - self.height  < 0 or self.y + self.height > screen_size):
            self.speedY = self.speedY * -1
        elif(self.x - self.width  < 0 or self.x + self.width > screen_size):
            self.speedX = self.speedX * -1

        self.rect.move_ip(self.speedX, self.speedY)

    def update(self, screen, boxColour):
        self.colour = boxColour

    def draw(self, surface, backgroundColour):
        pygame.draw.rect(screen, self.colour, self.rect)


class Listener(threading.Thread):
    """ Starts analysis and holds a state of analysed results.
        TODO: Store state over time to allow for rewinding through results.
    """
    def __init__(self):

        self.state = {
            'pitch': 0,
            'note': {'note':"A"},
            'genre': "N/A",
            'spectogramData':numpy.zeros([128,128,128])}

        callbacks = []
        for key, _ in self.state.items():
            callbacks.append({'function': self.callback, 'signal': key})

        self.analyser = rtmaii.Rtmaii(callbacks,
                                      mode='INFO',
                                      track=r'./test_data/spectogramTest.wav',
                                     )

        threading.Thread.__init__(self, args=(), kwargs=None)
        self.setDaemon(True)
        self.start()

    def start_analysis(self):
        """ Start analysis. """
        self.analyser.start()

    def stop_analysis(self):
        """ Stop analysis and clear existing state. """
        self.analyser.stop()

    def is_active(self):
        """ Check that analyser is still running. """
        return self.analyser.is_active()

    def run(self):
        """ Keep thread alive. """
        while True:
            pass

    def callback(self, data, **kwargs):
        """ Set data for signal event. """
        signal = kwargs['signal']
        if signal == 'genre':
            print(data)
        self.state[signal] = data

    def get_item(self, item):
        """ Get the latest value. """
        return self.state[item]


pygame.init()
boxNumbers = 7
listener = Listener()
listener.start_analysis()
boxes = []

pitchDict = {'C' : (202,21,116), 
                    'C#/Db' : (16,170,110), 
                    "D" : (218,86,37), 
                    "D#/Eb" : (28,114,165), 
                    "E" : (235,227,54), 
                    "F" : (119,45,126), 
                    "F#/Gb" : (105,181,64), 
                    "G" : (208,37,56), 
                    "G#/Ab" : (3,165,167), 
                    "A" : (235,151,38), 
                    "A#/Bb" : (76,71,140), 
                    "B" : (185,207,57)}

genreDict = {'Rock' : (10,21,116),
                    'Hip-Hop' : (40,70,160),
                    'Folk' : (130,160,182),
                    'Electric' : (172,255,1),
                    'N/A': (255,255,255)}


for i in range(0, boxNumbers):
    boxes.append(Box(i, boxes))

clock = pygame.time.Clock()
running = True


while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            break
            running = False
    pitch = listener.get_item('note')['note']
    newColour = pitchDict[pitch]
    genre = listener.get_item('genre')
    newBKGColour = genreDict[genre]

    screen.fill(newBKGColour)


    for box in boxes:
        
        box.draw(screen, newBKGColour)
        box.update(screen, newColour)
        box.untangle()
        box.collision()
        box.move()
          
    pygame.display.update()
    clock.tick(200)
