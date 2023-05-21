import pyglet
from pyglet import shapes
from config import WINDOW_HEIGHT


# Basic enemy class
class Enemy:
    cars = []

    def __init__(self, x, img):
        self.img = img
        self.x = x
        self.y = WINDOW_HEIGHT
        self.height = self.img.height
        self.width = self.img.width
        self.sprite = pyglet.sprite.Sprite(img=self.img, x=self.x,
                                           y=self.y)

    def update(self, speed):
        self.y = self.y - speed
        self.sprite = pyglet.sprite.Sprite(img=self.img, x=self.x,
                                           y=self.y)

    def draw(self):
        self.sprite.draw()
