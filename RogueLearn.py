
import colors
import tdl
from random import randint

#actual size of the window
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
 
#size of the map
MAP_WIDTH = 80
MAP_HEIGHT = 45
 
#parameters for dungeon generator
ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30


FOV_ALGO = 'BASIC'
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 10

MAX_ROOM_MONSTERS = 3

REALTIME = False
LIMIT_FPS = 20  #20 frames-per-second maximum


color_dark_wall = (0, 0, 100)
color_light_wall = (130, 110, 50)
color_dark_ground = (50, 50, 150)
color_light_ground = (200, 180, 50)


class Tile:
    #a tile of the map and its properties
    def __init__(self, blocked, block_sight=None):
        self.explored = False
        self.blocked = blocked

        #all tiles start unexplored
        self.explored = False
 
        #by default, if a tile is blocked, it also blocks sight
        if block_sight is None: 
            block_sight = blocked
        self.block_sight = block_sight

class Rect:
    #a rectangle on the map. used to characterize a room.
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h

    def center(self):
        center_x = (self.x1 + self.x2) // 2
        center_y = (self.y1 + self.y2) // 2
        return (center_x, center_y)

    def intersect(self, other):
        #returns true if this rectangle intersects with another one
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and 
        self.y1 <= other.y2 and self.y2 >= other.y1)
 
class GameObject:
    #this is a generic object: the player, a monster, an item, the stairs...
    #it's always represented by a character on screen.
    def __init__(self, x, y, char, name, color, blocks=False):
        self.name = name
        self.blocks = blocks
        self.x = x
        self.y = y
        self.char = char
        self.color = color

    def move(self, dx, dy):
        #move by the given amount, if the destination is not blocked
        if not is_blocked[self.x + dx][self.y + dy].blocked:
            self.x += dx
            self.y += dy
 
    def draw(self):
        global visible_tiles

        #only show if it's visible to the player                
        if (self.x, self.y) in visible_tiles:
            #draw the character that represents this object at its position
            con.draw_char(self.x, self.y, self.char, self.color, bg=None)
 
    def clear(self):
        #erase the character that represents this object
        con.draw_char(self.x, self.y, ' ', self.color, bg=None)
 

def create_room(room):
    global my_map
    #go through the tiles in the rectangle and make them passable
    for x in range(room.x1 + 1, room.x2):
        for y in range(room.y1 + 1, room.y2):
            my_map[x][y].blocked = False
            my_map[x][y].block_sight = False

def create_h_tunnel(x1, x2, y):
    global my_map
    for x in range(min(x1, x2), max(x1, x2) + 1):
        my_map[x][y].blocked = False
        my_map[x][y].block_sight = False

def create_v_tunnel(y1, y2, x):
    global my_map
    #vertical tunnel
    for y in range(min(y1, y2), max(y1, y2) + 1):
        my_map[x][y].blocked = False
        my_map[x][y].block_sight = False
 
def is_blocked(x, y):
    #first test the map tile
    if my_map[x][y].is_blocked:
        return True

    #Now check for any blocking objects
    for obj in objects:
        if obj.blocks and obj.x == x and obj.y == y:
            return true
    
    return False



def is_visible_tile(x, y):
    global my_map

    if x >= MAP_WIDTH or x < 0:
        return False
    elif y >= MAP_HEIGHT or y < 0:
        return False
    elif my_map[x][y].blocked == True:
        return False
    elif my_map[x][y].block_sight == True:  
        return False
    else:
        return True
  
def make_map():
    global my_map
 
    #fill map with "blocked" tiles
    my_map = [[ Tile(True)
        for y in range(MAP_HEIGHT) ]
             for x in range(MAP_WIDTH) ]
 
    rooms = []
    num_rooms = 0

    for r in range(MAX_ROOMS):
        #random width and height
        w = randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        h = randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        #random position without going out of the boundaries of the map
        x = randint(0, MAP_WIDTH-w-1)
        y = randint(0, MAP_HEIGHT-h-1)

        #"Rect" class makes rectangles easier to work with
        new_room = Rect(x, y, w, h)

        #run through the other rooms and see if they intersect with this one
        failed = False
        for other_room in rooms:
            if new_room.intersect(other_room):
                failed = True
                break

        if not failed:
            #this means there are no intersections, so this room is valid

            place_objects(new_room)
            #"paint" it to the map's tiles
            create_room(new_room)

            #center coordinates of new room, will be useful later
            (new_x, new_y) = new_room.center()

            if num_rooms == 0:
                #this is the first room, where the player starts at
                player.x = new_x
                player.y = new_y

            else:
                #all rooms after the first:
                #connect it to the previous room with a tunnel

                #center coordinates of previous room
                (prev_x, prev_y) = rooms[num_rooms-1].center()

                #draw a coin (random number that is either 0 or 1)
                if randint(0, 1):
                    #first move horizontally, then vertically
                    create_h_tunnel(prev_x, new_x, prev_y)
                    create_v_tunnel(prev_y, new_y, new_x)
                else:
                    #first move vertically, then horizontally
                    create_v_tunnel(prev_y, new_y, prev_x)
                    create_h_tunnel(prev_x, new_x, new_y)

            #finally, append the new room to the list
            rooms.append(new_room)
            num_rooms += 1
    

