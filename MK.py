from sys import implementation
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
EARTH_IMAGE_PATH = os.path.join('photos', 'earth', 'earth.png')
BACK_IMAGE_PATH = os.path.join('photos', 'background', 'back_1.png')
WAITING_BACK_IMAGE_PATH = os.path.join('photos', 'background', 'back_2.png')

HEIGHT_HALF = int(SCREEN_HEIGHT/2)
WIDTH_HALF = int(SCREEN_WIDTH/2)
epg.AUTO_UPDATE = False

GRAVITY = 2
#EARTH = 716MAX

PROJECT_DIR = os.getcwd()
#GRER_IMAGE_PATHES = (os.path.join(PROJECT_DIR, 'photos/grer/stay_1.png'),
 #                       os.path.join(PROJECT_DIR, 'photos/grer/go.png'),
  #                      os.path.join(PROJECT_DIR, 'photos/grer/jump.png'),
   #                     os.path.join(PROJECT_DIR, 'photos/grer/attack.png'),
    #                    os.path.join(PROJECT_DIR, 'photos/grer/hitted.png'),
     #                   os.path.join(PROJECT_DIR, 'photos/grer/dead.png'),
      #                  )


#ARTOM_IMAGE_PATHES = (os.path.join(PROJECT_DIR, 'photos/artom/stay_artom.png'),
 #                       os.path.join(PROJECT_DIR, 'photos/artom/go_artom.png'),
  #                      os.path.join(PROJECT_DIR, 'photos/artom/jump_artom.png'),
   #                     os.path.join(PROJECT_DIR, 'photos/artom/attack_artom.png'),
    #                    os.path.join(PROJECT_DIR, 'photos/artom/hitted_artom.png'),
     #                   os.path.join(PROJECT_DIR, 'photos/artom/dead_artom.png'),
      #                  )

BUTTON_RELEASED_IMAGE_PATH = os.path.join('photos', 'button', 'released.jpeg')
BUTTON_PRESSED_IMAGE_PATH = os.path.join('photos', 'button', 'pressed.jpeg')
BUTTON_DISABLED_IMAGE_PATH = os.path.join('photos', 'button', 'disabled.jpeg')

SERVER = 'localhost'
PORT = 55555

characters = {
    '1' : {
        'name' : 'grer',
        'size' : (100, 100),
        'anims_delay' : {'attack' : 5, 'dead' : 5, 'go' : 1, 'hitted' : 5,'jump' : 5 , 'stay' : 3}
        },
    '2' : {
        'name' : 'artom',
        'size' : (150, 150),
        'anims_delay' : {'attack' : 5, 'dead' : 5, 'go' : 3,'hitted' : 5 ,'jump' : 5 , 'stay' : 3}
        },
}

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
                        
    def get_choice (self, labels=[], update_buttons_enabled=True):
        choice = ''
        self.screen.set_background(self.background_path)
        if labels:
            label_y = SCREEN_HEIGHT / (len(labels) + 1)
            label_height = label_y
            for label in labels:
                label.place_to((WIDTH_HALF, label_y), center=True)
                label.show()
                label_y += label_height
        for button in self.buttons:
            button.show()
        self.active = True
        if update_buttons_enabled:
            threading.Thread(target=self.update_buttons_state, args=(), daemon=True).start()
        while self.active:
            update()
            for button in self.buttons:
                if button.get_pressed():
                    choice = button.extra_data
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
    
    def add_buttons(self, button_titles, buttons_extra_data=[], hide=False):
        for i in range(len(button_titles) - len(buttons_extra_data)):
            buttons_extra_data.append(None)

        for title, extra_data in zip(button_titles, buttons_extra_data):
            for button in self.buttons:
                new_x_pos = button.pos[0] + self.button_size[0] + self.button_margin
                button.move_to((new_x_pos, self.button_y))
            button_pos = (self.button_x, self.button_y)
            button = Button(self.button_img_paths, 
                                       title,
                                       button_pos,
                                       w=self.button_size[0],
                                       h=self.button_size[1],
                                       extra_data=extra_data,
                                       hide=hide,
                                       )
            self.buttons.insert(0, button)
    
    def remove_button(self, button_name):
        button_index = None
        for index, button in enumerate(self.buttons):
            if button.text == button_name:
                button_index = index
                break
        self.buttons.pop(button_index)
    

#@log_class
class Button(epg.Sprite, epg.Label):
    RELEASED = 0
    PRESSED = 1
    DISABLED = 2
    def __init__(self, button_image_paths, text, pos, w=50, h=50, savescale=False, extra_data=None, hide=False):
        epg.Sprite.__init__(self, button_image_paths[0], pos, w=w, h=h, savescale=savescale)
        epg.Label.__init__(self, text=text, x=pos[0], y=pos[1], center=True)
        self.skin_index = self.RELEASED
        self.animation_list = []
        self.animation_list.append(self.load_img(img=button_image_paths[self.RELEASED]))
        self.animation_list.append(self.load_img(img=button_image_paths[self.PRESSED]))
        self.animation_list.append(self.load_img(img=button_image_paths[self.DISABLED]))
        self.extra_data = extra_data or text
        print(extra_data, self.extra_data, text, "extra data")
        if hide:
            self.hide()

    
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

current_fighter = None
current_fighter_id = 0
rings = {}
current_fighter_config = ()

ground_level = SCREEN_HEIGHT - 254

