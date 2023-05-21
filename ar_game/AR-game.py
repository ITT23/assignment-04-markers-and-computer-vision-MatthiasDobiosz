import numpy as np
import pyglet
from pyglet import clock
import cv2
import cv2.aruco as aruco
import sys
from PIL import Image
from arucoUtils import performPerspectiveWarp
from config import WINDOW_WIDTH, WINDOW_HEIGHT
from Player import Player
from Enemy import Enemy
import random

# Load Images
# Player Image taken from: https://opengameart.org/content/sword-sprites
# Other Images from: https://opengameart.org/content/roguelike-monsters
playerImage = pyglet.image.load('Images/sword.png')
batImage = pyglet.image.load('Images/bat_image.png')
goblinImage = pyglet.image.load('Images/goblin_image.png')
reaperImage = pyglet.image.load('Images/reaper_image.png')

video_id = 0

window = pyglet.window.Window(WINDOW_WIDTH, WINDOW_HEIGHT)

if len(sys.argv) > 1:
    video_id = int(sys.argv[1])

# Define the ArUco dictionary and parameters
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)
aruco_params = aruco.DetectorParameters()


# converts OpenCV image to PIL image and then to pyglet texture
# https://gist.github.com/nkymut/1cb40ea6ae4de0cf9ded7332f1ca0d55
def cv2glet(img, fmt):
    '''Assumes image is in BGR color space. Returns a pyimg object'''
    if fmt == 'GRAY':
        rows, cols = img.shape
        channels = 1
    else:
        rows, cols, channels = img.shape

    raw_img = Image.fromarray(img)
    raw_img = raw_img.resize((WINDOW_WIDTH, WINDOW_HEIGHT))
    raw_img = raw_img.tobytes()

    top_to_bottom_flag = -1
    bytes_per_row = channels * cols
    pyimg = pyglet.image.ImageData(width=cols,
                                   height=rows,
                                   fmt=fmt,
                                   data=raw_img,
                                   pitch=top_to_bottom_flag * bytes_per_row)
    return pyimg


# Create a video capture object for the webcam
cap = cv2.VideoCapture(video_id)

