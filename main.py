from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import time

WIN_W, WIN_H = 1200, 800
TILE_SIZE = 120

LAYER_DEFS = [
    {"arena_x": 720,  "arena_y": 3000, "z_offset":    0, "tile_size": 120},
    {"arena_x": 540,  "arena_y": 2250, "z_offset": -800, "tile_size": 110},
    {"arena_x": 360,  "arena_y": 1500, "z_offset":-1600, "tile_size": 100},
]
LAYER_FLOOR_Z = [0, -800, -1600]   
LAYER_COUNT    = 3
FALL_THRESHOLD = -80   

ARENA_X   = LAYER_DEFS[0]["arena_x"]
ARENA_Y   = LAYER_DEFS[0]["arena_y"]
START_Y   = -2750.0
FINISH_Y  =  2750.0
FINISH_X  =  0.0
FINISH_R  =  130.0

CAM_FOLLOW, CAM_FIRST, CAM_FREE = 0, 1, 2
camera_mode   = CAM_FOLLOW
camera_angle  = 0.0
camera_height = 500.0
fovY          = 85.0

LEVEL_EASY, LEVEL_MEDIUM, LEVEL_HARD = "EASY", "MEDIUM", "HARD"
current_level = LEVEL_EASY

BASE_ENEMY_SPEED = 2.5
BASE_NUM_ENEMIES = 8

STATE_RUNNING    = "RUNNING"
STATE_LEVEL_DONE = "LEVEL_DONE"
STATE_GAMEOVER   = "GAME OVER"
STATE_WIN        = "YOU WIN!"
game_state = STATE_RUNNING

GRAVITY          = -1.2
JUMP_SPEED       = 26.0
KNOCKBACK_DECAY  = 0.80
LAUNCH_FORCE     = 50.0

player_x = player_y = player_z = player_angle = 0.0
player_speed  = 12.0
player_health = 250
player_score  = 0
player_vel_x = player_vel_y = player_vel_z = 0.0
is_on_ground   = True
sword_active   = False
jump_requested = False
keys_pressed   = {}   
player_dead    = False
damage_cooldown = 0
DAMAGE_CD_FRAMES = 20

player_layer = 0    

score_events = []
SCORE_EVENT_DURATION = 2.0
finish_rankings = []
player_finished = False

knockback_flash_timer = 0.0
KNOCKBACK_FLASH_DUR   = 0.4

slow_tiles = []
SLOW_FACTOR = 0.35
player_on_slow = False

vanish_tiles_layers    = [[], [], []]
vanish_tile_set_layers = [set(), set(), set()]

VANISH_GRACE   = 2.0 
VANISH_RESPAWN = 999.0 

LAUNCH_TILE_DEFS = [(-360,-1800,60),(360,-1200,60),(-360,-300,60),(360,600,60),(0,1500,60)]
launch_tiles = []
tile_flash   = {}

SLIDING_DOOR_DEFS = [
    {"cx":0,"cy":-2200,"half":300,"speed":4.0},
    {"cx":0,"cy":-1400,"half":350,"speed":5.0},
    {"cx":0,"cy": -400,"half":320,"speed":4.5},
    {"cx":0,"cy":  600,"half":380,"speed":5.5},
    {"cx":0,"cy": 1600,"half":340,"speed":4.0},
    {"cx":0,"cy": 2400,"half":300,"speed":6.0},
]
sliding_doors = []

HAMMER_DEFS = [
    {"cx":0,    "cy":-1800,"arm":320,"speed":2.5},
    {"cx":-360, "cy":-600, "arm":300,"speed":3.5},
    {"cx":360,  "cy":400,  "arm":300,"speed":-3.0},
    {"cx":0,    "cy":1200, "arm":340,"speed":4.0},
    {"cx":-360, "cy":2200, "arm":280,"speed":-2.8},
]
spinning_hammers = []

FLOAT_DEFS = [
    {"cy":-1000,"cz":130,"x_min":-500,"x_max":500,"speed":6.0},
    {"cy":200,  "cz":150,"x_min":-450,"x_max":450,"speed":7.5},
    {"cy":1800, "cz":140,"x_min":-520,"x_max":520,"speed":5.5},
]
float_hammers = []

BRKDOOR_DEFS = [{"cx":0,"cy":-500},{"cx":0,"cy":800},{"cx":0,"cy":2000}]
breakable_doors = []
BDOOR_THICKNESS = 30
BDOOR_HEIGHT    = 200

PENDULUM_DEFS = [
    {"px": -540, "py": -2400, "arm": 280, "max_angle": 70, "speed": 1.8},
    {"px":  540, "py": -1000, "arm": 300, "max_angle": 65, "speed": 2.2},
    {"px": -540, "py":  200,  "arm": 260, "max_angle": 75, "speed": 2.0},
    {"px":  540, "py":  1400, "arm": 290, "max_angle": 68, "speed": 1.6},
    {"px":    0, "py":  2600, "arm": 320, "max_angle": 72, "speed": 2.4},
]
pendulum_hammers = []
PENDULUM_HEAD_R    = 55
PENDULUM_KNOCKBACK = 55

ENEMY_RADIUS = 30
enemy_list   = []
bullet_list  = []
BULLET_SPEED = 24.0
BULLET_LIFE  = 100

AI_RADIUS = 28
NUM_AI    = 5
AI_COLORS = [(0.9,0.2,0.2),(0.1,0.8,0.2),(0.9,0.7,0.1),(0.7,0.1,0.9),(0.1,0.8,0.9)]
ai_players = []


last_time = 0.0
game_start_time = 0.0


def dist2(ax,ay,bx,by): return math.sqrt((ax-bx)**2+(ay-by)**2)
def clamp(v,lo,hi): return max(lo,min(hi,v))
def out_of_arena(x,y): return abs(x)>ARENA_X+100 or abs(y)>ARENA_Y+100

def layer_arena_x(layer): return LAYER_DEFS[min(layer, LAYER_COUNT-1)]["arena_x"]
def layer_arena_y(layer): return LAYER_DEFS[min(layer, LAYER_COUNT-1)]["arena_y"]
def layer_tile_size(layer): return LAYER_DEFS[min(layer, LAYER_COUNT-1)]["tile_size"]
def layer_floor_z(layer): return LAYER_FLOOR_Z[min(layer, LAYER_COUNT-1)]

def respawn_player():
    global player_x,player_y,player_z,player_vel_x,player_vel_y,player_vel_z,is_on_ground,player_layer
    player_x=0.0; player_y=START_Y+50; player_z=0.0
    player_vel_x=player_vel_y=player_vel_z=0.0; is_on_ground=True; player_layer=0

def get_enemy_speed(): return BASE_ENEMY_SPEED
def get_num_enemies(): return 0 if current_level in (LEVEL_EASY, LEVEL_HARD) else BASE_NUM_ENEMIES

def add_score_event(text, wx, wy, r=1.0, g=1.0, b=0.0):
    score_events.append([text, wx, wy, SCORE_EVENT_DURATION, r, g, b])

def tile_coords(ci, rj, layer=0):
    ts  = layer_tile_size(layer)
    ax  = layer_arena_x(layer)
    ay  = layer_arena_y(layer)
    x0  = -ax + ci * ts
    y0  = -ay + rj * ts
    return x0 + ts/2, y0 + ts/2

def world_to_tile(wx, wy, layer=0):
    ts   = layer_tile_size(layer)
    ax   = layer_arena_x(layer)
    ay   = layer_arena_y(layer)
    cols = int(ax*2/ts)
    rows = int(ay*2/ts)
    ci   = int((wx + ax) / ts)
    rj   = int((wy + ay) / ts)
    ci   = clamp(ci, 0, cols-1)
    rj   = clamp(rj, 0, rows-1)
    return ci, rj

def is_within_layer(wx, wy, layer):
    ax = layer_arena_x(layer)
    ay = layer_arena_y(layer)
    return abs(wx) <= ax and abs(wy) <= ay

def is_launch_tile(ci, rj):
    cx, cy = tile_coords(ci, rj)
    for (lx, ly, ls, _) in launch_tiles:
        if abs(cx-lx) < ls+TILE_SIZE/2 and abs(cy-ly) < ls+TILE_SIZE/2:
            return True
    return False

def make_ai(idx):
    return {"x":random.uniform(-ARENA_X+80,ARENA_X-80),"y":START_Y+random.uniform(-80,80),
            "z":0.0,"vel_z":0.0,"vel_x":0.0,"vel_y":0.0,"angle":0.0,"on_ground":True,
            "alive":True,"finished":False,"color":AI_COLORS[idx%len(AI_COLORS)],
            "speed":random.uniform(5.5,9.0),"dead":False,"on_slow":False,
            "name":f"AI{idx+1}","vanish_contact":0.0,"finish_rank":0,
            "layer":0}

def randomise_launch_tiles():
    global launch_tiles
    launch_tiles=[[lx,ly,ls,random.uniform(0,360)] for (lx,ly,ls) in LAUNCH_TILE_DEFS]

def init_sliding_doors():
    global sliding_doors
    sliding_doors=[{**d,"offset":0,"dir":random.choice([-1,1])} for d in SLIDING_DOOR_DEFS]

def init_hammers():
    global spinning_hammers
    spinning_hammers=[{**h,"angle":random.uniform(0,360)} for h in HAMMER_DEFS]

