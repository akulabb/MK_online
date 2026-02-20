#WING

import logging as mainlog
import socket
import threading
import time
import json
import inspect
from dataclasses import dataclass

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
PORT = 55555

FIGHT_TIME = 600
timer = FIGHT_TIME

ATTACK = 0
DEAD = 1
GO = 2
HITTED = 3
JUMP = 4
STAY = 5

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

#max_players_num = 0
#connected_players_num = 0
#alive_players_num = 0

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

def get_messaged_list(list_to_change: list, message: str) -> list:
    return list_to_change.insert(0, message)

@log_class
class Animation():
    def __init__(self, delay=5, ):#animation_path: str,):
        self.skins = []
        self.delay = delay

        #for path in os.listdir(animation_path):
        #    skin_path = os.path.join(animation_path, path)
        #    self.skins.append(self.load_skin(skin_path))
                                                                    #TODO animation_path, animation_delay
        self.skins_num = 4 #len(self.skins)



@log_class
class Character():
    def __init__(self, id: str, name: str,):
        self.id = id
        self.name = name 
        self.max_health = 100
        self.speed = 10
        self.damage = 5
        self.size = PLAYER_SIZE
        self.weapon_size = PLAYER_SIZE
        self.ATTACK_DELAY = 5
        self.HITTED_DELAY = 5
        self.animation_stay = Animation()
        self.animation_go = Animation()
        self.animation_jump = Animation()
        self.animation_attack = Animation()
        self.animation_hitted = Animation()
        self.animation_dead = Animation()
        self.attack_duration = self.animation_attack.delay * self.animation_attack.skins_num 
        

@log_class
class Player(threading.Thread):
    def __init__(self, id, socket, gravity):
        super().__init__(daemon=True)
        self.attack_delay = 0
        self.hitted_delay = 0
        self.action = STAY     
        self.id = id
        self.dir = bool(self.id % 2) or False            # True влево, False вправо
        self.health = 100
        self.socket = socket
        self.fall_speed = 0
        self.jumping = False
        self.gravity = gravity
        self.mode = READY
        self.update_timer_value = False
        self.immortal = True
        self.extra_socket = None
        self.character = None
        self.rect = None
        self.y_pos = None
        self.attack_duration = 0
   
    def add_extra_socket(self, extra_socket):
        self.extra_socket=extra_socket
        log.debug(f'added extra socket')
        
    def say(self, message):
        log.info(f'Player {self.id}: {message}')
    
    def set_start(self,):
        self.rect.update(START_POSITIONS[self.id], self.y_pos)
        self.health = self.character.max_health
        self.action = STAY
        self.mode = READY
    
    def set_character(self, character: Character):
        self.character = character
        self.y_pos = int(GROUND_LEVEL - character.size[1] / 2)
        self.rect = Rect(character.size, 
                         START_POSITIONS[self.id], 
                         self.y_pos
                        )
    
    def attack(self,):
        self.attack_duration = self.character.attack_duration
        self.attack_delay = ATTACK_DELAY+self.attack_duration
        attack_dist = self.character.weapon_size[0]
        if self.dir:
            hit_x = self.rect.center_x - attack_dist / 2
        else:
            hit_x = self.rect.center_x + attack_dist / 2
        
        hit = Rect(self.character.weapon_size,
                   hit_x,
                   self.y_pos,
                   )
        
   #     print('starting apply hitted')
        for hitted_enemy in hit.get_hitted(self.id): 
            hitted_enemy.hitted(self.character.damage)
         #   print('attack:enemy id', hitted_enemy.id)
    
    def hitted(self, damage):
#        global alive_players_num
        self.hitted_delay = HITTED_DELAY
        if self.mode == IN_GAME:
            if self.health > 0 and not self.immortal:
                self.health -= damage
                self.action = HITTED
            if self.health < 1 and self.action != DEAD:
                self.action = DEAD
