"""
v.0-9-7.
Библиотека easy_pygame для упрощения доступа к pygame для детей

можно создавать фон и спрайты.
Управлять движением спрайта с клавиатуры доступны 4 стрелки.
Управлять стилем вращения спрайта.
Движение и вращение спрайта реализовано через векторы. Это даёт возможность
вращать спрайт на произвольный угол и двигаться в произвольном направлении.
перемещать спрайт в произвольную точку, переворачивать по вертикали или горизонтали.
Контролировать касание спрайтов друг друга или края экрана через BORDER
Создавать надписи на экране и менять их через Label
Создавать стены через Wall

По умолчанию AUTO_UPDATE=True, то есть каждый спрайт запускает апдейт и отрисовку, когда ему
поступает какая-то команда. Спрайт должен быть на белом фоне
"""

import pygame
from pygame.math import Vector2
from time import sleep
from random import randint
from math import atan, ceil, degrees, sqrt
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
AUTO_UPDATE = True

WIDTH = 800
HEIGHT = 600
BORDER = 0
MOUSE = 10

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

UP = 0
DOWN = 180
RIGHT = 90
LEFT = 270

labels = {}
events = False
all_sprites = pygame.sprite.Group()
tmp_group = pygame.sprite.Group()
clock = pygame.time.Clock()

pygame.init()
pygame.font.init()
pygame.mixer.init()
pygame.event.get()

# функция создания окна с фоном.
def screen(background=WHITE,
           width=WIDTH,
           height=HEIGHT,
           ):
    default_screen = Screen(background=background,
                            width=width,
                            height=height,
                            )

def tick(fps):
    clock.tick(fps)
        
def close_window():
    global events 
    events = True
    for event in pygame.event.get(): # проверка закрытия окна
        if event.type == pygame.QUIT:
            pygame.quit()
            return True

def update():
    display.blit(bg, (0,0)) # отрисовка фона
    all_sprites.draw(display) # отрисовка спрайтов
    for label_id, label in labels.items():
         display.blit(label.surface, label.place)
    #pygame.display.update() # обновление всего.(можно обновлять отдельные поверхности)
    pygame.display.flip()

def pressed_key(key):
    if not events:
        pygame.event.get()
    keystate = pygame.key.get_pressed()
    if key == 'left':
        return keystate[pygame.K_LEFT]
    elif key == 'right':
        return keystate[pygame.K_RIGHT]
    elif key == 'up':
        return keystate[pygame.K_UP]
    elif key == 'down':
        return keystate[pygame.K_DOWN]
    elif key == 'space':
        return keystate[pygame.K_SPACE]
    else:
        return None


class Screen():
    def __init__(self, background=WHITE,
                 width=WIDTH,
                 height=HEIGHT,
                 caption='EasyPyGame'
                ):
        self.width = width
        self.height = height
        self.background = background
        global display
        display = pygame.display.set_mode((width, height))
        pygame.display.set_caption(caption)
        global bg
        bg = pygame.Surface((width, height))
        self.set_background(background)
        
    def set_background(self, background):
        self.background = background
        if type(background) == str:
            image = pygame.image.load(background).convert()
            image = pygame.transform.scale(image, (self.width, self.height))
            bg.blit(image, (0,0))
        else:
            bg.fill(background)
        if AUTO_UPDATE:
            update()
 
    
class Label():
    def __init__(self, text='label',
                 val='',
                 x=0,
                 y=0,
                 size=32,
                 center=False,
                 color=BLACK,
                 show=True,
                 ):
        self._id = text
        self.text = text
        self.value = val
        self.font_size = size
        self.color = color
        self.font = pygame.font.Font(None, self.font_size)
        self.surface = self._get_surf()
        self.place = (x, y)
        self.place_to((x, y), center=center)
        if show:
            labels[self._id] = self
            update()  
        
    def _get_surf(self):
        self.message = '{text}{value}'.format(text=self.text, value=self.value)
        return self.font.render(self.message, True, self.color)
        
    def set_value(self, value):
        self.value = value
        self.surface = self._get_surf()
        labels[self._id] = self
        
    def show(self):
        #print(f'Showing label{self._id}')
        labels[self._id] = self
            
    def hide(self):
        print(f'Hiding label{self._id}')
        labels.pop(self._id)
        
    def place_to(self, place, center=False):
        self.place = place
        if center:
            self.place = self.surface.get_rect(center=self.place)
            
    