# Game class that handles overall State and updates
class Game:
    def __init__(self):
        self.player = Player(playerImage)
        self.enemies = []

        self.notDetectedCounters = 0
        self.validImage = False
        self.isGameOver = False

        self.score = 0
        self.spawnRate = 20
        self.spawnIncreaseTimer = 0
        self.lives = 3
        self.enemySpeed = 5
        self.difficulty = 'easy'

    def draw(self, img):
        # Convert the frame to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Detect ArUco markers in the frame
        corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, aruco_dict,
                                                              parameters=aruco_params)
        if ids is not None:
            if len(ids) == 4:
                # warp image and update contours when 4 markers are detected
                img = performPerspectiveWarp(img, corners)
                self.player.update(img)
                self.validImage = True
            else:
                self.validImage = False
        else:
            self.validImage = False

        img = cv2glet(img, 'BGR')
        img.blit(0, 0, 0)

        if self.lives == 0:
            self.enemies = []
            self.isGameOver = True
            self.drawGameOverScreen()
        else:
            if self.validImage:
                if self.player.sprite is not None:
                    self.player.sprite.draw()
                self.draw_enemies()
                self.drawLabels()
                self.updateGameState()
            else:
                self.notDetectedCounters += 1
                # only completely reset game when markers are not found for some time
                if self.notDetectedCounters == 300:
                    self.resetGame()
                self.drawLabels()

    # increase difficulty
    def updateGameState(self):
        if self.spawnRate > 5:
            self.spawnIncreaseTimer += 1
            if self.spawnIncreaseTimer == 60:
                self.spawnRate -= 1
                self.spawnIncreaseTimer = 0
                if self.spawnRate > 15:
                    self.difficulty = 'easy'
                    self.enemySpeed = 5
                elif self.spawnRate > 10:
                    self.difficulty = 'medium'
                    self.enemySpeed = 7
                else:
                    self.difficulty = 'hard'
                    self.enemySpeed = 10

    def drawGameOverScreen(self):
        pyglet.text.Label('YOU DIED',
                          font_name='Times New Roman',
                          font_size=36,
                          x=WINDOW_WIDTH / 2,
                          y=WINDOW_HEIGHT / 2,
                          color=(0, 0, 0, 255),
                          anchor_x='center',
                          anchor_y='center').draw()
        pyglet.text.Label(
            'Enemies felled: ' + str(self.score),
            font_name='Times New Roman',
            font_size=18,
            x=WINDOW_WIDTH / 2,
            y=WINDOW_HEIGHT / 2 - 50,
            color=(0, 0, 0, 255),
            anchor_x='center',
            anchor_y='center').draw()
        pyglet.text.Label('Press R to enter callibration Phase',
                          font_name='Times New Roman',
                          font_size=18,
                          x=WINDOW_WIDTH / 2,
                          y=WINDOW_HEIGHT / 2 - 100,
                          color=(0, 0, 0, 255),
                          anchor_x='center',
                          anchor_y='center').draw()

    def drawLabels(self):
        if not self.validImage:
            pyglet.text.Label('No Markers Detected',
                              font_name='Times New Roman',
                              font_size=36,
                              x=WINDOW_WIDTH / 2,
                              y=WINDOW_HEIGHT / 2,
                              color=(0, 0, 0, 255),
                              anchor_x='center',
                              anchor_y='center').draw()
        else:
            pyglet.text.Label('Lives: ' + str(self.lives),
                              font_name='Times New Roman',
                              font_size=18,
                              x=50, y=50,
                              color=(0, 0, 0, 255),
                              anchor_x='center',
                              anchor_y='center').draw()
            pyglet.text.Label(
                'Score: ' + str(self.score),
                font_name='Times New Roman',
                font_size=18,
                x=10, y=90,
                color=(0, 0, 0, 255),
                anchor_x='left', anchor_y='center').draw()
            pyglet.text.Label(
                self.difficulty,
                font_name='Times New Roman',
                font_size=18,
                x=10, y=130,
                color=(0, 0, 0, 255),
                anchor_x='left', anchor_y='center').draw()

    def resetGame(self):
        self.enemies = []
        self.spawnIncreaseTimer = 0
        self.spawnRate = 20
        self.score = 0
        self.lives = 3
        self.notDetectedCounters = 0
        self.isGameOver = False
        self.difficulty = 'easy'

    def update(self, delta_time):
        # update enemies
        if self.validImage:
            self.update_enemies()
            if self.player.exists:
                self.check_collision()

    # Check if Player and Enemies collide
    def check_collision(self):
        for enemy in self.enemies:
            if (enemy.x < self.player.x + self.player.width and
                    enemy.x + enemy.width > self.player.x and
                    enemy.y < self.player.y + self.player.height and
                    enemy.y + enemy.height > self.player.y):
                self.score += 1
                self.enemies.remove(enemy)

    # only create an Enemy if it doesnt overlap with existing
    def no_overlap(self, new_enemy):
        for enemy in self.enemies:
            if enemy.y + enemy.height > new_enemy.y:
                return False
        return True

    def update_enemies(self):
        for enemy in self.enemies:
            enemy.update(self.enemySpeed)
            if enemy.y < -enemy.height:
                if self.lives > 0:
                    self.lives -= 1
                self.enemies.remove(enemy)

    def create_enemy(self, delta_time):
        if not self.isGameOver:
            monsterRandomizer = random.randint(0, 10)
            if monsterRandomizer < 4:
                enemyImage = batImage
            elif monsterRandomizer < 8:
                enemyImage = goblinImage
            else:
                enemyImage = reaperImage

            if random.randint(0, self.spawnRate) == 0:
                x = random.randint(0, WINDOW_WIDTH - enemyImage.width)
                new_enemy = Enemy(x, enemyImage)
                if self.no_overlap(new_enemy):
                    self.enemies.append(Enemy(x, enemyImage))

    def draw_enemies(self):
        for enemy in self.enemies:
            enemy.draw()


game = Game()


@window.event
def on_draw():
    window.clear()
    ret, frame = cap.read()
    game.draw(frame)


@window.event
def on_key_press(symbol, modifiers):
    if symbol == pyglet.window.key.R:
        game.resetGame()
    elif symbol == pyglet.window.key.Q or symbol == pyglet.window.key.ESCAPE:
        pyglet.app.exit()


clock.schedule_interval(game.update, 0.01)
clock.schedule_interval(game.create_enemy, 0.1)

pyglet.app.run()
