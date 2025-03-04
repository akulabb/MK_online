import logging as mainlog
import socket
import threading
import time
import json
import inspect

ERROR = -1

SCREEN_HEIGHT = 600
SCREEN_WIDTH = 800
GROUND_LEVEL = SCREEN_HEIGHT - 150              #716
START_POSITIONS = (int(SCREEN_WIDTH / 5), 
                   int(SCREEN_WIDTH - SCREEN_WIDTH / 5),
                   int(SCREEN_WIDTH / 5 * 2),
                   int(SCREEN_WIDTH / 5 * 3)
                   )

SERVER = 'localhost'
PORT = 5555

FIGHT_TIME = 600
timer = FIGHT_TIME
recent_time = 0

STAY = 0
GO = 1
JUMP = 2
ATTACK = 3
HITTED = 4
DEAD = 5

CONNECTED = 3 #в меню
WAITING = 2   #ждет от остальных игроков
READY = 1
IN_GAME = 0

LOGGING_LEVEL = mainlog.DEBUG
NOT_LOGGING_FUNCTION = ('apply_options', 'send_data', 'recieve', 'update', 'get_self_state', 'sub_func', 'say')

mainlog.basicConfig(level=LOGGING_LEVEL,
                format='%(levelname)s %(message)s')
log = mainlog.getLogger('log_to_file')
fhandler = mainlog.FileHandler(filename='log.txt', mode='a')
formatter = mainlog.Formatter('%(asctime)s, %(levelname)s, %(message)s, %(funcName)s, %(lineno)s, %(filename)s')

fhandler.setFormatter(formatter)
log.addHandler(fhandler)

ATTACK_DELAY = 5
HITTED_DELAY = 5

PLAYER_SIZE = (130, 130)

GRAVITY = 2

start_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
start_socket.bind((SERVER, PORT))
start_socket.listen(2)
log.info('Сервер запущен')

players = {num:None for num in range(20)}

game_started = False

max_players_num = 0
connected_players_num = 0
alive_players_num = 0

def to_log(func):
    def sub_func(*args, **kwargs):
        if not func.__name__ in NOT_LOGGING_FUNCTION:
            log.info(f"** {func.__name__} **")
        result = func(*args, **kwargs)
        return result
    return sub_func

def log_class(class_to_log, ):
    class_name = class_to_log.__name__
    for name, method in inspect.getmembers(class_to_log):
        if inspect.isfunction(method):
            setattr(class_to_log, name, to_log(method))
    return class_to_log