#                alive_players_num -= 1
#                print(f'player: {self.id} dead, alive_players_num: {alive_players_num}')
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
                if self.attack_duration:
                    self.action = ATTACK
                    self.attack_duration -= 1
                    if not self.attack_duration:
                        self.attack_delay = ATTACK_DELAY
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
                dx += self.character.speed * options.get('move')
                self.dir = options.get('direction')

        pos_x = self.rect.center_x + dx
        pos_y = self.rect.center_y + dy
        if self.attack_delay:
            self.attack_delay -= 1
        self.rect.update(pos_x, pos_y)
        
    def get_self_state(self):
        return (self.rect.center_x, self.rect.center_y, self.health, self.action, self.dir, self.mode, self.character.id)
    
    def waiting_for_second_socket(self):
        self.say('start waiting for second socket')
        while not self.extra_socket:
            time.sleep(0.25)
    
    def watch_rings(self,):                                 #TODO игра сразу же заканчивается, проверить Player.mode в Player.run()
        self.say('watch_rings запускается')
        prev_rings_state = []
        while self.mode == READY:
            rings_state = [ring.fight for ring in rings.values()]
            if prev_rings_state != rings_state:
                prev_rings_state = rings_state
                send(rings_state, self.extra_socket)
                self.say(f'Rings state: {rings_state}')
            time.sleep(0.1)
    
    def run(self):
        self.say('Игрок создан')
        player_connected = True
        send(tuple(characters.keys()), self.socket)
        character_choice = recieve(self.socket)
        self.say(character_choice)
        self.set_character(characters[character_choice])
        self.set_start()
        start_config = (self.dir,
                        self.rect.center_x, 
                        self.rect.center_y, 
                        self.rect.width,
                        self.rect.height,
                        self.character.id,
                       )
        start_state = (self.id,
                       start_config,
                       tuple(rings.keys()),         #Это названия доступных на сервере рингов
                       )                 
        send(start_state, self.socket)
        self.waiting_for_second_socket()
        self.say(f'start state: {start_state}')
        while player_connected:
            self.set_start()
            threading.Thread(target=self.watch_rings, daemon=True).start()
            try:
                ring_number = recieve(self.socket)   #ring_number ЭТО СТРОКА
                ring = rings[ring_number]
            except Exception:
                self.say(f'Неправильный номер ринга: {ring_number}, клиент будет отключен')
                player_connected = False
                continue
            self.say(f'выбрал ринг на {ring_number}')
            ring.add_player(self)
            self.say(f'start main cycle.')
            self.mode = IN_GAME
            while True:                                                    #главный цикл игры
                options = recieve(self.socket)
                #self.mode = IN_GAME
                if options == ERROR:
                    log.error(f'Потерянно соеденение с : {self.id} игрок отключился')
               #     alive_players_num -= 1
                    player_connected = False
                    break
                self.apply_options(options)
                send(ring.get_game_state(self.id, self.update_timer_value), self.socket)
                if self.update_timer_value:
                    self.update_timer_value = False
                winners_ids = ring.game_over()
                if winners_ids:
                    winners_ids.insert(0, 'game over')
                    self.say('GAME OVER')
                    recieve(self.socket)
                    self.say('sending finish')
                    send(winners_ids, self.socket)
                    self.say('recieving finish confirmation')
                    confirm = recieve(self.socket)
                    self.say(f'confirm: {confirm}')
                    ring.remove_player(self.id, clean_winners=False)
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
    def __init__(self, players_num, playing_time=30):
        super().__init__(daemon=True)
        self.playing_time = playing_time
        self.timer = self.playing_time
        self.players_num = players_num
        self.max_players_num = 0
        self.alive_players_num = 0
        self.ring_enable = False
        self.fight = False
        self.new_player_event = ServerEvent(name="add_new_player")
        self.remove_player_event = ServerEvent(name="remove_new_player")
        self.need_to_remove_player = False
        self.reuesters_ids = []
        self.players = []
        self.winners = []
    
    def game_over(self,):
        if not self.ring_enable:
            return [winner.id for winner in self.winners]
    
    def add_player(self, player):
        self.new_player_event.activate()
        self.reuesters_ids.clear()
        self.enable()
        self.players.append(player)
        self.say(f'It is new player on our ring! His name is {player.name}')
        
    def _remove_player_from(self, id, container):
        index = None
        for player in container:
            if player.id == id:
                index = container.index(player)
        if index != None:
            container.pop(index)
        return index
            
    def remove_player(self, id: int, clean_winners=True):
        remove = False
        self.need_to_remove_player = True
        if self._remove_player_from(id, self.players) != None:
            remove = True
            self.remove_player_event.activate(id)
            self.say(f'удален игрок {id} из players')
        if clean_winners:
            if self._remove_player_from(id, self.winners) != None:
                remove = True
                self.say(f'удален игрок {id} из winners')
        return remove 
        
    def enable(self, enable=True):
        self.ring_enable = enable
    
    def waiting_for_players(self,):
        self.say('Waiting for players')
        while len(self.players) < self.players_num:
            time.sleep(0.25)
            
    def say(self, message):
        log.info(f'Говорит ринг на {self.players_num}: {message}')
    
    def enable_players_immortal(self, enable=True):
        for player in self.players:
            player.immortal = enable
    
    def get_winners(self):
        self.winners = []
        for player in self.players:
            if not player.action == DEAD:    
                self.winners.append(player)
        return self.winners
    
    def run(self,):
        self.say('Referee started!')
        while True:
            self.waiting_for_players()
            self.enable_players_immortal(False)
            self.say('Game started!')
            self.fight = True
            self.timer = self.playing_time
            alive_players = self.players_num 
            while alive_players > 1 and self.timer > 0:
                time.sleep(1)
                self.timer -= 1
                for player in self.players:
                    player.update_timer_value = True
                    if player.action == DEAD:
                        alive_players -= 1
            self.winners = self.get_winners()
            if alive_players > 1:       #время на таймере истекло
                new_winners = []
                max_health = self.winners[0].health
                for winner in self.winners:
                    if winner.health > max_health:
                        new_winners = [winner,]
                    elif winner.health == max_health:
                        new_winners.append(winner)
                self.winners = new_winners
                   # health = winner.health
            self.enable(False)
            self.enable_players_immortal()
            while self.players:
                self.say(f'Ожидание покидания игроками ринга. На ринге остались: {self.players}')
                time.sleep(1)
            self.say('Game over!')
          #  self.players.clear()
            self.fight = False
            print(f'Ring clear')
            print()
            
    def get_game_state(self, requester_id: int, update_timer=False):
        game_state = {'timer': None}
        if self.new_player_event.is_actual_for(requester_id, self.players):
            game_state = ['new players']
            for player in self.players: 
                player_config = (player.id,
                        player.dir,
                        player.rect.center_x, 
                        player.rect.center_y, 
                        player.rect.width,
                        player.rect.height,
                        player.character.id,
                       )
                game_state.append(player_config)
        elif self.remove_player_event.is_actual_for(requester_id, self.players):
            game_state = ['remove_player', self.remove_player_event.extra_data]
            print(f'Sending remove pleyer {self.remove_player_event.extra_data} package to {requester_id}')
        else:
            for player in self.players:
                game_state[player.id] = player.get_self_state()
            if update_timer:
                game_state['timer'] = self.timer
        return game_state