def init_float_hammers():
    global float_hammers
    float_hammers=[{**f,"cx":f["x_min"],"dir":1} for f in FLOAT_DEFS]

def init_breakable_doors():
    global breakable_doors
    breakable_doors=[{**b,"alive":True} for b in BRKDOOR_DEFS]

def init_pendulum_hammers():
    global pendulum_hammers
    pendulum_hammers=[]
    for p in PENDULUM_DEFS:
        ph = dict(p)
        ph["angle"]  = random.uniform(-p["max_angle"]*0.5, p["max_angle"]*0.5)
        ph["omega"]  = random.uniform(-p["speed"]*1.6, p["speed"]*1.6)
        pendulum_hammers.append(ph)

def init_slow_tiles():
    global slow_tiles
    slow_tiles = []
    cols = int(ARENA_X*2/TILE_SIZE)
    rows = int(ARENA_Y*2/TILE_SIZE)
    for ci in range(cols):
        for rj in range(rows):
            if is_launch_tile(ci, rj): continue
            if random.random() < 0.12:
                slow_tiles.append((ci, rj))

def init_vanish_tiles_hard_mode():
    global vanish_tiles_layers, vanish_tile_set_layers
    vanish_tiles_layers    = [[], [], []]
    vanish_tile_set_layers = [set(), set(), set()]

    for layer in range(LAYER_COUNT):
        ts   = layer_tile_size(layer)
        ax   = layer_arena_x(layer)
        ay   = layer_arena_y(layer)
        cols = int(ax*2/ts)
        rows = int(ay*2/ts)
        fz   = layer_floor_z(layer)
        grace = VANISH_GRACE * (1.0 - layer * 0.25)   
        for ci in range(cols):
            for rj in range(rows):
                cx, cy = tile_coords(ci, rj, layer)
                vanish_tiles_layers[layer].append({
                    "ci": ci, "rj": rj, "cx": cx, "cy": cy,
                    "state": "solid", "timer": 0.0,
                    "floor_z": fz, "grace": grace
                })
                vanish_tile_set_layers[layer].add((ci, rj))

def spawn_enemies():
    global enemy_list
    enemy_list=[]
    for _ in range(get_num_enemies()):
        ex=random.uniform(-ARENA_X+60,ARENA_X-60)
        ey=random.uniform(-ARENA_Y+100,ARENA_Y-100)
        while dist2(ex,ey,player_x,player_y)<400:
            ex=random.uniform(-ARENA_X+60,ARENA_X-60)
            ey=random.uniform(-ARENA_Y+100,ARENA_Y-100)
        enemy_list.append([ex,ey,True])

def init_level():
    global last_time, game_start_time
    global sliding_doors, spinning_hammers, float_hammers, breakable_doors, pendulum_hammers
    global slow_tiles, launch_tiles, enemy_list, vanish_tiles_layers, vanish_tile_set_layers

    if current_level == LEVEL_HARD:
        sliding_doors = []
        spinning_hammers = []
        float_hammers = []
        breakable_doors = []
        pendulum_hammers = []
        slow_tiles = []
        launch_tiles = []
        enemy_list = []
        init_vanish_tiles_hard_mode()
    else:
        randomise_launch_tiles()
        init_sliding_doors()
        init_hammers()
        init_float_hammers()
        init_breakable_doors()
        init_pendulum_hammers()
        init_slow_tiles()
        spawn_enemies()
        vanish_tiles_layers    = [[], [], []]
        vanish_tile_set_layers = [set(), set(), set()]

    last_time = time.time()
    game_start_time = time.time()

def reset_game(level=LEVEL_EASY):
    global player_x,player_y,player_z,player_angle,player_vel_x,player_vel_y,player_vel_z
    global player_health,player_score,is_on_ground,sword_active,jump_requested
    global bullet_list,tile_flash,game_state,keys_pressed,ai_players
    global current_level,player_dead,damage_cooldown,player_on_slow
    global score_events,finish_rankings,player_finished,knockback_flash_timer
    global player_layer

    current_level=level
    player_x=0.0; player_y=START_Y; player_z=0.0; player_angle=0.0
    player_health=250; player_score=0
    player_vel_x=player_vel_y=player_vel_z=0.0
    is_on_ground=True; sword_active=False; jump_requested=False
    player_dead=False; damage_cooldown=0; player_on_slow=False
    bullet_list=[]; tile_flash={}; keys_pressed={}
    game_state=STATE_RUNNING
    score_events=[]; finish_rankings=[]; player_finished=False
    knockback_flash_timer=0.0
    player_layer=0

    if current_level == LEVEL_HARD:
        ai_players = []
        for i in range(NUM_AI):
            ai = make_ai(i)
            ai["x"] = random.uniform(-ARENA_X+100, ARENA_X-100)
            ai["y"] = START_Y + random.uniform(-200, 400)
            ai["layer"] = 0
            ai_players.append(ai)
    else:
        ai_players=[make_ai(i) for i in range(NUM_AI)]

    init_level()

def draw_text(x,y,text,font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1,1,1)
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0,WIN_W,0,WIN_H)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    glRasterPos2f(x,y)
    for ch in text: glutBitmapCharacter(font,ord(ch))
    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)

def draw_text_color(x,y,text,r,g,b,font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(r,g,b)
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0,WIN_W,0,WIN_H)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    glRasterPos2f(x,y)
    for ch in text: glutBitmapCharacter(font,ord(ch))
    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)



def draw_death_scene():
    glColor3f(1.0,1.0,1.0)
    glBegin(GL_QUADS)
    glVertex3f(-8000,-8000,0); glVertex3f(8000,-8000,0)
    glVertex3f(8000,8000,0);   glVertex3f(-8000,8000,0)
    glEnd()
    glPushMatrix(); glTranslatef(player_x,player_y,1)
    glColor3f(0.15,0.55,1.0)
    glBegin(GL_QUADS)
    glVertex3f(-23,-40,0); glVertex3f(23,-40,0)
    glVertex3f(23,40,0);   glVertex3f(-23,40,0)
    glEnd()
    glColor3f(1.0,0.82,0.65)
    glBegin(GL_POLYGON)
    for i in range(16):
        a=math.radians(i*22.5)
        glVertex3f(math.cos(a)*22, 52+math.sin(a)*22, 0)
    glEnd()
    glColor3f(0,0,0)
    for ex2,ey2 in [(-8,52),(8,52)]:
        glBegin(GL_LINES)
        glVertex3f(ex2-5,ey2-5,1); glVertex3f(ex2+5,ey2+5,1)
        glEnd()
        glBegin(GL_LINES)
        glVertex3f(ex2+5,ey2-5,1); glVertex3f(ex2-5,ey2+5,1)
        glEnd()
    glPopMatrix()

LAYER_BASE_COLORS = [
    ((0.72, 0.72, 0.80), (0.38, 0.38, 0.58)),   
    ((0.80, 0.55, 0.20), (0.58, 0.35, 0.10)),   
    ((0.95, 0.30, 0.95), (0.45, 0.05, 0.65)),   
]

def draw_floor_layer(layer):
    ld      = LAYER_DEFS[layer]
    ax      = ld["arena_x"]
    ay      = ld["arena_y"]
    ts      = ld["tile_size"]
    fz      = LAYER_FLOOR_Z[layer]
    cols    = int(ax*2/ts)
    rows    = int(ay*2/ts)
    even_c, odd_c = LAYER_BASE_COLORS[layer]

    vanish_state = {}
    for vt in vanish_tiles_layers[layer]:
        vanish_state[(vt["ci"],vt["rj"])] = (vt["state"], vt["timer"], vt["grace"])

    for i in range(cols):
        for j in range(rows):
            x0 = -ax + i*ts; y0 = -ay + j*ts
            cx = x0 + ts/2;  cy = y0 + ts/2

            vs_info = vanish_state.get((i,j), ("solid", 0.0, VANISH_GRACE))
            vs, vtimer, grace = vs_info
            if vs == "gone": continue

            if vs == "cracking":
                frac = min(1.0, vtimer / grace)
                r = even_c[0] + (0.9 - even_c[0])*frac
                g = even_c[1] * (1.0 - frac*0.9)
                b = even_c[2] * (1.0 - frac)
                glColor3f(r, g, b)
            elif (i+j)%2==0:
                glColor3f(*even_c)
            else:
                glColor3f(*odd_c)

            glBegin(GL_QUADS)
            glVertex3f(x0,    y0,    fz)
            glVertex3f(x0+ts, y0,    fz)
            glVertex3f(x0+ts, y0+ts, fz)
            glVertex3f(x0,    y0+ts, fz)
            glEnd()

            # Crack lines on cracking tiles
            if vs == "cracking":
                frac = min(1.0, vtimer / grace)
                glColor3f(0.12,0.06,0.0)
                glLineWidth(1.5 + frac*3.0)
                glBegin(GL_LINES)
                glVertex3f(cx-ts*0.3, cy-ts*0.1, fz+3)
                glVertex3f(cx+ts*0.1, cy+ts*0.35, fz+3)
                glVertex3f(cx+ts*0.2, cy-ts*0.3, fz+3)
                glVertex3f(cx-ts*0.15,cy+ts*0.2, fz+3)
                if frac > 0.5:
                    glVertex3f(cx-ts*0.1, cy-ts*0.35, fz+3)
                    glVertex3f(cx+ts*0.35, cy+ts*0.1, fz+3)
                glEnd()
                glLineWidth(1.0)

