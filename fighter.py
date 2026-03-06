import easy_pygame as epg
from easy_pygame import UP, DOWN, BORDER
import pygame
import inspect
import logging as mainlog
import os



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

ATTACK = 0
DEAD = 1
GO = 2
HITTED = 3
JUMP = 4
STAY = 5

LOGGING_LEVEL = mainlog.DEBUG
NOT_LOGGING_FUNCTION = ('sub_func', 'stay', 'go', 'jump', 'attack', 'hitted', "dead")

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


class Animation:
    def __init__(self, animation_path: str, size: tuple, skin_delay: int, colorkey=BEST_COLORKEY, direction=RIGHT):
        self.skins = []
        self.size = size
        self.colorkey = colorkey
        self.current_skin_index = 0
        self.skin_delay = skin_delay
        self.frame_counter = 0
        self.direction = direction

        for path in os.listdir(animation_path):
            skin_path = os.path.join(animation_path, path)
            self.skins.append(self.load_skin(skin_path))
        self.skins_num = len(self.skins)
    
    def load_skin(self, skin_path):
        skin = pygame.image.load(skin_path)
        skin = pygame.transform.scale(skin, self.size)
        skin.set_colorkey(self.colorkey)
        return skin

    def flip_skins(self,):
        flipped_skins = []
        for skin in self.skins:
            flipped_skins.append(pygame.transform.flip(skin, flip_x=True, flip_y=False))
        self.skins = flipped_skins
        self.direction = not self.direction
    
    def get_next_skin(self, first_skin=False):
        if first_skin:
            self.frame_counter = 0
            self.current_skin_index = 0
            return self.skins[0]
        if self.frame_counter >= self.skin_delay:
            self.current_skin_index = (self.current_skin_index+1) % self.skins_num
            skin = self.skins[self.current_skin_index]
            self.frame_counter = 0
            return skin

        self.frame_counter +=1
        

#@log_class
class Fighter(epg.Sprite):
    def __init__(self, character, x_pos, y_pos, flip, wigth, height, ground_level, gravity, id, img=epg.GREEN, show=True):
        self.actions = (self.attack,
                        self.dead,
                        self.go,
                        self.hitted,
                        self.jump,
                        self.stay,
                       )
        # 0 = stay, 1 = go, 2 = jump, 3 = attack, 4 = hitted, 5 = dead
        pos = (x_pos, y_pos)
        super().__init__(pos=pos, w=wigth, h=height, savescale=False, show=show)
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
        self.action_index = STAY
        self.animation_list = []
        self.change_character(character)
        self.stay()
    
    

    def check_options(self, ):
        #print('START skins_dir : ', self.skins_dir)
        options = {'move' : 0,
                   'direction' : self.animation_list[self.action_index].direction,
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
        self.set_animation(STAY)
        
    def go(self,):
        self.set_animation(GO)
        
    def jump(self,):
        self.set_animation(JUMP)
        
    def attack(self, ):
        self.set_animation(ATTACK)
        
    def hitted(self,):
        self.set_animation(HITTED)
    
    def dead(self,):
        self.set_animation(DEAD)
    
    def apply_game_state(self, state):
        x_pos, y_pos, health, action, self.direction, hide, char_id = state
        #print(f"Apply game state\nDirection : {self.direction}, Self skins dir : {self.skins_dir}")
        self.move_to((x_pos, y_pos))
        self.health_bar.set_value(health)

        first_skin = (self.action_index != action)
        next_skin = self.animation_list[self.action_index].get_next_skin(first_skin=first_skin)

        if next_skin:
            self.image = self.orig_image = next_skin 
        self.actions[action]()
        if hide:
            self.hide()
        else:
            self.show()
    
    def set_animation(self, action_index: int):
        animation = self.animation_list[action_index]
        if animation.direction != self.direction:
            animation.flip_skins()
        #self.image = self.orig_image = self.animation_list[action_index].get_next_skin()
        self.action_index = action_index
    
    def change_character(self, character: dict):
        self.animation_list = []
        char_path = os.path.join('photos', character.get('name'))
        for anim_name, anim_delay in character.get('anims_delay').items():
            action_path = os.path.join(char_path, anim_name)
            animation = Animation(action_path, character.get('size'), skin_delay=anim_delay, direction=RIGHT)
            self.animation_list.append(animation)
        #for path in new_animation_list:
        #    self.animation_list.append(self.load_img(img=path, colorkey=(43, 205, 27)))
        #self.set_skin(STAY)
        
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
    
