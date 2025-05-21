import easy_pygame as epg
from easy_pygame import UP, DOWN, LEFT, RIGHT
import pygame as pg
from fighter import *
import connection
import os
import time
import threading
import inspect
import logging as mainlog

epg.AUTO_UPDATE = False
SCREEN_HEIGHT = epg.HEIGHT = 600
SCREEN_WIDTH = epg.WIDTH = 800
SPRITE_WIDTH = 130
SPRITE_HEIGHT = 130

FPS = 30
BALL_IMAGE_PATH = 'photos/ball.png'
EARTH_IMAGE_PATH = 'photos/earth.png'
BACK_IMAGE_PATH = 'photos/back.png'
WAITING_BACK_IMAGE_PATH = 'photos/back2.png'

HEIGHT_HALF = int(SCREEN_HEIGHT/2)
WIDTH_HALF = int(SCREEN_WIDTH/2)
epg.AUTO_UPDATE = False

GRAVITY = 2
#EARTH = 716

PROJECT_DIR = os.getcwd()
FIGHTER_IMAGE_PATHES = (os.path.join(PROJECT_DIR, 'photos\\stay.png'),
                        os.path.join(PROJECT_DIR, 'photos\\go.png'),
                        os.path.join(PROJECT_DIR, 'photos\\jump.png'),
                        os.path.join(PROJECT_DIR, 'photos\\attack.png'),
                        os.path.join(PROJECT_DIR, 'photos\\hitted.png'),
                        os.path.join(PROJECT_DIR, 'photos\\dead.png'),
                        )

BUTTON_RELEASED_IMAGE_PATH = 'photos/released.jpeg'
BUTTON_PRESSED_IMAGE_PATH = 'photos/pressed.jpeg'
BUTTON_DISABLED_IMAGE_PATH = 'photos/disabled.jpeg'

SERVER = 'localhost'
PORT = 5555


#@log_class
class Menu():
    def __init__(self, screen,
                 server,
                 menu_background_img_path, 
                 button_titles, 
                 button_img_paths, 
                 button_size, 
                 button_order='v', 
                 button_margin=100,
                ):
        self.background_path = menu_background_img_path
        self.screen = screen
        self.server = server
        self.button_margin = button_margin
        self.button_img_paths = button_img_paths
        self.button_size = button_size
        self.button_order = button_order
        self.active = False
        if self.button_order == 'v':
            self.button_x = int(SCREEN_WIDTH / 2)
            self.button_y = self.button_margin + int(button_size[1] / 2)
        else:
            self.button_x = self.button_margin + int(button_size[0] / 2)
            self.button_y = int(SCREEN_HEIGHT / 2)
        self.buttons = []
        self.add_buttons(button_titles)
        for button in self.buttons:
            button.hide()
                        
    def get_choice (self, labels=[]):
        choice = ''
        self.screen.set_background(self.background_path)
        if labels:
            label_y = SCREEN_HEIGHT / (len(labels) + 1)
            label_height = label_y
            for label in labels:
                label.place_to((CENTER_X, label_y), center=True)
                label.show()
                label_y += label_height
        for button in self.buttons:
            button.show()
        self.active = True
        threading.Thread(target=self.update_buttons_state, args=(), daemon=True).start()
        while self.active:
            update()
            for button in self.buttons:
                if button.get_pressed():
                    choice = button.text
                    update()
                    time.sleep(0.5)
                    self.active = False
                    button.set_skin(button.RELEASED)
        for button in self.buttons:
            button.hide()
        for label in labels:
            label.hide()
        return choice
        
    def update_buttons_state(self,):
        print(f'started update_buttons_state')
        while self.active:
            rings_state = self.server.recv(self.server.extra_socket)
            print(f'got new buttons state: {rings_state}')
            for button, ring_state in zip(self.buttons, rings_state):
                button_state = not ring_state
                button.enable(button_state)
    
    def add_buttons(self, button_titles):
        for title in button_titles:
            for button in self.buttons:
                new_x_pos = button.pos[0] + self.button_size[0] + self.button_margin
                button.move_to((new_x_pos, self.button_y))
            button_pos = (self.button_x, self.button_y)
            button = Button(self.button_img_paths, 
                                       title,
                                       button_pos,
                                       w=self.button_size[0],
                                       h=self.button_size[1],
                                       )
            self.buttons.insert(0, button)
    