def draw_layer_walls(layer):
    ld  = LAYER_DEFS[layer]
    ax  = ld["arena_x"]
    ay  = ld["arena_y"]
    fz  = LAYER_FLOOR_Z[layer]
    wh  = 60  
    intensity = 1.0 - layer * 0.25
    glColor3f(0.35*intensity, 0.20*intensity, 0.08*intensity)

    for sx in [-ax-8, ax+8]:
        glPushMatrix(); glTranslatef(sx, 0, fz + wh/2)
        glScalef(16.0/120, (ay*2)/120, wh/120)
        glutSolidCube(120); glPopMatrix()
    for sy in [-ay-8, ay+8]:
        glPushMatrix(); glTranslatef(0, sy, fz + wh/2)
        glScalef((ax*2+32)/120, 16.0/120, wh/120)
        glutSolidCube(120); glPopMatrix()

def draw_layer_hole_rim(layer):
    """
    Draw a glowing rim around the hole in the upper layer floor
    so players can see where to fall through.
    Only drawn for layers 0 and 1 (they have a layer below).
    """
    if layer >= LAYER_COUNT - 1: return
    lower_ld = LAYER_DEFS[layer+1]
    ax2 = lower_ld["arena_x"]
    ay2 = lower_ld["arena_y"]
    fz  = LAYER_FLOOR_Z[layer]

    # Pulsing glow colour
    pulse = 0.5 + 0.5*math.sin(time.time()*3.0)
    if layer == 0:
        glColor3f(1.0, 0.6*pulse+0.4, 0.0)
    else:
        glColor3f(1.0, 0.1, 0.1*pulse+0.05)

    thick = 18
    glBegin(GL_QUADS)
    # bottom strip
    glVertex3f(-ax2-thick, -ay2-thick, fz+4)
    glVertex3f( ax2+thick, -ay2-thick, fz+4)
    glVertex3f( ax2+thick, -ay2,       fz+4)
    glVertex3f(-ax2-thick, -ay2,       fz+4)
    # top strip
    glVertex3f(-ax2-thick,  ay2,       fz+4)
    glVertex3f( ax2+thick,  ay2,       fz+4)
    glVertex3f( ax2+thick,  ay2+thick, fz+4)
    glVertex3f(-ax2-thick,  ay2+thick, fz+4)
    # left strip
    glVertex3f(-ax2-thick, -ay2, fz+4)
    glVertex3f(-ax2,       -ay2, fz+4)
    glVertex3f(-ax2,        ay2, fz+4)
    glVertex3f(-ax2-thick,  ay2, fz+4)
    # right strip
    glVertex3f( ax2,       -ay2, fz+4)
    glVertex3f( ax2+thick, -ay2, fz+4)
    glVertex3f( ax2+thick,  ay2, fz+4)
    glVertex3f( ax2,        ay2, fz+4)
    glEnd()

def draw_floor():
    if current_level == LEVEL_HARD:
        for layer in range(LAYER_COUNT-1, -1, -1):
            draw_floor_layer(layer)
            draw_layer_walls(layer)
            draw_layer_hole_rim(layer)
    else:
        # Normal non-hard floor
        cols=int(ARENA_X*2/TILE_SIZE); rows=int(ARENA_Y*2/TILE_SIZE)
        slow_set = set(slow_tiles)

        for i in range(cols):
            for j in range(rows):
                x0=-ARENA_X+i*TILE_SIZE; y0=-ARENA_Y+j*TILE_SIZE
                cx=x0+TILE_SIZE/2; cy=y0+TILE_SIZE/2

                is_launch=False; launch_idx=-1
                for li,(lx,ly,ls,_) in enumerate(launch_tiles):
                    if abs(cx-lx)<ls+TILE_SIZE/2 and abs(cy-ly)<ls+TILE_SIZE/2:
                        is_launch=True; launch_idx=li; break

                if is_launch:
                    flash=tile_flash.get(launch_idx,0)
                    glColor3f(1.0,1.0,0.0) if flash>0 else glColor3f(0.9,0.1,0.1)
                elif (i,j) in slow_set:
                    glColor3f(0.35, 0.55, 0.15)
                elif (i+j)%2==0:
                    glColor3f(0.72,0.72,0.80)
                else:
                    glColor3f(0.38,0.38,0.58)

                glBegin(GL_QUADS)
                glVertex3f(x0,y0,0); glVertex3f(x0+TILE_SIZE,y0,0)
                glVertex3f(x0+TILE_SIZE,y0+TILE_SIZE,0); glVertex3f(x0,y0+TILE_SIZE,0)
                glEnd()

                if (i,j) in slow_set:
                    glColor3f(0.2, 0.35, 0.05)
                    for ddx,ddy in [(-20,-20),(20,-20),(0,10),(-30,25),(30,15)]:
                        glBegin(GL_POLYGON)
                        for k in range(6):
                            a=math.radians(k*60)
                            glVertex3f(cx+ddx+math.cos(a)*7, cy+ddy+math.sin(a)*7, 1)
                        glEnd()

def draw_start_line():
    if current_level == LEVEL_HARD: return
    glColor3f(0.2,1.0,0.2)
    glBegin(GL_QUADS)
    glVertex3f(-ARENA_X,START_Y-14,2); glVertex3f(ARENA_X,START_Y-14,2)
    glVertex3f(ARENA_X,START_Y+14,2);  glVertex3f(-ARENA_X,START_Y+14,2)
    glEnd()
    glColor3f(1.0,1.0,0.0)
    for sx in [-ARENA_X,ARENA_X]:
        glPushMatrix(); glTranslatef(sx,START_Y,0)
        gluCylinder(gluNewQuadric(),8,8,200,8,4); glPopMatrix()
    glColor3f(0.0,0.8,0.1)
    glBegin(GL_QUADS)
    glVertex3f(-160,START_Y-8,180); glVertex3f(160,START_Y-8,180)
    glVertex3f(160,START_Y+8,200);  glVertex3f(-160,START_Y+8,200)
    glEnd()

def draw_finish_line():
    if current_level == LEVEL_HARD: return
    stripe_w=ARENA_X*2/12
    for i in range(12):
        x0=-ARENA_X+i*stripe_w
        glColor3f(1,1,1) if i%2==0 else glColor3f(0,0,0)
        glBegin(GL_QUADS)
        glVertex3f(x0,FINISH_Y-14,2); glVertex3f(x0+stripe_w,FINISH_Y-14,2)
        glVertex3f(x0+stripe_w,FINISH_Y+14,2); glVertex3f(x0,FINISH_Y+14,2)
        glEnd()
    glColor3f(0.0,1.0,0.45)
    glPushMatrix(); glTranslatef(FINISH_X,FINISH_Y,3)
    gluDisk(gluNewQuadric(),0,FINISH_R,40,1); glPopMatrix()
    glColor3f(1.0,0.8,0.0)
    for sx in [-ARENA_X,ARENA_X]:
        glPushMatrix(); glTranslatef(sx,FINISH_Y,0)
        gluCylinder(gluNewQuadric(),8,8,240,8,4); glPopMatrix()
    glPushMatrix(); glTranslatef(FINISH_X,FINISH_Y,0)
    gluCylinder(gluNewQuadric(),6,6,210,8,4)
    glTranslatef(0,0,210); glColor3f(1.0,0.85,0.0)
    for i in range(5):
        ar=math.radians(i*72.0); ar2=math.radians(i*72.0+36)
        glBegin(GL_TRIANGLES)
        glVertex3f(0,0,0)
        glVertex3f(math.cos(ar)*42,math.sin(ar)*42,58)
        glVertex3f(math.cos(ar2)*22,math.sin(ar2)*22,0)
        glEnd()
    glPopMatrix()

def draw_walls():
    if current_level == LEVEL_HARD: return  
    glColor3f(0.45,0.25,0.07); wh=150
    for sx in [-ARENA_X-10, ARENA_X+10]:
        glPushMatrix(); glTranslatef(sx,0,wh/2)
        glScalef(20.0/120,(ARENA_Y*2)/120,wh/120)
        glutSolidCube(120); glPopMatrix()
    for sy in [-ARENA_Y-10, ARENA_Y+10]:
        glPushMatrix(); glTranslatef(0,sy,wh/2)
        glScalef((ARENA_X*2+40)/120,20.0/120,wh/120)
        glutSolidCube(120); glPopMatrix()

def draw_body(bc, hc=(1.0,0.82,0.65)):
    glColor3f(*bc)
    glPushMatrix(); glTranslatef(0,0,38); glutSolidCube(46); glPopMatrix()
    glColor3f(*hc)
    glPushMatrix(); glTranslatef(0,0,76); glutSolidSphere(23,14,14); glPopMatrix()
    glColor3f(0,0,0)
    glPushMatrix(); glTranslatef(9,23,81); glutSolidSphere(5,6,6); glPopMatrix()
    glPushMatrix(); glTranslatef(-9,23,81); glutSolidSphere(5,6,6); glPopMatrix()
    ac=(bc[0]*0.8,bc[1]*0.8,bc[2]*0.8); glColor3f(*ac)
    for sx in [-1,1]:
        glPushMatrix(); glTranslatef(sx*32,0,44); glRotatef(90,1,0,0)
        gluCylinder(gluNewQuadric(),8,7,38,8,4); glPopMatrix()
    lc=(bc[0]*0.6,bc[1]*0.6,bc[2]*0.6); glColor3f(*lc)
    for sx in [-1,1]:
        glPushMatrix(); glTranslatef(sx*14,0,9); glRotatef(180,1,0,0)
        gluCylinder(gluNewQuadric(),9,9,32,8,4); glPopMatrix()