@to_log
def connect():
    disconnect = True
    while disconnect:
        try:
            server.connect_main_socket()
            disconnect = False
        except ConnectionRefusedError:
            log.error('connection failed')
            time.sleep(1)
        update()

def sync_characters():
    char_ids = server.recv()
    character_names = [characters[id].get('name') for id in char_ids]
    character_menu.add_buttons(character_names, char_ids)

def initialize(char_id):
    global current_fighter_id, rings, current_fighter_config
    if char_id == 'exit':
        return
    server.send(char_id)
    start_game_state = server.get_start()
    print(f'start game state:{start_game_state}')
    current_fighter_id, current_fighter_config, rings = start_game_state
   # server.add_extra_socket(current_fighter_id)
    server.connect_extra_socket(current_fighter_id)
    button_names = [f'Ринг на {ring}' for ring in rings]
    button_names.reverse()
    main_menu.add_buttons(button_names)
    create_fighters({current_fighter_id: current_fighter_config}, show=False, current=True)
    current_fighter.change_character(characters[char_id])
    pygame.display.set_caption(str(current_fighter.id))
    
@to_log
def start_game():
    pass

def get_str_time(int_time):
    seconds = int_time % 60
    minutes = int_time // 60
    str_time = f'{minutes} : {seconds}'
    return str_time

@to_log
def create_fighters(game_state, show=True, current=False):
    global fighters, current_fighter
#    fighters = []
    for id, fighter_config in game_state.items():
        print(f'fighter {id} created')
        dir, x_pos, y_pos, wigth, height, char_id = fighter_config
        fighter = Fighter(character=characters[char_id],
                         x_pos=x_pos,
                         y_pos=y_pos,
                         flip=dir,
                         wigth=wigth, 
                         height=height,
                         ground_level=ground_level,
                         gravity=GRAVITY,
                         id=int(id),
                         show=show,
                        )
        if current:
            current_fighter = fighter
        fighters.append(fighter)
 #   return fighters
 
@to_log
def fight():
    screen.set_background(EARTH_IMAGE_PATH)
    label_timer.show()
    current_fighter.show()
    print('файтеры', len(fighters))
    
    while True:
        game_state = {}
        options = current_fighter.check_options()
        game_state = server.get_game_state(options)
        #print(f'GAME STATE:{game_state}')
        if type(game_state) == list:
            
            #конец игры
            if game_state[0] == 'game over':    
                print('ОКОНЧАНИЕ РАУНДА...')
                print(f'winners: {game_state}')
                print(fighters, 'game_over')
                server.send('end')
                for fighter in fighters:
                    print(f'Hiding fighter {fighter.id}')
                    fighter.hide()
                print('Раунд окончен.')
                return game_state
            
            #добавление игроков
            elif game_state[0] == 'new players':
                game_state.pop(0)
                new_players = {fighter_config.pop(0) : fighter_config for fighter_config in game_state}
                fighters_ids = [fighter.id for fighter in fighters]
                for fighter_id in fighters_ids:
                    if fighter_id in new_players.keys():
                        new_players.pop(fighter_id)
                create_fighters(new_players)
                update()
                continue
            
            #удаление вышедших игроков
            elif game_state[0] == 'remove_player':
                print('REMOVE PLAYER _______')
                id_to_remove = game_state[1]
                index = None
                for fighter in fighters:
                    if fighter.id == id_to_remove:
                        index = fighters.index(fighter)
                        fighter.hide()
                if index != None:
                    fighters.pop(index)
                print(f'deleted fighter {id_to_remove}')
                continue
        
        #отрисовка нового состояния игры
        for fighter in fighters:        
            fighter_state = game_state.get(str(fighter.id))
            #print('FIGHTER STATE', fighter_state)
            if not fighter_state:
                #print('Потеряно соеденение. fighter_state отсутствует.')
                #print(f'game_state: {game_state}')
                continue
            fighter.apply_game_state(fighter_state)
        
        #обновление таймера
        timer = game_state.pop('timer')
        if not timer == None:       
            label_timer.set_value(get_str_time(timer))
        #log.info(f'Timer:{timer}')
        
        
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
    
main_menu = Menu(screen,
            server,
            BACK_IMAGE_PATH, 
            ('characters', 'выйти',),
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

character_menu = Menu(
    screen,
    server,
    BACK_IMAGE_PATH,
    ('exit',),
    (BUTTON_RELEASED_IMAGE_PATH, BUTTON_PRESSED_IMAGE_PATH, BUTTON_DISABLED_IMAGE_PATH),
    (90, 90),
    button_order='h',
    button_margin=70
)

connect()
sync_characters()
character_id = character_menu.get_choice(update_buttons_enabled=False)
print("CHAR_ID : ", character_id)
initialize(character_id)     #TODO перезапуск инициализации при потере подключения

character_menu.remove_button('exit')

while character_id != 'exit' or choice == 'выйти': # server.connected: TODO крутить цикл пока клиент подключен
    print(f'start menu')
    choice = main_menu.get_choice()
    
    if choice == 'characters':
        character_id = character_menu.get_choice(update_buttons_enabled=False)
        current_fighter.change_character(characters[character_id])


    else:
        ring_num = choice[-1]
        server.send(ring_num)
        winners = fight()
        fighters = [current_fighter]
        label_game_over.show()
        update()
        time.sleep(5)
        label_game_over.hide()
#TODO закрыть сокеты перед завершением программы
exit()  