def render_all():
    global fov_recompute
    global visible_tiles

    if fov_recompute:
        fov_recompute = False
        visible_tiles = tdl.map.quickFOV(player.x, player.y,
                                         is_visible_tile,
                                         fov=FOV_ALGO,
                                         radius=TORCH_RADIUS,
                                         lightWalls=FOV_LIGHT_WALLS)

    #go through all tiles, and set their background color  according to the FOV
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            visible = (x, y) in visible_tiles
            wall = my_map[x][y].block_sight
            if not visible:
                #if it's not visible right now, the player can only see it if it's explored
                if my_map[x][y].explored:
                    if wall:
                        con.draw_char(x, y, None, fg=None, bg=color_dark_wall)
                    else:
                        con.draw_char(x, y, None, fg=None, bg=color_dark_ground)
            else:
                if wall:
                    con.draw_char(x, y, None, fg=None, bg=color_light_wall)
                else:
                    con.draw_char(x, y, None, fg=None, bg=color_light_ground) 
                #since it's visible, explore it
                my_map[x][y].explored = True

                
    #draw all objects in the list
    for obj in objects:
        obj.draw()
 
    #blit the contents of "con" to the root console and present it
    root.blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0)
 
def handle_keys():
    global playerx, playery
    global fov_recompute
 
    if REALTIME:
        keypress = False
        for event in tdl.event.get():
            if event.type == 'KEYDOWN':
               user_input = event
               keypress = True
        if not keypress:
            return

    else: #turn-based
        user_input = tdl.event.key_wait()
 
    if user_input.key == 'ENTER' and user_input.alt:
        #Alt+Enter: toggle fullscreen
        tdl.set_fullscreen(not tdl.get_fullscreen())
 
    elif user_input.key == 'ESCAPE':
        return 'exit'  #exit game
 
    if game_state == 'playing':
        #movement keys
        if user_input.key == 'UP':
            player_move_or_attack(0, -1)
            fov_recompute = True
    
        elif user_input.key == 'DOWN':
            player_move_or_attack(0, 1)
            fov_recompute = True
        
        elif user_input.key == 'LEFT':
            player_move_or_attack(-1, 0)
            fov_recompute = True
        
        elif user_input.key == 'RIGHT':
            player_move_or_attack(1, 0)
            fov_recompute = True

    else:
        return 'didnt_take_turn'

def player_move_or_attack(dx, dy):
    global fov_recompute

    #The coordinates the player is moving/attacking to.
    x = player.x + dx
    y = player.y + dy

    #Try to find an attackable object there
    target = None
    for obj in objects:
        if obj.x == x and obj.y == y:
            target = obj
            break

    #attack if target found, otherwise move.
    if targer is not None:
        print("The " + target.name " laughs at your puny efforts to attack him.")
    else:
        player.move(dx, dy)
        fov_recompute = True    

def place_objects(room):
    #choose a random number
    num_monsters = randint(0, MAX_ROOM_MONSTERS)

    for i in range(num_monsters):
        #choose radom spot for this monster
        x = randint(room.x1, room.x2)
        y = randint(room.y1, room.y2)
        if not is_blocked(x, y):
            if randint(0,100) > 80:
                monster = GameObject(x, y, 'o', 'Orc', colors.desaturated_green, blocks=True)
            else:
                monster = GameObject(x, y, 'T', 'Troll', colors.darker_green, blocks==True)
        object.append(monster)




#############################################
# Initialization & Main Loop                #
#############################################

tdl.set_font('RogueLearn/arial10x10.png', greyscale=True, altLayout=True)
root = tdl.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="Roguelike", fullscreen=False)
tdl.setFPS(LIMIT_FPS)
con = tdl.Console(SCREEN_WIDTH, SCREEN_HEIGHT)
 game_state = 'playing'
 player_action = None
#create object representing the player
player = GameObject(0, 0, '@','Player', colors.white, blocks=True)
 
#the list of objects with those two
objects = 'playing'

 
#generate map (at this point it's not drawn to the screen)
make_map()

fov_recompute = True
 
 
while not tdl.event.is_window_closed():
 
    #draw all objects in the list
    render_all()

    tdl.flush()

    #erase all objects at their old locations, before they move
    for obj in objects:
        obj.clear()
 
    #handle keys and exit game if needed
    player_action = handle_keys()
    if player_action == 'exit':
        break

    if game_state == 'playing' and player_action != 'didnt_take_turn':
        for obj in objects:
            if obj != 'player'
                print("The " + obj.name  + " growls.")