class Sprite(pygame.sprite.Sprite):
    def __init__(self, img=GREEN, 
                 pos=(int(WIDTH / 2), int(HEIGHT / 2)), 
                 w=50, 
                 h=50,
                 savescale=True,
                 full_path=False,
                 show=True,
                 ):
        super().__init__()
        self.size = w, h
        self.angle = 0 # угол поворота изображения спрайта
        self.image = self.load_img(img=img,
                              savescale=savescale,
                              full_path=full_path,
                              )
        self.orig_image = self.image # оригинал чтобы не терять качество при поворотах
        self.rect = self.image.get_rect(center=pos)#, width=w * 0.7, height=h * 0.7)
        self.pos = Vector2(pos).rotate(self.angle)# вектор позиции
        self.velocity = Vector2(0, -0) #нулевой вектор смещения спрайта
        if show:
            all_sprites.add(self) # добавление себя в группу спрайтов.
        if AUTO_UPDATE:
            update()
    
    def load_img(self, img=GREEN, savescale=True, full_path=False, colorkey=WHITE):
        w, h = self.size
        if type(img) == str:
            if not full_path:
                img = os.path.join(CURRENT_DIR, img)
            image = pygame.image.load(img)
            if savescale:
                scale = w / image.get_width()
                h = int(image.get_height() * scale)
                self.size = w, h
            image = pygame.transform.scale(image, (w, h))
            image.set_colorkey(colorkey)
        else:
            image = pygame.Surface((w, h))
            image.fill(img)
        return image
    
    def move(self, direction=500, speed=0):
        if direction == 500:
            direction = self.angle
        # смещаем спрайт. Единичный вектор, повернутый в направлении спрайта
        # умножаем на скорость спрайта. Получаем вектор смещения спрайта.
        self.velocity = Vector2(0, -1).rotate(direction) * speed
        self.pos += self.velocity # получаем новый вектор позиции
        self.rect.center = self.pos # задаем новые координаты спрайта
        if AUTO_UPDATE:
            update()
        
    def move_to(self, position):
        self.pos = position
        self.rect.center = self.pos
        if AUTO_UPDATE:
            update()
                
    def rotate_to(self, target, resize=True):
        if isinstance(target, Sprite):
            to_x, to_y = target.pos
        elif target == MOUSE:
            to_x, to_y = pygame.mouse.get_pos()
        else:
            to_x = to_y = 0
        x, y = self.pos
        diff_x = x - to_x
        diff_y = y - to_y
        if diff_y == 0:
            if diff_x >= 0:
                angle = -90
            else:
                angle = 90
        else:
            angle = -degrees(atan(diff_x / diff_y))
            if diff_y <= 0:
                angle = angle - 180
        self.rotate(angle, resize)
        
    def distance_to(self, target):
        to_x, to_y = target.pos
        x, y = self.pos
        diff_x = abs(x - to_x)
        diff_y = abs(y - to_y)
        return sqrt(diff_x**2 + diff_y**2)

    def rotate(self, angle, resize=True):
        size_mod = 0.7
        # разворачиваем изображение (исходную копию)
        #self.image = pygame.transform.rotozoom(self.orig_image, -angle, 1)
        self.image = pygame.transform.rotate(self.orig_image, -angle)
        # получаем новый прямоугольник для повернутого изображения
        self.image.set_colorkey(WHITE)
        center = self.rect.center
        self.rect = self.image.get_rect(center=center)
        if resize:
            self.rect.size = tuple(size * size_mod for size in self.rect.size)
            self.rect.center = center
        self.angle = angle
        if AUTO_UPDATE:
            update()
        
    def flip(self, x=False, y=False, orig=True):
        if orig:
            self.image = pygame.transform.flip(self.orig_image, x, y)
        else:
            self.image = pygame.transform.flip(self.image, x, y)
        if AUTO_UPDATE:
            update()

    def taped(self, target, delete=False):
        hits = 0
        tmp_target = None
        if target == MOUSE:
            tmp_target = Sprite(pos=pygame.mouse.get_pos(), w=1, h=1)
            tmp_group.add(tmp_target)
        elif target == BORDER:
            if self.pos[0] < 10 or self.pos[0] > display.get_width() - 10 or\
               self.pos[1] < 10 or self.pos[1] > display.get_height() - 10:
                hits += 1
        elif isinstance(target, Sprite):
            tmp_group.add(target)    
        elif isinstance(target, Wall):
            tmp_group.add(*target.sprites)
        hits = hits or pygame.sprite.spritecollide(self, tmp_group, delete)
        tmp_group.empty()
        if tmp_target:
            tmp_target.kill()
        return hits or False
        
    def copy(self,
             img=None,
             savescale=False,
             pos=None,
             w=None,
             h=None,
             angle=None,
             ):
        new_sprite = Sprite(img=img,
                     pos=pos or self.pos,
                     w=w or self.size[0],
                     h=h or self.size[1],
                     savescale=savescale,
                     )
        new_sprite.angle = angle or self.angle
        new_sprite.rect.center = self.pos
        if not img:
            new_sprite.image = new_sprite.orig_image = self.image.copy()
        new_sprite.rect = new_sprite.image.get_rect(center=pos)
        return new_sprite
    
    def hide(self):
        all_sprites.remove(self)
        
    def show(self):
        all_sprites.add(self) 


class Wall():
    def __init__(self, stamp=RED, points=((0, 0), (10, 0),), thick=30):
        #print('creating brick')
        brick = Sprite(img=stamp,
                       savescale=False,
                       pos=points[0],
                       w=thick,
                       h=thick,
                       )
        self.sprites = [brick, ]
        previous_point = None
        for point in points:
            if previous_point:
                start_sprite = self.sprites.pop()
                end_sprite = brick.copy(pos=point)
                start_sprite.rotate_to(end_sprite, resize=False)
                end_sprite.rotate_to(start_sprite, resize=False)
                distance = start_sprite.distance_to(end_sprite)
                num_sprites_in_line = ceil(distance / thick)
                step = distance / num_sprites_in_line
                sprites_in_line = [start_sprite, ]
                for num in range(num_sprites_in_line):
                    new_sprite = start_sprite.copy(pos=previous_point)
                    sprites_in_line.append(new_sprite)
                    for move in range(num):
                        new_sprite.move(speed=step)
                self.sprites.extend(sprites_in_line)
                self.sprites.append(end_sprite)
            previous_point = point
        if AUTO_UPDATE:
            update()
    
    def remove(self):
        for block in self.sprites:
            block.kill()
                
