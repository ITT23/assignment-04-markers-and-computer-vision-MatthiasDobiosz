import numpy as np
import pyglet
import cv2
from config import WINDOW_HEIGHT


# Basic Player class
class Player:
    def __init__(self, img):
        self.contours = None
        self.img = img
        self.width = img.width
        self.height = img.height
        self.sprite = None
        self.x = None
        self.y = None
        self.exists = False

    def update(self, img):
        self.detectContours(img)
        self.generateSprite()

    def generateSprite(self):
        if self.contours is not None:
            # get highest Point
            # Generated with ChatGPT
            highestPoint = tuple(
                self.contours[self.contours[:, :, 1].argmin()][0])
            # reverse y-coordinate
            correctY = WINDOW_HEIGHT - highestPoint[1]
            self.x = highestPoint[0]
            self.y = correctY
            self.sprite = pyglet.sprite.Sprite(img=self.img, x=self.x,
                                               y=self.y)
            self.exists = True
        else:
            self.sprite = None
            self.x = None
            self.y = None
            self.exists = False

    # detect Hand/Finger Contours
    # https://medium.com/analytics-vidhya/hand-detection-and-finger-counting-using-opencv-python-5b594704eb08
    def detectContours(self, img):
        hsvim = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower = np.array([0, 48, 80], dtype="uint8")
        upper = np.array([20, 255, 255], dtype="uint8")
        skinRegionHSV = cv2.inRange(hsvim, lower, upper)
        blurred = cv2.blur(skinRegionHSV, (2, 2))
        ret, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY)

        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE,
                                               cv2.CHAIN_APPROX_SIMPLE)
        try:
            contours = max(contours, key=lambda x: cv2.contourArea(x))
            self.contours = contours
        except:
            self.contours = None