def draw_player():
    if player_dead or camera_mode==CAM_FIRST: return
    glPushMatrix(); glTranslatef(player_x,player_y,player_z); glRotatef(player_angle,0,0,1)
    draw_body((0.15,0.55,1.0))
    if sword_active:
        glPushMatrix(); glTranslatef(40,10,36); glRotatef(-60,0,0,1); glRotatef(20,1,0,0)
        glColor3f(0.85,0.92,1.0); gluCylinder(gluNewQuadric(),4,1,95,6,4)
        glColor3f(0.8,0.65,0.0); glPushMatrix(); glScalef(3,1,0.5); glutSolidCube(14); glPopMatrix()
        glPopMatrix()
    glPopMatrix()

def draw_ai_players():
    for ai in ai_players:
        if not ai["alive"]: continue
        if ai["dead"]:
            if current_level == LEVEL_HARD: continue
            glPushMatrix(); glTranslatef(ai["x"],ai["y"],1)
            glColor3f(*ai["color"])
            glBegin(GL_QUADS)
            glVertex3f(-20,-35,0); glVertex3f(20,-35,0)
            glVertex3f(20,35,0);   glVertex3f(-20,35,0)
            glEnd()
            glPopMatrix(); continue
        glPushMatrix(); glTranslatef(ai["x"],ai["y"],ai["z"]); glRotatef(ai["angle"],0,0,1)
        draw_body(ai["color"]); glPopMatrix()

def draw_launch_tiles():
    for li,(lx,ly,ls,ang) in enumerate(launch_tiles):
        flash=tile_flash.get(li,0)
        glColor3f(1.0,1.0,0.0) if flash>0 else glColor3f(1.0,0.05,0.05)
        glBegin(GL_QUADS)
        glVertex3f(lx-ls,ly-ls,2); glVertex3f(lx+ls,ly-ls,2)
        glVertex3f(lx+ls,ly+ls,2); glVertex3f(lx-ls,ly+ls,2)
        glEnd()
        glColor3f(1,1,0); ar=math.radians(ang)
        ax=math.sin(ar)*28; ay=math.cos(ar)*28
        px=-math.cos(ar)*12; py=math.sin(ar)*12
        glBegin(GL_TRIANGLES)
        glVertex3f(lx+ax,ly+ay,3); glVertex3f(lx+px,ly+py,3); glVertex3f(lx-px,ly-py,3)
        glEnd()

def draw_sliding_doors():
    for d in sliding_doors:
        glPushMatrix(); glTranslatef(d["cx"]+d["offset"],d["cy"],65)
        glScalef((d["half"]*2)/65,1.0,1.0); glColor3f(0.2,0.6,0.95)
        glutSolidCube(65); glPopMatrix()

def draw_spinning_hammers():
    for h in spinning_hammers:
        glPushMatrix(); glTranslatef(h["cx"],h["cy"],90); glRotatef(h["angle"],0,0,1)
        glColor3f(0.5,0.5,0.5)
        glPushMatrix(); glRotatef(-90,1,0,0); glTranslatef(0,0,-90)
        gluCylinder(gluNewQuadric(),8,8,90,8,4); glPopMatrix()
        glColor3f(0.6,0.3,0.1)
        glPushMatrix(); glTranslatef(h["arm"]/2,0,0); glScalef(h["arm"]/32,1.0,1.0)
        glutSolidCube(32); glPopMatrix()
        glColor3f(0.85,0.1,0.85)
        glPushMatrix(); glTranslatef(h["arm"],0,0); glutSolidCube(58); glPopMatrix()
        glPopMatrix()

def draw_float_hammers():
    for fh in float_hammers:
        glPushMatrix(); glTranslatef(fh["cx"],fh["cy"],fh["cz"])
        glColor3f(0.9,0.5,0.1)
        glPushMatrix(); glScalef(4.2,1.0,0.5); glutSolidCube(58); glPopMatrix()
        glColor3f(0.2,0.8,0.3)
        glPushMatrix(); glTranslatef(-130,0,0); glutSolidCube(50); glPopMatrix()
        glPushMatrix(); glTranslatef(130,0,0);  glutSolidCube(50); glPopMatrix()
        glColor3f(0.7,0.7,0.7)
        glPushMatrix(); glRotatef(90,1,0,0); glTranslatef(0,-fh["cz"],0)
        gluCylinder(gluNewQuadric(),5,5,fh["cz"],6,4); glPopMatrix()
        glPopMatrix()

def draw_breakable_doors():
    for bd in breakable_doors:
        if not bd["alive"]: continue
        glPushMatrix(); glTranslatef(bd["cx"],bd["cy"],BDOOR_HEIGHT/2)
        glColor3f(0.65,0.38,0.12)
        glScalef((ARENA_X*2)/60,(BDOOR_THICKNESS*2)/60,BDOOR_HEIGHT/60)
        glutSolidCube(60); glPopMatrix()
        glColor3f(0.45,0.25,0.05)
        for dz in [-BDOOR_HEIGHT*0.3, 0, BDOOR_HEIGHT*0.3]:
            glPushMatrix(); glTranslatef(bd["cx"],bd["cy"],BDOOR_HEIGHT/2+dz)
            glScalef((ARENA_X*2)/60,(BDOOR_THICKNESS*2+2)/60,4.0/60)
            glutSolidCube(60); glPopMatrix()

def draw_pendulum_hammers():
    for ph in pendulum_hammers:
        ang_rad = math.radians(ph["angle"])
        pivot_z = 320
        tip_x = ph["px"] + math.sin(ang_rad) * ph["arm"]
        tip_y = ph["py"]
        tip_z = pivot_z - math.cos(ang_rad) * ph["arm"]

        glPushMatrix(); glTranslatef(ph["px"], ph["py"], pivot_z)
        glColor3f(0.6,0.6,0.6); glutSolidSphere(14, 8, 8); glPopMatrix()

        glColor3f(0.55, 0.28, 0.08)
        glBegin(GL_LINES)
        glVertex3f(ph["px"], ph["py"], pivot_z)
        glVertex3f(tip_x, tip_y, tip_z)
        glEnd()

        dx = tip_x - ph["px"]; dz = tip_z - pivot_z
        rod_len = math.sqrt(dx*dx + dz*dz) + 0.001
        rot_angle = math.degrees(math.atan2(dx, -dz))
        glPushMatrix(); glTranslatef(ph["px"], ph["py"], pivot_z); glRotatef(rot_angle, 0, 1, 0)
        glColor3f(0.55, 0.28, 0.08)
        gluCylinder(gluNewQuadric(), 10, 10, rod_len, 8, 2); glPopMatrix()

        glPushMatrix(); glTranslatef(tip_x, tip_y, tip_z)
        glColor3f(0.75, 0.1, 0.1); glutSolidSphere(PENDULUM_HEAD_R, 14, 14)
        glColor3f(0.95, 0.3, 0.0)
        for k in range(6):
            a = math.radians(k*60)
            glPushMatrix()
            glTranslatef(math.cos(a)*PENDULUM_HEAD_R*0.7, math.sin(a)*PENDULUM_HEAD_R*0.7, 0)
            glutSolidCone(10, 22, 5, 2); glPopMatrix()
        glPopMatrix()

def draw_enemies():
    for e in enemy_list:
        if not e[2]: continue
        glPushMatrix(); glTranslatef(e[0],e[1],0)
        glColor3f(1.0,0.18,0.18)
        glPushMatrix(); glTranslatef(0,0,30); glutSolidCube(40); glPopMatrix()
        glColor3f(1.0,0.55,0.0)
        glPushMatrix(); glTranslatef(0,0,62); glutSolidSphere(20,10,10); glPopMatrix()
        glPopMatrix()

def draw_bullets():
    glColor3f(1.0,1.0,0.1)
    for b in bullet_list:
        glPushMatrix(); glTranslatef(b[0],b[1],32)
        glutSolidSphere(9,8,8); glPopMatrix()

_cached_mv = None
_cached_pj = None
_cached_vp = (0, 0, WIN_W, WIN_H)

def world_to_screen(wx, wy, wz=80):
    """Project a world point to screen coords using cached GLfloat matrices (no glGetDoublev)."""
    if _cached_mv is None or _cached_pj is None:
        return None
    try:
        sx, sy, _ = gluProject(wx, wy, wz, _cached_mv, _cached_pj, _cached_vp)
        return int(sx), int(sy)
    except Exception:
        return None

def draw_score_events():
    for ev in score_events:
        text, wx, wy, t, r, g, b = ev
        offset_z = 80 + (SCORE_EVENT_DURATION - t) * 60
        sc = world_to_screen(wx, wy, offset_z)
        if sc:
            sx, sy = sc
            if 0 < sx < WIN_W and 0 < sy < WIN_H:
                draw_text_color(sx, sy, text, r, g, b)