#@log_class
class Button(epg.Sprite, epg.Label):
    RELEASED = 0
    PRESSED = 1
    DISABLED = 2
    def __init__(self, button_image_paths, text, pos, w=50, h=50, savescale=False):
        epg.Sprite.__init__(self, button_image_paths[0], pos, w=w, h=h, savescale=savescale)
        epg.Label.__init__(self, text=text, x=pos[0], y=pos[1], center=True)
        self.skin_index = self.RELEASED
        self.animation_list = []
        self.animation_list.append(self.load_img(img=button_image_paths[self.RELEASED]))
        self.animation_list.append(self.load_img(img=button_image_paths[self.PRESSED]))
        self.animation_list.append(self.load_img(img=button_image_paths[self.DISABLED]))

    
    def set_skin(self, skin_index):
        self.image = self.orig_image = self.animation_list[skin_index]
        self.skin_index = skin_index
    
    def get_pressed(self,):
        if not self.skin_index == self.DISABLED:
            if self.taped(epg.MOUSE) and pg.mouse.get_pressed()[0]:
                self.set_skin(self.PRESSED)
                return True
     #   else:
      #      self.set_skin(self.RELEASED)
      #      return False
    
    def move_to(self, pos):
        epg.Sprite.move_to(self, pos)
        epg.Label.place_to(self, pos, center=True)
    
    def hide(self):
        epg.Sprite.hide(self)
        epg.Label.hide(self)
        print(f'In Button. Hiding: {self}')
    
    def show(self):
        epg.Sprite.show(self)
        epg.Label.show(self)
        print(f'In Button. Showing: {self}')
        
    def enable(self, enable=True):
        if enable:
            self.set_skin(self.RELEASED)
        else:
            self.set_skin(self.DISABLED)


def update():
    epg.update()
    if epg.close_window():
        exit()
    epg.tick(FPS)
    

screen = epg.Screen(WAITING_BACK_IMAGE_PATH, width=SCREEN_WIDTH, height=SCREEN_HEIGHT)

server = connection.Connection(SERVER, PORT)

fighters = []

current_fighter_id = 0
rings = {}
current_fighter_config = ()

ground_level = SCREEN_HEIGHT - 254

@to_log
def initialize():
    global current_fighter_id, rings, current_fighter_config, server
    disconnect = True
    while disconnect:
        try:
            server.connect_main_socket()
            disconnect = False
        except ConnectionRefusedError:
            log.error('connection failed')
            time.sleep(1)
        update()
    start_game_state = server.get_start()
    print(f'start game state:{start_game_state}')
    current_fighter_id, current_fighter_config, rings = start_game_state
   # server.add_extra_socket(current_fighter_id)
    server.connect_extra_socket(current_fighter_id)
    button_names = [f'Ринг на {ring}' for ring in rings]
    button_names.reverse()
    menu.add_buttons(button_names)
    create_fighters({current_fighter_id: current_fighter_config}, show=False)
    
@to_log
def start_game():
    pass

def get_str_time(int_time):
    seconds = int_time % 60
    minutes = int_time // 60
    str_time = f'{minutes} : {seconds}'
    return str_time

@to_log
def create_fighters(game_state, show=True):
    global fighters
#    fighters = []
    for id, player_pos in game_state.items():
        print(f'fighter {id} created')
        dir, x_pos, y_pos, wigth, height = player_pos
        fighters.append(Fighter(animation_pathes=FIGHTER_IMAGE_PATHES,
                        x_pos=x_pos,
                        y_pos=y_pos,
                        flip=dir,
                        wigth=wigth, 
                        height=height,
                        ground_level=ground_level,
                        gravity=GRAVITY,
                        id=int(id),
                        show=show,
                        ))
 #   return fighters
