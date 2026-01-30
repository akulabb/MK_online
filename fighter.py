import easy_pygame as epg
from easy_pygame import UP, DOWN, BORDER
import pygame
import inspect
import logging as mainlog



SCREEN_HEIGHT = 600
SCREEN_WIDTH = 800
RIGHT = False
LEFT = True
BEST_COLORKEY = (43, 205, 27)

HEALTHBAR_OFFSET = int(SCREEN_WIDTH / 7)

SIDE_HEALTHBARS_DISTANCE = SCREEN_WIDTH - 2*HEALTHBAR_OFFSET

HEALTHBAR_POSITIONS = (HEALTHBAR_OFFSET, 
                       SCREEN_WIDTH - HEALTHBAR_OFFSET,
                       SIDE_HEALTHBARS_DISTANCE / 3 + HEALTHBAR_OFFSET,
                       (SIDE_HEALTHBARS_DISTANCE / 3) * 2 + HEALTHBAR_OFFSET,
                    )

STAY = 0
GO = 1
JUMP = 2
ATTACK = 3
HITTED = 4
DEAD = 5

LOGGING_LEVEL = mainlog.DEBUG
NOT_LOGGING_FUNCTION = ('sub_func',)

mainlog.basicConfig(level=LOGGING_LEVEL,
                format='%(levelname)s %(message)s')
log = mainlog.getLogger('log_to_file')
fhandler = mainlog.FileHandler(filename='log_client.txt', mode='a')
formatter = mainlog.Formatter('%(asctime)s, %(levelname)s, %(message)s, %(funcName)s, %(lineno)s, %(filename)s')

fhandler.setFormatter(formatter)
log.addHandler(fhandler)

def to_log(func):
    def sub_func(*args, **kwargs):
        if not func.__name__ in NOT_LOGGING_FUNCTION:
            #log.info(f"** {func.__name__} **")
            pass
        result = func(*args, **kwargs)
        return result
    return sub_func

def log_class(class_to_log):
    class_name = class_to_log.__name__
    for name, method in inspect.getmembers(class_to_log):
        if inspect.isfunction(method):
            setattr(class_to_log, name, to_log(method))
    return class_to_log


class Animations:
    def __init__(self, animation_path: str, size: tuple, colorkey=BEST_COLORKEY):
        self.skins = []
        self.size = size
        self.colorkey = colorkey
        for path in os.listdir(animation_path):
            skin_path = os.pathjoin((animation_path, path))
            self.skins.append(load_skin(skin_path))
    
    def load_skin(self, skin_path):
        skin = pygame.image.load(skin_path)
        skin = pygame.transform.scale(skin, self.size)
        skin.set_colorkey(self.colorkey)
        return skin


@log_class
class Fighter(epg.Sprite):
    def __init__(self, animation_pathes, x_pos, y_pos, flip, wigth, height, ground_level, gravity, id, img=epg.GREEN, show=True):
        pos = (x_pos, y_pos)
        super().__init__(img=animation_pathes[0], pos=pos, w=wigth, h=height, savescale=False, show=show)
        self.gravity = gravity
        self.fall_speed = 0
        self.ground_level = ground_level
        self.knife = None
        self.direction = flip
        self.enemy = None
        self.id = id
        health_bar_width = epg.WIDTH / 4 - 20
        health_bar_x = int(HEALTHBAR_POSITIONS[id] - health_bar_width / 2)
        self.health_bar = HealthBar(id=self.id, health=100, pos=(health_bar_x, 10), width=health_bar_width, show=show)
        self.skin_index = 0
        self.animation_list = []
        self.change_animation_list(animation_pathes)
        self.stay()
        self.actions = (self.stay,
                        self.go,
                        self.jump,
                        self.attack,
                        self.hitted,
                        self.dead
                       )
        # 0 = stay, 1 = go, 2 = jump, 3 = attack, 4 = hitted, 5 = dead
    
    

    def check_options(self, ):
        #print('START skins_dir : ', self.skins_dir)
        options = {'move' : 0,
                   'direction' : self.skins_dir,
                   'jump' : False,
                   'hit' : False,
                    }
                    
        keystate = pygame.key.get_pressed()
                    
        if keystate[pygame.K_a]:
            #print('Key pressed A')
            options['direction'] = LEFT             #True
            options['move'] = -1
        if keystate[pygame.K_d]:
            #print('Key pressed D')
            options['direction'] = RIGHT            #False
            options['move'] = 1
        if keystate[pygame.K_SPACE]:
            options['jump'] = True
        if keystate[pygame.K_e]:
            options['hit'] = True
        #print('options dir : ', options['direction'], 'skins_dir : ', self.skins_dir)
        return options

        
    def update_health(self, health):
        self.health_bar.set_value(self.health_bar.value + health)    
        
    def stay(self,):
        self.set_skin(STAY)
        
    def go(self,):
        self.set_skin(GO)
        
    def jump(self,):
        self.set_skin(JUMP)
        
    def attack(self, ):
        self.set_skin(ATTACK)
        
    def hitted(self,):
        self.set_skin(HITTED)
    
    def dead(self,):
        self.set_skin(DEAD)
    
    def apply_game_state(self, state):
        x_pos, y_pos, health, action, self.direction, hide, char_id = state
        #print(f"Apply game state\nDirection : {self.direction}, Self skins dir : {self.skins_dir}")
        self.move_to((x_pos, y_pos))
        self.health_bar.set_value(health)
        self.actions[action]()
        if hide:
            self.hide()
        else:
            self.show()
    
    def set_skin(self, skin_index):
        if self.skins_dir != self.direction:
            #print(f'Self skins dir changed from {self.skins_dir} to {self.direction}')
            for index, skin in enumerate(self.animation_list):
                self.animation_list[index] = pygame.transform.flip(skin, flip_x=True, flip_y=False)             #TODO посмотреть как работает flip и доделать разворот картинки
            self.skins_dir = self.direction
            #print(f"self Skins DIR: {self.skins_dir}")
        self.image = self.orig_image = self.animation_list[skin_index]
        self.skin_index = skin_index
    
    def change_animation_list(self, new_animation_list):
        self.animation_list = []
        self.skins_dir = False
        for path in new_animation_list:
            self.animation_list.append(self.load_img(img=path, colorkey=(43, 205, 27)))
        self.set_skin(STAY)
        
    def hide(self,):
        super().hide()
        self.health_bar.hide()
        #print('HIDE')
    
    def show(self,):
        super().show()
        self.health_bar.show()
        #print('SHOW')
        
    def __repr__(self,):
        return f'Fighter {self.id}'


@log_class
class HealthBar(epg.Label):
    HEIGHT = 40
    def __init__(self, id, pos, width, health=100, show=True):
        self.width = width
        x, y = pos
        super().__init__(text=id, x=x, y=y, val=health, show=show)
        
    
    def _get_surf(self, ):
        raito = self.width/100
        surface = pygame.Surface((self.width+4, self.HEIGHT+4))
        pygame.draw.rect(surface, epg.BLACK, (0, 0, self.width, self.HEIGHT))
        pygame.draw.rect(surface, epg.RED, (2, 2, self.width, self.HEIGHT))
        pygame.draw.rect(surface, epg.YELLOW, (2, 2, self.value * raito, self.HEIGHT))
        return surface
    