def draw_knockback_overlay():
    glColor3f(1.0, 0.0, 0.0)
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800) 
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glBegin(GL_QUADS)
    
    # Bottom Edge
    glVertex3f(0, 0, 0)
    glVertex3f(1000, 0, 0)
    glVertex3f(1000, 20, 0)
    glVertex3f(0, 20, 0)
    
    # Top Edge
    glVertex3f(0, 780, 0)
    glVertex3f(1000, 780, 0)
    glVertex3f(1000, 800, 0)
    glVertex3f(0, 800, 0)
    
    # Left Edge
    glVertex3f(0, 20, 0)
    glVertex3f(20, 20, 0)
    glVertex3f(20, 780, 0)
    glVertex3f(0, 780, 0)
    
    # Right Edge
    glVertex3f(980, 20, 0)
    glVertex3f(1000, 20, 0)
    glVertex3f(1000, 780, 0)
    glVertex3f(980, 780, 0)
    
    glEnd()

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_comment():
    cam_names=["FOLLOW","FIRST-PERSON","FREE"]
    lvl_colors={LEVEL_EASY:(0.3,1,0.3),LEVEL_MEDIUM:(1,0.8,0.1),LEVEL_HARD:(1,0.2,0.2)}
    lc=lvl_colors[current_level]
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0,WIN_W,0,WIN_H)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    glColor3f(0.3,0,0)
    glBegin(GL_QUADS)
    glVertex2f(8,WIN_H-22); glVertex2f(258,WIN_H-22)
    glVertex2f(258,WIN_H-8); glVertex2f(8,WIN_H-8)
    glEnd()
    hp_frac=max(0,player_health/250.0)
    glColor3f(1.0-hp_frac,hp_frac,0.1)
    glBegin(GL_QUADS)
    glVertex2f(8,WIN_H-22); glVertex2f(8+250*hp_frac,WIN_H-22)
    glVertex2f(8+250*hp_frac,WIN_H-8); glVertex2f(8,WIN_H-8)
    glEnd()
    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)

    draw_text(10,WIN_H-40,f"HP: {player_health}/250  Score: {player_score}")
    draw_text_color(10,WIN_H-62,f"Level: {current_level}",*lc)
    slow_txt = "  [SLOW ZONE]" if player_on_slow else ""
    draw_text(10,WIN_H-84,f"Cam: {cam_names[camera_mode]}  Sword: {'ON' if sword_active else 'OFF'}{slow_txt}")
    draw_text(10,WIN_H-106,"WASD=Move  SPACE=Jump  LClick=Shoot  RClick=Sword  C=Cam  R=Restart")

    if current_level == LEVEL_HARD:
        layer_names = ["TOP (Layer 1)", "MIDDLE (Layer 2)", "BOTTOM (Layer 3)"]
        layer_colors = [(0.5,0.8,1.0),(1.0,0.6,0.1),(1.0,0.2,0.2)]
        lname = layer_names[min(player_layer, LAYER_COUNT-1)]
        lc2   = layer_colors[min(player_layer, LAYER_COUNT-1)]
        draw_text_color(10,WIN_H-128,f"Current Floor: {lname}  [Fall through to descend!]",*lc2)

    sb_x = WIN_W - 230
   

    if current_level == LEVEL_HARD:
        draw_text_color(sb_x, WIN_H-22, "-- SURVIVAL LOG --", 1.0, 0.2, 0.2)
        alive_ais = sum(1 for ai in ai_players if not ai["dead"])
        draw_text_color(sb_x, WIN_H-44, f"You: {'ALIVE' if not player_dead else 'DEAD'}", 0.3, 0.8, 1.0)
        draw_text_color(sb_x, WIN_H-66, f"AI Alive: {alive_ais} / {NUM_AI}", 1.0, 0.8, 0.0)
        
        for i, ai in enumerate(ai_players):
            if ai["dead"]:
                draw_text_color(sb_x, WIN_H-88-i*20, f"{ai['name']}: DEAD", 0.5,0.5,0.5)
            else:
                ln = ai.get("layer", 0)+1
                draw_text_color(sb_x, WIN_H-88-i*20, f"{ai['name']}: L{ln}", *ai["color"])
    else:
        draw_text_color(sb_x, WIN_H-22, "-- RACE STANDINGS --", 1.0, 0.9, 0.0)
        if player_finished:
            rank = finish_rankings.index("You")+1 if "You" in finish_rankings else "?"
            pst = f"#{rank} FINISHED"
            draw_text_color(sb_x, WIN_H-44, f"You:  {pst}  Sc:{player_score}", 0.2, 1.0, 0.4)
        elif player_dead:
            draw_text_color(sb_x, WIN_H-44, f"You:  DEAD  Sc:{player_score}", 1.0, 0.3, 0.3)
        else:
            draw_text_color(sb_x, WIN_H-44, f"You:  {player_y:.0f}  Sc:{player_score}", 0.3, 0.8, 1.0)
        for i, ai in enumerate(ai_players):
            if ai["dead"]:
                st = "DEAD"; rc, gc, bc = 1.0, 0.3, 0.3
            elif ai["finished"]:
                rank = finish_rankings.index(ai["name"])+1 if ai["name"] in finish_rankings else "?"
                st = f"#{rank} FIN"; rc, gc, bc = 0.2, 1.0, 0.4
            else:
                st = f"{ai['y']:.0f}"; rc, gc, bc = *ai["color"],
            draw_text_color(sb_x, WIN_H-66-i*22, f"{ai['name']}: {st}", rc, gc, bc)

    if current_level == LEVEL_MEDIUM:
        draw_text_color(10,WIN_H-150,"[Green = MUD: slows you]",0.5,0.9,0.2)
    if current_level == LEVEL_HARD:
        draw_text_color(10,WIN_H-150,"[3-LAYER HEX-A-GONE: Tiles vanish! Fall to next layer!]",1.0,0.55,0.1)
        draw_text_color(10,WIN_H-172,"[Layer 1 -> Layer 2 -> Layer 3 (smallest) -> VOID = DEAD]",0.9,0.4,0.1)

    # Level complete / game over overlays─
    if game_state == STATE_LEVEL_DONE:
        draw_text_color(WIN_W//2-130,WIN_H//2+55,"LEVEL COMPLETE!",0.2,1.0,0.3,GLUT_BITMAP_TIMES_ROMAN_24)
        elapsed = time.time() - game_start_time
        draw_text_color(WIN_W//2-130,WIN_H//2+28,f"Time: {elapsed:.1f}s   Final Score: {player_score}",1.0,0.9,0.1)

        if current_level != LEVEL_HARD:
            draw_text_color(WIN_W//2-130,WIN_H//2+8,"Finish Order:",0.8,0.8,1.0)
            for ri, name in enumerate(finish_rankings):
                draw_text_color(WIN_W//2-120+ri*95, WIN_H//2-12, f"#{ri+1} {name}", 0.9,0.8,0.2)

        if current_level==LEVEL_EASY:
            draw_text(WIN_W//2-180,WIN_H//2-40,"Press M = Continue to MEDIUM")
            draw_text(WIN_W//2-180,WIN_H//2-60,"Press H = Continue to HARD (3-Layer Survival)")
            draw_text(WIN_W//2-180,WIN_H//2-80,"Press R = Restart Easy")
        elif current_level==LEVEL_MEDIUM:
            draw_text(WIN_W//2-180,WIN_H//2-40,"Press H = Continue to HARD (3-Layer Survival)")
            draw_text(WIN_W//2-180,WIN_H//2-60,"Press R = Restart")
        else:
            draw_text_color(WIN_W//2-150,WIN_H//2-20,"SURVIVAL CHAMPION! Last one standing!",1,0.9,0,GLUT_BITMAP_HELVETICA_18)
            draw_text(WIN_W//2-100,WIN_H//2-55,"Press R = Restart")

    if game_state == STATE_GAMEOVER:
        draw_text_color(WIN_W//2-100,WIN_H//2+45,"GAME OVER",1,0.1,0.1,GLUT_BITMAP_TIMES_ROMAN_24)
        draw_text_color(WIN_W//2-130,WIN_H//2+18,f"Final Score: {player_score}",1.0,0.8,0.1)
        if current_level == LEVEL_HARD:
            draw_text_color(WIN_W//2-120,WIN_H//2-8,"You fell through all 3 floors into the void!",0.7,0.7,0.7)
        else:
            if finish_rankings:
                winner = finish_rankings[0]
                draw_text_color(WIN_W//2-150,WIN_H//2-8,
                                f"Winner: {winner}  |  Order: {', '.join(finish_rankings)}",0.3,1.0,0.4)
            else:
                draw_text_color(WIN_W//2-120,WIN_H//2-8,"Nobody finished yet...",0.7,0.7,0.7)
        draw_text(WIN_W//2-150,WIN_H//2-40,"Press R to restart")
        draw_text_color(WIN_W//2-150,WIN_H//2-65,
                        f"Score breakdown: Enemies={player_score} ",0.6,0.8,1.0)

def setupCamera():
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    gluPerspective(fovY,WIN_W/WIN_H,0.1,16000)
    glMatrixMode(GL_MODELVIEW); glLoadIdentity()
    if camera_mode==CAM_FOLLOW:
        rad=math.radians(player_angle)
        cx=player_x+math.sin(rad)*380; cy=player_y-math.cos(rad)*380
      
        cz = player_z + 380
        gluLookAt(cx,cy,cz,player_x,player_y,player_z+50,0,0,1)
    elif camera_mode==CAM_FIRST:
        rad=math.radians(player_angle)
        cx,cy,cz=player_x,player_y,player_z+72
        lx=player_x-math.sin(rad)*100; ly=player_y+math.cos(rad)*100
        gluLookAt(cx,cy,cz,lx,ly,cz,0,0,1)
    else:
        rad=math.radians(camera_angle)
        dist = 4500 if current_level == LEVEL_HARD else 2800
        gluLookAt(math.sin(rad)*dist,-math.cos(rad)*dist,camera_height,0,0,-700 if current_level==LEVEL_HARD else 0,0,0,1)
    global _cached_mv, _cached_pj
    _cached_mv = (GLfloat * 16)()
    _cached_pj = (GLfloat * 16)()
    glGetFloatv(GL_MODELVIEW_MATRIX,  _cached_mv)
    glGetFloatv(GL_PROJECTION_MATRIX, _cached_pj)

def apply_launch(ex,ey,ez):
    for li,(lx,ly,ls,ang) in enumerate(launch_tiles):
        if abs(ex-lx)<ls and abs(ey-ly)<ls and ez<5:
            ar=math.radians(ang)
            horiz=LAUNCH_FORCE*0.6
            return math.sin(ar)*horiz, math.cos(ar)*horiz, LAUNCH_FORCE, li
    return None

def check_entity_on_slow(ex, ey, ez):
    if ez > 5: return False
    ci, rj = world_to_tile(ex, ey)
    return (ci, rj) in set(slow_tiles)

def apply_pendulum_knockback(entity_x, entity_y, entity_z, ph):
    ang_rad = math.radians(ph["angle"])
    pivot_z = 320
    tip_x = ph["px"] + math.sin(ang_rad) * ph["arm"]
    tip_y = ph["py"]
    tip_z = pivot_z - math.cos(ang_rad) * ph["arm"]

    hd = dist2(entity_x, entity_y, tip_x, tip_y)
    if hd < PENDULUM_HEAD_R + 28 and abs(entity_z - tip_z) < 60:
        ddx = entity_x - ph["px"]; ddy = entity_y - ph["py"]
        dl = math.sqrt(ddx*ddx + ddy*ddy) or 1
        speed = PENDULUM_KNOCKBACK * (1 + abs(ph["omega"]) * 0.04)
        return (ddx/dl)*speed, (ddy/dl)*speed, 36.0, True

    steps = 8
    for s in range(1, steps):
        t = s / steps
        rx = ph["px"] + math.sin(ang_rad) * ph["arm"] * t
        ry = ph["py"]
        rz = pivot_z - math.cos(ang_rad) * ph["arm"] * t
        rd = dist2(entity_x, entity_y, rx, ry)
        if rd < 22 + 28 and abs(entity_z - rz) < 45:
            ddx = entity_x - ph["px"]; ddy = entity_y - ph["py"]
            dl = math.sqrt(ddx*ddx + ddy*ddy) or 1
            speed = PENDULUM_KNOCKBACK * 0.75
            return (ddx/dl)*speed, (ddy/dl)*speed, 28.0, True

    return 0, 0, 0, False

def spinning_hammer_knockback(entity_x, entity_y, entity_z, h):
    hr = math.radians(h["angle"])
    arm = h["arm"]
    tip_x = h["cx"] + math.cos(hr)*arm
    tip_y = h["cy"] + math.sin(hr)*arm
    if dist2(entity_x, entity_y, tip_x, tip_y) < 68 and entity_z < 145:
        ddx = entity_x - h["cx"]; ddy = entity_y - h["cy"]
        dl = math.sqrt(ddx*ddx + ddy*ddy) or 1
        return (ddx/dl)*52, (ddy/dl)*52, 36.0, True
    steps = 8
    for s in range(1, steps):
        t = s / steps
        hx = h["cx"] + math.cos(hr)*arm*t
        hy = h["cy"] + math.sin(hr)*arm*t
        if dist2(entity_x, entity_y, hx, hy) < 22 and entity_z < 145:
            ddx = entity_x - h["cx"]; ddy = entity_y - h["cy"]
            dl = math.sqrt(ddx*ddx + ddy*ddy) or 1
            return (ddx/dl)*38, (ddy/dl)*38, 28.0, True
    return 0, 0, 0, False

def get_hard_floor(entity_x, entity_y, entity_z, entity_layer):
    fz = layer_floor_z(entity_layer)
    ax = layer_arena_x(entity_layer)
    ay = layer_arena_y(entity_layer)
    if abs(entity_x) > ax or abs(entity_y) > ay:
        return fz, True

    ci, rj = world_to_tile(entity_x, entity_y, entity_layer)
    vt_set = vanish_tile_set_layers[entity_layer]
    if (ci, rj) not in vt_set:
        return fz, False   
    for vt in vanish_tiles_layers[entity_layer]:
        if vt["ci"] == ci and vt["rj"] == rj:
            return fz, (vt["state"] == "gone")

    return fz, False

def update_ai():
    global player_x, player_y, finish_rankings

    for ai in ai_players:
        if not ai["alive"] or ai["finished"] or ai["dead"]: continue

        ai["vel_z"] += GRAVITY
        ai["z"]     += ai["vel_z"]

        if current_level == LEVEL_HARD:
            layer = ai.get("layer", 0)
            fz, is_over_void = get_hard_floor(ai["x"], ai["y"], ai["z"], layer)

            # Land on floor
            if ai["z"] <= fz and not is_over_void:
                ai["z"] = fz; ai["vel_z"] = 0; ai["on_ground"] = True
            if is_over_void and ai["z"] < fz - 20:
                next_layer = layer + 1
                if next_layer < LAYER_COUNT:
                    if is_within_layer(ai["x"], ai["y"], next_layer):
                        ai["layer"] = next_layer
                    else:
                        ai["dead"] = True; continue
                else:
                    ai["dead"] = True; continue

            # True void death
            if ai["z"] < layer_floor_z(LAYER_COUNT-1) - 600:
                ai["dead"] = True; continue

        else:
            # Normal mode
            if ai["z"] <= 0:
                ai["z"] = 0; ai["vel_z"] = 0; ai["on_ground"] = True
            if ai["z"] < -800:
                ai["dead"] = True; continue

        ai["on_slow"] = check_entity_on_slow(ai["x"], ai["y"], ai["z"])
        eff_speed = ai["speed"] * (SLOW_FACTOR if ai["on_slow"] else 1.0)

        if current_level == LEVEL_HARD:
            if "tgt_x" not in ai or random.random() < 0.04:
                ax2 = layer_arena_x(ai.get("layer",0))
                ay2 = layer_arena_y(ai.get("layer",0))
                ai["tgt_x"] = clamp(ai["x"] + random.uniform(-350, 350), -ax2+50, ax2-50)
                ai["tgt_y"] = clamp(ai["y"] + random.uniform(-350, 350), -ay2+50, ay2-50)

            dx = ai["tgt_x"] - ai["x"]
            dy = ai["tgt_y"] - ai["y"]

            fz2, iov = get_hard_floor(ai["x"], ai["y"], ai["z"], ai.get("layer",0))
            if iov and ai["on_ground"]:
                ai["vel_z"] = JUMP_SPEED * 0.9
                ai["on_ground"] = False
        else:
            tx = random.uniform(-120, 120)
            dx = tx - ai["x"]; dy = FINISH_Y - ai["y"]

        d = math.sqrt(dx*dx + dy*dy) or 1
        ai["x"] += (dx/d)*eff_speed
        ai["y"] += (dy/d)*eff_speed
        ai["angle"] = math.degrees(math.atan2(-dx, dy))

        ai["x"] += ai["vel_x"]; ai["y"] += ai["vel_y"]
        ai["vel_x"] *= KNOCKBACK_DECAY; ai["vel_y"] *= KNOCKBACK_DECAY

        if current_level != LEVEL_HARD:
            ai["x"] = clamp(ai["x"], -ARENA_X+30, ARENA_X-30)
            ai["y"] = clamp(ai["y"], -ARENA_Y+30, ARENA_Y-30)
            if out_of_arena(ai["x"], ai["y"]):
                ai["x"] = random.uniform(-200,200)
                ai["y"] = START_Y + random.uniform(-50,50)
                ai["z"] = 0; ai["vel_x"]=ai["vel_y"]=ai["vel_z"]=0
        else:
            ax3 = layer_arena_x(ai.get("layer",0))
            ay3 = layer_arena_y(ai.get("layer",0))
            ai["x"] = clamp(ai["x"], -ax3+30, ax3-30)
            ai["y"] = clamp(ai["y"], -ay3+30, ay3-30)

        res = apply_launch(ai["x"], ai["y"], ai["z"])
        if res:
            vx,vy,vz,li = res
            ai["vel_x"]=vx; ai["vel_y"]=vy; ai["vel_z"]=vz; ai["on_ground"]=False

        for h in spinning_hammers:
            vx,vy,vz,hit = spinning_hammer_knockback(ai["x"],ai["y"],ai["z"],h)
            if hit:
                ai["vel_x"]=vx; ai["vel_y"]=vy; ai["vel_z"]=vz; ai["on_ground"]=False; break

        for ph in pendulum_hammers:
            vx,vy,vz,hit = apply_pendulum_knockback(ai["x"],ai["y"],ai["z"],ph)
            if hit:
                ai["vel_x"]=vx; ai["vel_y"]=vy; ai["vel_z"]=vz; ai["on_ground"]=False; break

        for bd in breakable_doors:
            if not bd["alive"]: continue
            if (abs(ai["y"] - bd["cy"]) < BDOOR_THICKNESS + AI_RADIUS + 60 and
                    abs(ai["x"] - bd["cx"]) < ARENA_X and ai["z"] < BDOOR_HEIGHT):
                if ai["on_ground"]:
                    ai["vel_z"] = JUMP_SPEED * 1.1; ai["on_ground"] = False
                if abs(ai["y"] - bd["cy"]) < BDOOR_THICKNESS + AI_RADIUS:
                    ai["y"] = (bd["cy"] - BDOOR_THICKNESS - AI_RADIUS - 1
                               if ai["y"] < bd["cy"]
                               else bd["cy"] + BDOOR_THICKNESS + AI_RADIUS + 1)
                    ai["vel_y"] = 0

        for other in ai_players:
            if other is ai or not other["alive"] or other["dead"] or other["finished"]: continue
            d_o = dist2(ai["x"],ai["y"],other["x"],other["y"])
            if 0 < d_o < AI_RADIUS*2:
                ov = AI_RADIUS*2-d_o
                ddx = ai["x"]-other["x"]; ddy = ai["y"]-other["y"]
                dl = math.sqrt(ddx*ddx+ddy*ddy) or 1
                ai["x"] += (ddx/dl)*ov*0.5; ai["y"] += (ddy/dl)*ov*0.5
                other["x"] -= (ddx/dl)*ov*0.5; other["y"] -= (ddy/dl)*ov*0.5

        if not player_dead:
            dp = dist2(ai["x"],ai["y"],player_x,player_y)
            min_sep = AI_RADIUS + 30
            if 0 < dp < min_sep:
                ddx = player_x - ai["x"]; ddy = player_y - ai["y"]
                dl = math.sqrt(ddx*ddx + ddy*ddy) or 1
                ov = min_sep - dp
                player_x += (ddx/dl)*ov*0.5; player_y += (ddy/dl)*ov*0.5
                ai["x"]  -= (ddx/dl)*ov*0.5; ai["y"]  -= (ddy/dl)*ov*0.5
                player_x = clamp(player_x, -ARENA_X+24, ARENA_X-24)
                player_y = clamp(player_y, -ARENA_Y+24, ARENA_Y-24)
                ai["x"]  = clamp(ai["x"], -ARENA_X+30, ARENA_X-30)
                ai["y"]  = clamp(ai["y"], -ARENA_Y+30, ARENA_Y-30)

        if current_level != LEVEL_HARD:
            if dist2(ai["x"],ai["y"],FINISH_X,FINISH_Y) < FINISH_R:
                ai["finished"] = True
                if ai["name"] not in finish_rankings:
                    finish_rankings.append(ai["name"])

def update_vanish_tiles(dt):
    """
    Tick all vanish tiles across all 3 layers.
    A tile transitions: solid -> cracking -> gone.
    Anyone standing on it (z close to floor_z) starts the crack timer.
    """
    for layer in range(LAYER_COUNT):
        fz = layer_floor_z(layer)
        standing_on = set()
        if not player_dead and player_layer == layer and abs(player_z - fz) <= 8:
            standing_on.add(world_to_tile(player_x, player_y, layer))
        for ai in ai_players:
            if (ai["alive"] and not ai["dead"] and
                    ai.get("layer", 0) == layer and abs(ai["z"] - fz) <= 8):
                standing_on.add(world_to_tile(ai["x"], ai["y"], layer))

        for vt in vanish_tiles_layers[layer]:
            if vt["state"] == "gone":
                continue
            key = (vt["ci"], vt["rj"])
            if key in standing_on:
                vt["timer"] += dt
                if vt["state"] == "solid":
                    vt["state"] = "cracking"
            if vt["timer"] >= vt["grace"]:
                vt["state"] = "gone"
                vt["timer"] = 0.0

def update():
    global player_x,player_y,player_z,player_angle
    global player_vel_x,player_vel_y,player_vel_z
    global player_health,player_score,game_state
    global is_on_ground,bullet_list,enemy_list,tile_flash
    global jump_requested,player_dead,damage_cooldown
    global player_on_slow, last_time
    global score_events, finish_rankings, player_finished
    global knockback_flash_timer, player_layer

    if game_state not in (STATE_RUNNING,):
        if player_dead: update_ai()
        now = time.time(); dt = min(now - last_time, 0.1); last_time = now
        if knockback_flash_timer > 0: knockback_flash_timer = max(0, knockback_flash_timer - dt)
        score_events[:] = [e for e in score_events if e[3] > 0]
        for ev in score_events: ev[3] -= dt
        return

    if player_dead:
        now = time.time(); dt = min(now - last_time, 0.1); last_time = now
        if knockback_flash_timer > 0: knockback_flash_timer = max(0, knockback_flash_timer - dt)
        score_events[:] = [e for e in score_events if e[3] > 0]
        for ev in score_events: ev[3] -= dt
        update_ai(); return

    now  = time.time()
    dt   = min(now - last_time, 0.1)
    last_time = now

    if knockback_flash_timer > 0: knockback_flash_timer = max(0, knockback_flash_timer - dt)
    score_events[:] = [e for e in score_events if e[3] > 0]
    for ev in score_events: ev[3] -= dt
    for k in list(keys_pressed.keys()):
        keys_pressed[k] -= 1
        if keys_pressed[k] <= 0:
            del keys_pressed[k]

    if damage_cooldown > 0: damage_cooldown -= 1

    def take_damage(amount, cause=""):
        global player_health,game_state,player_dead,damage_cooldown,knockback_flash_timer
        if damage_cooldown > 0: return
        player_health -= amount; damage_cooldown = DAMAGE_CD_FRAMES
        knockback_flash_timer = KNOCKBACK_FLASH_DUR
        if cause:
            add_score_event(f"-{amount} {cause}", player_x, player_y, 1.0, 0.2, 0.2)
        if player_health <= 0:
            player_health = 0; player_dead = True; game_state = STATE_GAMEOVER

    player_on_slow = check_entity_on_slow(player_x, player_y, player_z)
    eff_speed = player_speed * (SLOW_FACTOR if player_on_slow else 1.0)

    rad = math.radians(player_angle)
    if b'w' in keys_pressed:
        player_x -= math.sin(rad)*eff_speed; player_y += math.cos(rad)*eff_speed
    if b's' in keys_pressed:
        player_x += math.sin(rad)*eff_speed; player_y -= math.cos(rad)*eff_speed
    if b'a' in keys_pressed: player_angle += 4.5
    if b'd' in keys_pressed: player_angle -= 4.5

    if jump_requested and is_on_ground:
        player_vel_z = JUMP_SPEED; is_on_ground = False; jump_requested = False

    player_vel_z += GRAVITY
    player_z+=player_vel_z

    # Hard mode floor 
    if current_level == LEVEL_HARD:
        fz, is_over_void = get_hard_floor(player_x, player_y, player_z, player_layer)

        # Land on current layer floor
        if player_z <= fz and not is_over_void:
            player_z = fz; player_vel_z = 0; is_on_ground = True; jump_requested = False

        # Falling below this layer's floor level — try next layer
        if is_over_void and player_z < fz - 20:
            next_layer = player_layer + 1
            if next_layer < LAYER_COUNT:
                if is_within_layer(player_x, player_y, next_layer):
                    player_layer = next_layer
                    add_score_event(f"LAYER {player_layer+1}!", player_x, player_y, 1.0, 0.5, 0.0)
                else:
                    # Outside bounds of next layer — eliminated
                    take_damage(999, "VOID!")
            else:
                # Fell through all layers
                take_damage(999, "VOID!")

        # True death if fallen way below last layer
        if player_z < layer_floor_z(LAYER_COUNT-1) - 600:
            take_damage(999, "VOID!")

        # Arena bounds per layer (can't walk off edge)
        ax_l = layer_arena_x(player_layer)
        ay_l = layer_arena_y(player_layer)
        player_x = clamp(player_x, -ax_l+24, ax_l-24)
        player_y = clamp(player_y, -ay_l+24, ay_l-24)

    else:
        # Normal floor
        if player_z <= 0:
            player_z = 0; player_vel_z = 0; is_on_ground = True; jump_requested = False

        if player_z < -800:
            respawn_player(); take_damage(15, "FALL")

        if out_of_arena(player_x, player_y):
            respawn_player(); take_damage(15, "FALL")
        else:
            player_x = clamp(player_x, -ARENA_X+24, ARENA_X-24)
            player_y = clamp(player_y, -ARENA_Y+24, ARENA_Y-24)

    player_x += player_vel_x; player_y += player_vel_y
    player_vel_x *= KNOCKBACK_DECAY; player_vel_y *= KNOCKBACK_DECAY

    # Vanishing tiles (hard mode)
    if current_level == LEVEL_HARD:
        update_vanish_tiles(dt)

    # Launch pads─
    res = apply_launch(player_x, player_y, player_z)
    if res:
        vx,vy,vz,li = res
        player_vel_x=vx; player_vel_y=vy; player_vel_z=vz
        is_on_ground=False; tile_flash[li]=14
        player_score -= 2
        add_score_event("-2 LAUNCH", player_x, player_y, 1.0, 0.6, 0.0)

    for k in list(tile_flash.keys()):
        tile_flash[k] -= 1
        if tile_flash[k] <= 0: del tile_flash[k]

    # Breakable doors 
    for bd in breakable_doors:
        if not bd["alive"]: continue
        if (abs(player_x-bd["cx"]) < ARENA_X and
                abs(player_y-bd["cy"]) < BDOOR_THICKNESS+26 and
                player_z < BDOOR_HEIGHT):
            player_y = (bd["cy"]-BDOOR_THICKNESS-27 if player_y < bd["cy"]
                        else bd["cy"]+BDOOR_THICKNESS+27)
            player_vel_y = 0; take_damage(10, "DOOR")

    if sword_active:
        sr = math.radians(player_angle)
        stx = player_x - math.sin(sr)*110; sty = player_y + math.cos(sr)*110
        for bd in breakable_doors:
            if bd["alive"] and abs(sty-bd["cy"]) < 140 and abs(stx-bd["cx"]) < ARENA_X:
                bd["alive"] = False; player_score += 15
                add_score_event("+15 DOOR!", stx, sty, 0.2, 1.0, 0.4)

    # Sliding doors 
    for d in sliding_doors:
        d["offset"] += d["dir"]*d["speed"]
        if d["offset"] > d["half"] or d["offset"] < -d["half"]: d["dir"] *= -1
        door_x = d["cx"]+d["offset"]; door_y = d["cy"]
        w = d["half"]; h2 = 33
        if abs(player_x-door_x) < w+24 and abs(player_y-door_y) < h2+24 and player_z < 130:
            ddx = player_x-door_x; ddy = player_y-door_y
            dl = math.sqrt(ddx*ddx+ddy*ddy) or 1
            push = (w+24)-dl
            player_x += (ddx/dl)*push*0.5; player_y += (ddy/dl)*push*0.5
            player_vel_x = (ddx/dl)*14; player_vel_y = (ddy/dl)*14
            player_vel_z = 7; is_on_ground = False; take_damage(10, "DOOR")

    # Spinning hammers 
    for h in spinning_hammers:
        h["angle"] = (h["angle"] + h["speed"]) % 360
        vx,vy,vz,hit = spinning_hammer_knockback(player_x, player_y, player_z, h)
        if hit:
            player_vel_x = vx; player_vel_y = vy; player_vel_z = vz
            is_on_ground = False; take_damage(10, "HAMMER")

    # Floating hammers 
    for fh in float_hammers:
        fh["cx"] += fh["dir"]*fh["speed"]
        if fh["cx"] > fh["x_max"] or fh["cx"] < fh["x_min"]: fh["dir"] *= -1
        z_lo = fh["cz"]-34; z_hi = fh["cz"]+34
        if (abs(player_x-fh["cx"]) < 145 and abs(player_y-fh["cy"]) < 68 and
                player_z+80 > z_lo and player_z < z_hi):
            player_vel_x = (player_x-fh["cx"])/10*16
            player_vel_z = 26; is_on_ground = False; take_damage(10, "HAMMER")

    #Pendulum hammers 
    for ph in pendulum_hammers:
        ph["omega"] += -(9.0/ph["arm"]) * math.sin(math.radians(ph["angle"])) * ph["speed"]
        ph["omega"] *= 0.995
        ph["angle"] += ph["omega"]
        ma = ph["max_angle"]
        if ph["angle"] >  ma: ph["angle"] =  ma; ph["omega"] *= -0.9
        if ph["angle"] < -ma: ph["angle"] = -ma; ph["omega"] *= -0.9

        vx,vy,vz,hit = apply_pendulum_knockback(player_x, player_y, player_z, ph)
        if hit:
            player_vel_x = vx; player_vel_y = vy; player_vel_z = vz
            is_on_ground = False; take_damage(15, "PENDULUM")

    #Enemies
    es = get_enemy_speed()
    for e in enemy_list:
        if not e[2]: continue
        ddx = player_x-e[0]; ddy = player_y-e[1]
        dl  = math.sqrt(ddx*ddx+ddy*ddy) or 1
        e[0] += (ddx/dl)*es; e[1] += (ddy/dl)*es

        if dl < ENEMY_RADIUS + 30:
            ov = (ENEMY_RADIUS + 30) - dl
            push_x = (ddx/dl) * (ov + 1); push_y = (ddy/dl) * (ov + 1)
            player_x += push_x; player_y += push_y
            player_vel_x = (ddx/dl) * 22; player_vel_y = (ddy/dl) * 22
            player_vel_z = 8; is_on_ground = False; take_damage(20, "ENEMY")
            player_x = clamp(player_x, -ARENA_X+24, ARENA_X-24)
            player_y = clamp(player_y, -ARENA_Y+24, ARENA_Y-24)

    #Bullets
    new_b = []
    for b in bullet_list:
        b[0] += b[2]; b[1] += b[3]; b[4] -= 1
        if b[4] <= 0 or abs(b[0]) > ARENA_X or abs(b[1]) > ARENA_Y: continue
        hit = False
        for e in enemy_list:
            if e[2] and dist2(b[0],b[1],e[0],e[1]) < ENEMY_RADIUS+14:
                e[2] = False; player_score += 10
                add_score_event("+10 KILL!", b[0], b[1], 0.2, 1.0, 0.3)
                hit = True; break
        if not hit: new_b.append(b)
    bullet_list = new_b

    n_needed = get_num_enemies()
    alive    = sum(1 for e in enemy_list if e[2])
    while alive < n_needed:
        ex = random.uniform(-ARENA_X+60, ARENA_X-60)
        ey = random.uniform(-ARENA_Y+60, ARENA_Y-60)
        while dist2(ex,ey,player_x,player_y) < 400:
            ex = random.uniform(-ARENA_X+60, ARENA_X-60)
            ey = random.uniform(-ARENA_Y+60, ARENA_Y-60)
        enemy_list.append([ex,ey,True]); alive += 1

    update_ai()

    if current_level == LEVEL_HARD:
        alive_ais = sum(1 for ai in ai_players if not ai["dead"])
        if alive_ais == 0 and not player_dead and game_state == STATE_RUNNING:
            player_finished = True
            player_score += 500
            game_state = STATE_LEVEL_DONE
    else:
        if not player_finished and dist2(player_x,player_y,FINISH_X,FINISH_Y) < FINISH_R:
            player_finished = True
            if "You" not in finish_rankings:
                finish_rankings.append("You")
            rank = finish_rankings.index("You") + 1
            rank_bonus = max(0, (NUM_AI+2-rank)*50)
            elapsed = time.time() - game_start_time
            time_bonus = max(0, int(300 - elapsed*2))
            player_score += 200 + rank_bonus + time_bonus
            add_score_event(f"+{200+rank_bonus+time_bonus} FINISH!",
                            FINISH_X, FINISH_Y, 1.0, 0.9, 0.0)
            game_state = STATE_LEVEL_DONE

KEY_FRESH = 8

def keyDown(key,x,y):
    global camera_mode,jump_requested,game_state
    k=key.lower(); keys_pressed[k] = KEY_FRESH   # refresh/add
    if k==b'r': reset_game(LEVEL_EASY); return
    if game_state==STATE_LEVEL_DONE:
        if k==b'm' and current_level==LEVEL_EASY:   reset_game(LEVEL_MEDIUM); return
        if k==b'h' and current_level in (LEVEL_EASY,LEVEL_MEDIUM): reset_game(LEVEL_HARD); return
        return
    if game_state!=STATE_RUNNING: return
    if k==b'c': camera_mode=(camera_mode+1)%3
    if k==b' ': jump_requested=True

def keyUp(key,x,y): pass   

def specialKeyListener(key, x, y):
    global camera_angle, camera_height

    if key == GLUT_KEY_LEFT:
        camera_angle += 0.5

    elif key == GLUT_KEY_RIGHT:
        camera_angle -= 0.5

    elif key == GLUT_KEY_UP:
        camera_height += 20

    elif key == GLUT_KEY_DOWN:
        camera_height -= 20

def mouse(button,state,mx,my):
    global sword_active
    if game_state!=STATE_RUNNING or player_dead: return
    if button==GLUT_LEFT_BUTTON and state==GLUT_DOWN:
        rad=math.radians(player_angle)
        bx=player_x-math.sin(rad)*55; by=player_y+math.cos(rad)*55
        bullet_list.append([bx,by,-math.sin(rad)*BULLET_SPEED,math.cos(rad)*BULLET_SPEED,BULLET_LIFE])
    if button==GLUT_RIGHT_BUTTON and state==GLUT_DOWN:
        sword_active=not sword_active

def showScreen():
    glClearColor(0.08, 0.12, 0.28, 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, WIN_W, WIN_H)
    
    setupCamera()
    
    if player_dead:
        draw_death_scene()
        draw_ai_players()
    else:
        draw_floor()
        draw_walls()
        if current_level != LEVEL_HARD:
            draw_launch_tiles()
        draw_start_line()
        draw_finish_line()
        draw_sliding_doors()
        draw_spinning_hammers()
        draw_float_hammers()
        draw_pendulum_hammers()
        draw_breakable_doors()
        draw_enemies()
        draw_bullets()
        draw_player()
        draw_ai_players()
        draw_score_events()
        
    draw_knockback_overlay()
    draw_comment()
    glutSwapBuffers()

def idle():
    update()
    glutPostRedisplay()

def main():
 
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIN_W, WIN_H)
    glutInitWindowPosition(50, 50)
    glutCreateWindow(b"Fall Guys SPedi")
    glEnable(GL_DEPTH_TEST)

    reset_game(LEVEL_EASY)

    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyDown)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouse)
    glutIdleFunc(idle)
    
    glutMainLoop()

if __name__ == "__main__":
    main()
    main()