@to_log
def fight():
    screen.set_background(EARTH_IMAGE_PATH)
    label_timer.show()
    print('файтеры', len(fighters))
    while True:
        game_state = {}
        print(fighters)
        for fighter in fighters:
            if fighter.id == current_fighter_id:
                options = fighter.check_options()
                game_state = server.get_game_state(options)
        print(f'GAME STATE:{game_state}')
        if game_state == 'finish':
            print('ОКОНЧАНИЕ РАУНДА...')
            print(fighters)
            for fighter in fighters:
                print(f'Hiding fighter {fighter.id}')
                fighter.hide()
            print('Раунд окончен.')
            return None
        print(fighters)
        for fighter in fighters:        #отрисовка нового состояния игры
            fighter_state = game_state.get(str(fighter.id))
            print('FIGHTER STATE', fighter_state)
            if not fighter_state:
                print('Потеряно соеденение. fighter_state отсутствует.')
                print(f'game_state: {game_state}')
                continue
            fighter.apply_game_state(fighter_state)
        timer = game_state.pop('timer')
        if not timer == None:       #обновление таймера
            label_timer.set_value(get_str_time(timer))
        log.info(f'Timer:{timer}')
        if len(game_state) > len(fighters):     #добавление новых игроков
            print('new fighters on server')
            new_fighters = {}
            print(fighters)
            for fighter_id in game_state.keys():
                if not fighter_id in tuple(str(fighter.id) for fighter in fighters):
                    print(f'not found id {fighter_id} in local ides')
                    new_fighter_state = game_state.get(fighter_id)
                    new_fighter_state = (new_fighter_state[4],
                                         new_fighter_state[0],
                                         new_fighter_state[1],
                                         SPRITE_WIDTH,
                                         SPRITE_HEIGHT,
                                        )
                    print('new_fighter_state:', new_fighter_state)
                    new_fighters[fighter_id] = new_fighter_state
            create_fighters(new_fighters)
        elif len(game_state) < len(fighters):       #удаление вышедших игроков
            index = None
            for fighter in fighters:
                if not fighter.id in game_state.keys():
                    index = fighters.index(fighter)
            if index != None:
                fighters.pop(index)
        update()
    label_timer.hide()
    print('end')
    
label_game_over = epg.Label(text='GAME OVER',
                        x=WIDTH_HALF,
                        y=HEIGHT_HALF,
                        size=50,
                        center=True,
                        show=False,
                        )
    
label_timer = epg.Label(text='',
                        val=0,
                        x=WIDTH_HALF,
                        y=100,
                        center=True,
                        size=50,
                        show=False,
                        )
    
menu = Menu(screen,
            server,
            BACK_IMAGE_PATH, 
            ('выйти',),
            (BUTTON_RELEASED_IMAGE_PATH, BUTTON_PRESSED_IMAGE_PATH, BUTTON_DISABLED_IMAGE_PATH),
            (90, 90),
            button_order='h',
            button_margin=70,
            )

waiting_menu = Menu(screen,
                    server,
                    WAITING_BACK_IMAGE_PATH, 
                    ('выйти',),
                    (BUTTON_RELEASED_IMAGE_PATH, BUTTON_PRESSED_IMAGE_PATH, BUTTON_DISABLED_IMAGE_PATH),
                    (90, 90),
                    button_order='h',
                    button_margin=70,
                   )

initialize()     #TODO перезапуск инициализации при потере подключения

while True: # server.connected: TODO крутить цикл пока клиент подключен
    #threading.Thread(target=start_game).start()
    
    print(f'start menu')
    choice = menu.get_choice()

    if choice == 'выйти':
        break

    else:
        ring_num = choice[-1]
        server.send(ring_num)
        fight()                 #TODO fight() должен возвращать результат игры
        fighters = []           #TODO не удалять текущего файтера
        label_game_over.show()
        update()
        time.sleep(5)
        label_game_over.hide()
#TODO закрыть сокеты перед завершением программы
exit()