@log_class
class Player(threading.Thread):
    def __init__(self, id, socket, gravity):
        super().__init__(daemon=True)
        self.attack_delay = 0
        self.hitted_delay = 0
        self.action = STAY     # 0 = stay, 1 = go, 2 = jump, 3 = attack, 4 hitted, 5 = dead
        self.id = id
        self.dir = bool(self.id % 2) or False            # True влево, False вправо
        self.health = 100
        self.y_pos = int(GROUND_LEVEL - PLAYER_SIZE[1] / 2)
        self.rect = Rect(PLAYER_SIZE, 
                         START_POSITIONS[self.id], 
                         self.y_pos
                        )
        self.socket = socket
        self.fall_speed = 0
        self.jumping = False
        self.gravity = gravity
        self.mode = READY
        self.extra_socket = None
        self.update_timer_value = False
    
    def add_extra_socket(self, extra_socket):
        self.extra_socket=extra_socket
        log.debug(f'added extra socket')
        
    def say(self, message):
        log.info(f'Player {self.id}: {message}')
    
    def set_start(self,):
        self.rect.update(START_POSITIONS[self.id], self.y_pos)
        self.health = 100
        self.action = STAY
        self.mode = READY
    
    def attack(self,):
        self.attack_delay = ATTACK_DELAY
        attack_dist = self.rect.width
        if self.dir:
            hit_x = self.rect.center_x - attack_dist / 2
        else:
            hit_x = self.rect.center_x + attack_dist / 2
        
        hit = Rect(PLAYER_SIZE,
                     hit_x,
                     self.y_pos,
                     )
        
   #     print('starting apply hitted')
        for hitted_enemy in hit.get_hitted(self.id): 
            hitted_enemy.hitted()
         #   print('attack:enemy id', hitted_enemy.id)
    
    def hitted(self):
        global alive_players_num
        self.hitted_delay = HITTED_DELAY
        if self.mode == IN_GAME:
            if self.health > 0:
                self.health -= 5
                self.action = HITTED
            if self.health < 1 and self.action != DEAD:
                self.action = DEAD
                alive_players_num -= 1
                print(f'player: {self.id} dead, alive_players_num: {alive_players_num}')
    #    print('hitted:health', self.health)
    
    def apply_options(self, options):
        dx = 0
        dy = 0
        # gravitation
        self.fall_speed += self.gravity
        dy = self.fall_speed
        
        # удержание спрайта в пределах экрана
        if (self.rect.left + dx) < 0:       #левая граница экрана
            dx = -self.rect.left
        elif self.rect.right + dx > SCREEN_WIDTH:   #правая граница
            dx = SCREEN_WIDTH - self.rect.right
        if (self.rect.bottom + dy) > GROUND_LEVEL:
            dy = (GROUND_LEVEL - self.rect.bottom)
            self.fall_speed = 0
            self.jumping = False
        
        # controling
        if self.action != DEAD:
            if self.hitted_delay:
                self.action = HITTED
                self.hitted_delay -= 1
            else:
                self.action = STAY
                if options.get('move'):
                    self.action = GO
                if options.get('jump') and not self.jumping:
                    self.fall_speed = -30
                    self.jumping = True
                    self.action = JUMP
                if options.get('hit') and not self.attack_delay:
             #       print('call attack')
                    self.action = ATTACK
                    self.attack()
                dx += options.get('move')
                self.dir = options.get('direction')

        pos_x = self.rect.center_x + dx
        pos_y = self.rect.center_y + dy
        if self.attack_delay:
            self.attack_delay -= 1
        self.rect.update(pos_x, pos_y)
        
    def get_self_state(self):
        return (self.rect.center_x, self.rect.center_y, self.health, self.action, self.dir, self.mode)
    
    def waiting_for_second_socket(self):
        self.say('start waiting for second socket')
        while not self.extra_socket:
            time.sleep(0.25)
    
    def run(self):
        self.say('Игрок создан')
        player_connected = True
        while player_connected:
            self.set_start()
            #log.info(f'Player {self.id} is ready!')
            start_state = {'current_player_id' : self.id}
            start_state[id] = (self.dir,
                               self.rect.center_x, 
                               self.rect.center_y, 
                               self.rect.width,
                               self.rect.height,)
         #   global connected_players_num, alive_players_num, max_players_num, game_started, timer
          #  while connected_players_num < 2:
           #     print(connected_players_num, 'кол-во игроков')
            #    time.sleep(1)
            # for id, player in players.items():
                # if player:
                    # start_state[id] = (player.dir,
                                       # player.rect.center_x, 
                                       # player.rect.center_y, 
                                       # player.rect.width,
                                       # player.rect.height,
                                       # )
            send(start_state, self.socket)
            self.waiting_for_second_socket()
            self.say(f'start state: {start_state}')
            ring_number = recieve(self.socket)   #ring_number ЭТО СТРОКА  # TODO сделать цикл try except
            self.say(f'выбрал ринг на {ring_number}')
            ring = rings.get(ring_number)
            ring.add_player(self)
            ring.start_game()
            self.say(f'start main cycle.')
            while True:                                                    #главный цикл игры
                options = recieve(self.socket)
                self.mode = IN_GAME
                if options == ERROR:
                    log.error(f'Потерянно соеденение с : {self.id} игрок отключился')
                    alive_players_num -= 1
                    player_connected = False
                    break
                self.apply_options(options)
                send(ring.get_game_state(self.update_timer_value), self.socket)
                if self.update_timer_value:
                    self.update_timer_value = False
                if ring.game_over():
                    self.say('GAME OVER')
                    self.socket.recv(1024)
                    send('finish', self.socket)
                    break
        remove_player(self.id)