class ServerEvent:
    def __init__(self, name):
        self.requesters = []
        self.name = name
        self.is_active = False
        self.extra_data = None
    
    def activate(self, extra_data=None):
        self.extra_data = extra_data
        self.is_active = True
    
    def deactivate(self, ):
        self.is_active = False

    def is_actual_for(self, id, players):
        if self.is_active and not id in self.requesters:
            self.requesters.append(id)
            players_ids = [player.id for player in players]
            players_ids.sort()
            self.requesters.sort()
            if self.requesters == players_ids:
                self.deactivate()
                self.requesters.clear()
            return True


@to_log
def remove_player(id):              #TODO найти на каком ринге игрок и удалить его оттуда(если есть)
#    global connected_players_num, rings
    players[id].socket.close()
    players[id] = None
    for ring in rings.values():
        ring.remove_player(id)
    log.debug(f'игрок закончился с id : {id}')
#    connected_players_num -= 1

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


grer = Character('1', 'grer')
artom = Character('2', 'artom')

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

characters = {
    '1' : grer,
    '2' : artom,
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
#                connected_players_num += 1
                break
        else:
            print('Максимальное количество игроков')
            new_socket.close()
    elif type(socket_type) == int and socket_type >= 0:
        players[socket_type].add_extra_socket(new_socket)
    else:
        print('Неправильный тип подключения!')
            