class Rect:
    def __init__(self, size, center_x, center_y, ):
        self.width, self.height = size
        self.center_x = center_x
        self.center_y = center_y
        self.update(center_x, center_y)
    
    def update(self, center_x, center_y):
        self.top = int(center_y - self.height / 2)
        self.bottom = int(center_y + self.height / 2)
        self.right = int(center_x + self.width / 2)
        self.left = int(center_x - self.width / 2)
        self.center_x = center_x
        self.center_y = center_y    
    
    def get_hitted(self, my_player_id):
        enemies = []
        for id, player in players.items():
            if player and not id == my_player_id:
                if (player.rect.right >= self.left and
                        player.rect.left <= self.right and
                        player.rect.top <= self.bottom and
                        player.rect.bottom >= self.top):
         #           print('enemys append')
                    enemies.append(player)
        return enemies


class Ring(threading.Thread):
    def __init__(self, players_num, playing_time=10):
        super().__init__(daemon=True)
        self.playing_time = playing_time
        self.timer = self.playing_time
        self.players_num = players_num
        self.max_players_num = 0
        self.alive_players_num = 0
        self.game_started = False
        self.players = []
    
    def game_over(self,):
        pass
    
    def add_player(self, player):
        self.alive_players_num += 1
        self.max_players_num += 1
        self.players.append(player)
        self.say('It is new player on our ring! His name is {player.name}')
        
    def start_game(self):
        self.game_started = True
    
    def waiting_for_players(self,):
        self.say('Waiting for players')
        while len(self.players) < self.players_num:
            time.sleep(0.25)
            
    def say(self, message):
        log.info(f'Говорит ринг на {self.players_num}: {message}')
        
    
    def run(self,):
        self.say('Referee started!')
        while True:
            self.waiting_for_players()
            self.say('Game started!')
            self.timer = self.playing_time
            while self.timer > 0:         #TODO разобраться с waiting_players
                time.sleep(1)
                self.timer -= 1
                for player in self.players:
                    player.update_timer_value = True
            self.game_started = False
            self.alive_players_num = 0
            self.max_players_num = 0
            self.say('Game over!')
            print()
            
    def get_game_state(self, update_timer=False):
        game_state = {'timer': None}
        for player in self.players:
            game_state[player.id] = player.get_self_state()
        if update_timer:
            game_state['timer'] = self.timer
            recent_time = self.timer
        return game_state


def waiting_players():
    result = True
    for player in players.values():
        if player:
            result = result and bool(player.mode)
    return result

@to_log
def remove_player(id):
    global connected_players_num
    players[id].socket.close()
    players[id] = None
    log.debug(f'игрок закончился с id : {id}')
    connected_players_num -= 1

def send(data, client_socket):
    try:
        str_data = json.dumps(data)
        byte_data = str_data.encode()
        client_socket.send(byte_data)
    except Exception as err:
        log.error(f'connection error : {err}')

def recieve(client_socket,):
    try:
        raw_data = client_socket.recv(1024)
        str_data = raw_data.decode()
        data = json.loads(str_data)
    except Exception as err:
        log.error(f'{err}')
        data = ERROR
    finally:
        return data

@to_log
def choice_waiting(player):
    send('connected', player.socket)
    ring_num = recieve(player.socket)
    log.info(f'player {player.id} chose to {ring_name}')        #TODO обработать ошибку соединения
    if ring_name in ring.keys():
        rings(ring_name).add_player(player)



ring2 = Ring(2)
ring3 = Ring(3)
ring4 = Ring(4)

ring2.start()
ring3.start()
ring4.start()
#создать объект ринга и админа

rings = {'2' : ring2,
         '3' : ring3,
         '4' : ring4,
        }

while True:
    new_socket, adress = start_socket.accept()
    socket_type = recieve(new_socket)
    log.info(f'Новое подключение с адресом : {adress}, тип подключения {socket_type}')
    if socket_type == 'main':
        for id, player_in_slot in players.items():
            if not player_in_slot:
                player = Player(id, new_socket, GRAVITY)
                player.start()
                players[id] = player
                connected_players_num += 1
                break
        else:
            print('Максимальное количество игроков')
            new_socket.close()
    elif type(socket_type) == int and socket_type >= 0:
        players[socket_type].add_extra_socket(new_socket)
    else:
        print('Неправильный тип подключения!')
            