# Imports
import copy
import math
import time

import pyglet
import json
import random

# Meta
plat_version = "0.5.0-7"

# Cell data
cells = []
grid_width = 100
grid_height = 100

grid_offset = 200


def init_cells():
    for i in range(0, grid_width * grid_height):
        cells.append([0, 0, 0])


materials = [
    "Air",
    "Sand",
    "Water",
    "Iron",
    "Mud",
    "Rust",
    "Acid",
    "Sodium",
    "Caesium",
    "Lava",
    "Stone",
    "Glass",
    "Brick",
    "Ice",
    "Hot Water",
    "Salt",
    "Saltwater"
]

hidden_materials = [
    14
]

# Physics constants
sinks_in_water = [
    4,  # Mud
    10  # Stone
]

# Constants
blocksize = 8
sim_rate = 0.01

# Globals
global mouse_down, mouse_x, mouse_y, mouse_erase
mouse_down = False
mouse_x = 0
mouse_y = 0
mouse_erase = False

global current_mat, mat_view_pointer
current_mat = 1
mat_view_pointer = 0

global time_delta, old_time
time_delta = 0
old_time = 0
# Init colour data
colour_data = json.load(open("colourtable.json"))

# Init functions
init_cells()

# Init window
win = pyglet.window.Window(caption=f"2DPhysSim {plat_version}", width=(blocksize * grid_width) + grid_offset,
                           height=blocksize * grid_height, vsync=True, resizable=False, visible=False)
pyglet.font.add_directory("fonts")

# Init all visual cells
visual_cells = []
all_colors = []
cell_batch = pyglet.graphics.Batch()
for x_init in range(0, grid_width):
    for y_init in range(0, grid_height):
        visual_cells.append(
            pyglet.shapes.Rectangle(
                x=x_init * blocksize + grid_offset,
                y=y_init * blocksize,
                width=blocksize,
                height=blocksize,
                color=(0, 0, 0),
                batch=cell_batch
            )
        )
        all_colors.append([0, 0, 0])

# Init material view objects
mat_batch = pyglet.graphics.Batch()
mat_view_bg = pyglet.shapes.Rectangle(
    x=0,
    y=0,
    width=grid_offset,
    height=blocksize * grid_height,
    color=(20, 20, 20),
    batch=mat_batch
)

mat_list = []
mat_height = 40
mat_pad = 5

mat_selection = pyglet.shapes.Rectangle(
    x=0,
    y=0,
    width=250,
    height=mat_height,
    color=(50, 50, 50),
    batch=mat_batch
)

for m in range(0, len(materials)):
    mat_list.append(
        pyglet.shapes.Rectangle(
            x=mat_pad,
            y=blocksize * grid_height - (m + 1) * mat_height + mat_pad,
            width=mat_height - mat_pad * 2,
            height=mat_height - mat_pad * 2,
            color=colour_data["colours"][m][0],
            batch=mat_batch
        )
    )
    mat_list.append(
        pyglet.text.Label(
            text=materials[m],
            font_name="Lexend",
            x=mat_height,
            y=blocksize * grid_height - (m + 1) * mat_height + mat_pad,
            font_size=16,
            batch=mat_batch
        )
    )

# Debug info
debug_FPS = pyglet.window.FPSDisplay(win)


# Functions
def get_cell_index(x, y):
    end_x = min(max(x, 0), grid_width - 1)
    end_y = min(max(y, 0), grid_height - 1)
    return grid_width * end_x + end_y


def update_visuals():
    for i in range(0, len(cells)):
        this_col_data = colour_data["colours"][cells[i][0]][cells[i][1]]
        if all_colors[i] != this_col_data:
            visual_cells[i].color = this_col_data
            all_colors[i] = this_col_data


def update_mouse_px():
    used_x = int((mouse_x - grid_offset) // blocksize)
    used_y = int(mouse_y // blocksize)
    if used_x >= 0:
        set_px(used_x, used_y, current_mat)


def erase_mouse_px():
    used_x = int((mouse_x - grid_offset) // blocksize)
    used_y = int(mouse_y // blocksize)
    if used_x >= 0:
        set_px(used_x, used_y, 0)


def mouse_pick():
    used_x = int((mouse_x - grid_offset) // blocksize)
    used_y = int(mouse_y // blocksize)
    if used_x >= 0:
        globals()["current_mat"] = cells[get_cell_index(used_x, used_y)][0]
        update_selection()


def set_px(x, y, mat):
    cells[get_cell_index(x, y)] = [mat, random.randint(0, len(colour_data["colours"][mat]) - 1), 0]


def update_current_px(x, y):
    globals()["mouse_x"] = min(max(0, x), win.width - 1)
    globals()["mouse_y"] = min(max(0, y), win.height)

    if mouse_x > win.width - 1:
        globals()["mouse_x"] = win.width - 1
    elif mouse_x < 0:
        globals()["mouse_x"] = 0

    if mouse_y > win.height:
        globals()["mouse_y"] = win.height
    elif mouse_y < 0:
        globals()["mouse_y"] = 0

    if mouse_down:
        update_mouse_px()


def update_selection():
    mat_selection.y = blocksize * grid_height - (current_mat + 1) * mat_height


def sand_physics(x, y, this_cell):
    if y != 0 and cells[get_cell_index(x, y - 1)][0] == 0:
        # Move down into air
        cells[get_cell_index(x, y - 1)] = copy.deepcopy(this_cell)
        cells[get_cell_index(x, y)] = [0, 0, 0]
        return True
    elif y > 0:
        # Try and move down and to the left or right
        if random.getrandbits(1):
            # Try left, then right
            if x > 0 and cells[get_cell_index(x - 1, y - 1)][0] == 0 and cells[get_cell_index(x - 1, y)][0] == 0:
                cells[get_cell_index(x - 1, y - 1)] = copy.deepcopy(this_cell)
                cells[get_cell_index(x, y)] = [0, 0, 0]
                return True
            elif x < grid_width - 1 and cells[get_cell_index(x + 1, y - 1)][0] == 0 and cells[get_cell_index(x + 1, y)][
                0] == 0:
                cells[get_cell_index(x + 1, y - 1)] = copy.deepcopy(this_cell)
                cells[get_cell_index(x, y)] = [0, 0, 0]
                return True
        else:
            # Try right, then left
            if x < grid_width - 1 and cells[get_cell_index(x + 1, y - 1)][0] == 0 and cells[get_cell_index(x + 1, y)][
                0] == 0:
                cells[get_cell_index(x + 1, y - 1)] = copy.deepcopy(this_cell)
                cells[get_cell_index(x, y)] = [0, 0, 0]
                return True
            elif x > 0 and cells[get_cell_index(x - 1, y - 1)][0] == 0 and cells[get_cell_index(x - 1, y)][0] == 0:
                cells[get_cell_index(x - 1, y - 1)] = copy.deepcopy(this_cell)
                cells[get_cell_index(x, y)] = [0, 0, 0]
                return True
    return False


def fluid_physics(x, y, this_cell):
    if y != 0 and cells[get_cell_index(x, y - 1)][0] == 0:
        # Move down into air
        cells[get_cell_index(x, y - 1)] = copy.deepcopy(this_cell)
        cells[get_cell_index(x, y)] = [0, 0, 0]
        return True
    elif y > 0:
        # Try and move down and to the left or right
        if random.getrandbits(1):
            # Try left, then right
            if x > 0 and cells[get_cell_index(x - 1, y - 1)][0] == 0 and cells[get_cell_index(x - 1, y)][0] == 0:
                cells[get_cell_index(x - 1, y - 1)] = copy.deepcopy(this_cell)
                cells[get_cell_index(x, y)] = [0, 0, 0]
                return True
            elif x < grid_width - 1 and cells[get_cell_index(x + 1, y - 1)][0] == 0 and cells[get_cell_index(x + 1, y)][
                0] == 0:
                cells[get_cell_index(x + 1, y - 1)] = copy.deepcopy(this_cell)
                cells[get_cell_index(x, y)] = [0, 0, 0]
                return True
        else:
            # Try right, then left
            if x < grid_width - 1 and cells[get_cell_index(x + 1, y - 1)][0] == 0 and cells[get_cell_index(x + 1, y)][
                0] == 0:
                cells[get_cell_index(x + 1, y - 1)] = copy.deepcopy(this_cell)
                cells[get_cell_index(x, y)] = [0, 0, 0]
                return True
            elif x > 0 and cells[get_cell_index(x - 1, y - 1)][0] == 0 and cells[get_cell_index(x - 1, y)][0] == 0:
                cells[get_cell_index(x - 1, y - 1)] = copy.deepcopy(this_cell)
                cells[get_cell_index(x, y)] = [0, 0, 0]
                return True
    if random.random() < 0.1:
        # Try and move right, or else left
        if x < grid_width - 1 and cells[get_cell_index(x + 1, y)][0] == 0:
            cells[get_cell_index(x + 1, y)] = copy.deepcopy(this_cell)
            cells[get_cell_index(x + 1, y)][2] = 1
            cells[get_cell_index(x, y)] = [0, 0, 0]
            return True
        elif cells[get_cell_index(x - 1, y)][0] == 0:
            cells[get_cell_index(x - 1, y)] = copy.deepcopy(this_cell)
            cells[get_cell_index(x + 1, y)][2] = 1
            cells[get_cell_index(x, y)] = [0, 0, 0]
            return True

    else:
        if x > 0 and cells[get_cell_index(x - 1, y)][0] == 0:
            cells[get_cell_index(x - 1, y)] = copy.deepcopy(this_cell)
            cells[get_cell_index(x + 1, y)][2] = 1
            cells[get_cell_index(x, y)] = [0, 0, 0]
            return True
        elif cells[get_cell_index(x + 1, y)][0] == 0:
            cells[get_cell_index(x + 1, y)] = copy.deepcopy(this_cell)
            cells[get_cell_index(x + 1, y)][2] = 1
            cells[get_cell_index(x, y)] = [0, 0, 0]
            return True
    return False


def heavy_physics(x, y, this_cell):
    if y != 0 and cells[get_cell_index(x, y - 1)][0] == 0:
        # Move down into air
        cells[get_cell_index(x, y - 1)] = copy.deepcopy(this_cell)
        cells[get_cell_index(x, y)] = [0, 0, 0]
        return True
    return False


def spread(x, y, can_spread, this_cell):
    if y > 0 and cells[get_cell_index(x, y - 1)][0] in can_spread:
        set_px(x, y - 1, this_cell[0])
    if y < grid_height - 1 and cells[get_cell_index(x, y + 1)][0] in can_spread:
        set_px(x, y + 1, this_cell[0])
    if x < grid_width - 1 and cells[get_cell_index(x + 1, y)][0] in can_spread:
        set_px(x + 1, y, this_cell[0])
    if x > 0 and cells[get_cell_index(x - 1, y)][0] in can_spread:
        set_px(x - 1, y, this_cell[0])


def absorb(x, y, mat_in, mat_out):
    for i in range(0, len(mat_in)):
        if y > 0 and cells[get_cell_index(x, y - 1)][0] == mat_in[i]:
            set_px(x, y - 1, mat_out[i])
            cells[get_cell_index(x, y)] = [0, 0, 0]
            return True
        elif y < grid_height - 1 and cells[get_cell_index(x, y + 1)][0] == mat_in[i]:
            set_px(x, y + 1, mat_out[i])
            cells[get_cell_index(x, y)] = [0, 0, 0]
            return True
        elif x < grid_width - 1 and cells[get_cell_index(x + 1, y)][0] == mat_in[i]:
            set_px(x + 1, y, mat_out[i])
            cells[get_cell_index(x, y)] = [0, 0, 0]
            return True
        elif x > 0 and cells[get_cell_index(x - 1, y)][0] == mat_in[i]:
            set_px(x - 1, y, mat_out[i])
            cells[get_cell_index(x, y)] = [0, 0, 0]
            return True
    return False


def change(x, y, mat_in, mat_out):
    for i in range(0, len(mat_in)):
        if y > 0 and cells[get_cell_index(x, y - 1)][0] == mat_in[i]:
            set_px(x, y - 1, mat_out[i])
            return True
        elif y < grid_height - 1 and cells[get_cell_index(x, y + 1)][0] == mat_in[i]:
            set_px(x, y + 1, mat_out[i])
            return True
        elif x < grid_width - 1 and cells[get_cell_index(x + 1, y)][0] == mat_in[i]:
            set_px(x + 1, y, mat_out[i])
            return True
        elif x > 0 and cells[get_cell_index(x - 1, y)][0] == mat_in[i]:
            set_px(x - 1, y, mat_out[i])
            return True
    return False


def check_swaps(x, y, swap_list, this_cell):
    if y < grid_height - 1 and (cells[get_cell_index(x, y + 1)][0] in swap_list):
        old_this_cell = copy.deepcopy(this_cell)
        cells[get_cell_index(x, y)] = copy.deepcopy(cells[get_cell_index(x, y + 1)])
        cells[get_cell_index(x, y + 1)] = copy.deepcopy(old_this_cell)
        return True
    return False


def check_fluid_swaps(x, y, swap_list, this_cell):
    if y < grid_height - 1 and (cells[get_cell_index(x, y + 1)][0] in swap_list):
        # Check above
        old_this_cell = copy.deepcopy(this_cell)
        cells[get_cell_index(x, y)] = copy.deepcopy(cells[get_cell_index(x, y + 1)])
        cells[get_cell_index(x, y + 1)] = copy.deepcopy(old_this_cell)
        return True
    if y < grid_height - 1 and x > 0 and (cells[get_cell_index(x - 1, y + 1)][0] in swap_list):
        # Check above left
        old_this_cell = copy.deepcopy(this_cell)
        cells[get_cell_index(x, y)] = copy.deepcopy(cells[get_cell_index(x - 1, y + 1)])
        cells[get_cell_index(x - 1, y + 1)] = copy.deepcopy(old_this_cell)
        return True
    if y < grid_height - 1 and x < grid_width - 1 and (cells[get_cell_index(x + 1, y + 1)][0] in swap_list):
        # Check above right
        old_this_cell = copy.deepcopy(this_cell)
        cells[get_cell_index(x, y)] = copy.deepcopy(cells[get_cell_index(x + 1, y + 1)])
        cells[get_cell_index(x + 1, y + 1)] = copy.deepcopy(old_this_cell)
        return True

    # Check neighbouring cells
    if random.getrandbits(1):
        if y > 0 and x < grid_width - 1 and (cells[get_cell_index(x, y - 1)][0] in swap_list) and \
                cells[get_cell_index(x + 1, y - 1)][0] == this_cell[0]:
            old_this_cell = copy.deepcopy(cells[get_cell_index(x, y - 1)])
            cells[get_cell_index(x, y - 1)] = copy.deepcopy(cells[get_cell_index(x + 1, y - 1)])
            cells[get_cell_index(x + 1, y - 1)] = copy.deepcopy(old_this_cell)
    else:
        if y > 0 and x > 0 and (cells[get_cell_index(x, y - 1)][0] in swap_list) and \
                cells[get_cell_index(x - 1, y - 1)][0] == this_cell[0]:
            old_this_cell = copy.deepcopy(cells[get_cell_index(x, y - 1)])
            cells[get_cell_index(x, y - 1)] = copy.deepcopy(cells[get_cell_index(x - 1, y - 1)])
            cells[get_cell_index(x - 1, y - 1)] = copy.deepcopy(old_this_cell)
    return False


def explode_on_contact(x, y, mat_in, radius):
    for i in range(0, len(mat_in)):
        if y > 0 and cells[get_cell_index(x, y - 1)][0] in mat_in:
            explosion(x, y, radius)
            return True
        elif y < grid_height - 1 and cells[get_cell_index(x, y + 1)][0] in mat_in:
            explosion(x, y, radius)
            return True
        elif x < grid_width - 1 and cells[get_cell_index(x + 1, y)][0] in mat_in:
            explosion(x, y, radius)
            return True
        elif x > 0 and cells[get_cell_index(x - 1, y)][0] in mat_in:
            explosion(x, y, radius)
            return True
    return False


def explosion(x, y, radius):
    for x_ex in range(0, grid_width):
        for y_ex in range(0, grid_height):
            if radius ** 2 - (x_ex - x) ** 2 >= 0 and radius ** 2 - (y_ex - y) ** 2 >= 0:
                if abs(x_ex - x) < math.sqrt(radius ** 2 - (y_ex - y) ** 2) and abs(y_ex - y) < math.sqrt(
                        radius ** 2 - (x_ex - x) ** 2):
                    cells[get_cell_index(x_ex, y_ex)] = [0, 0, 0]


def update_physics():
    for x in range(0, grid_width):
        for y in range(0, grid_width):
            this_cell = cells[get_cell_index(x, y)]
            if this_cell[2] > 0:
                cells[get_cell_index(x, y)][2] -= 1
                continue
            match this_cell[0]:
                case 0:
                    # Air
                    continue
                case 1:
                    # Sand
                    sand_physics(x, y, this_cell)
                case 2:
                    # Water

                    # Mud transformation
                    if absorb(x, y, [1, 15], [4, 16]):
                        continue

                    # Rust transformation
                    change(x, y, [3], [5])

                    # Sinking
                    if check_swaps(x, y, sinks_in_water, this_cell):
                        continue

                    fluid_physics(x, y, this_cell)
                case 3:
                    # Iron
                    continue
                case 4:
                    # Mud
                    sand_physics(x, y, this_cell)
                case 5:
                    # Rust
                    continue
                case 6:
                    # Acid
                    # Destroy metals
                    if absorb(x, y, [3, 5, 7, 8], [0, 16, 0, 0]):
                        continue

                    # Sinking
                    if check_swaps(x, y, sinks_in_water, this_cell):
                        continue

                    fluid_physics(x, y, this_cell)
                case 7:
                    # Sodium
                    if explode_on_contact(x, y, [2, 16], 10):
                        continue
                    sand_physics(x, y, this_cell)
                case 8:
                    # Caesium
                    if explode_on_contact(x, y, [2, 16], 50):
                        continue
                    sand_physics(x, y, this_cell)
                case 9:
                    # Lava
                    # Reactions - water into stone
                    if absorb(x, y, [2, 16], [10, 15]):
                        continue

                    # Sinking
                    if check_swaps(x, y, sinks_in_water, this_cell):
                        continue

                    change(x, y, [1, 4, 13, 5], [11, 12, 14, 3])

                    fluid_physics(x, y, this_cell)
                case 10:
                    # Stone
                    heavy_physics(x, y, this_cell)
                case 11:
                    # Glass
                    pass
                case 12:
                    # Brick
                    pass
                case 13:
                    # Ice
                    spread(x, y, [2], this_cell)
                case 14:
                    # Hot Water
                    spread(x, y, [13], this_cell)

                    set_px(x, y, 2)
                case 15:
                    # Salt
                    if explode_on_contact(x, y, [9], 2):
                        continue

                    sand_physics(x, y, this_cell)
                case 16:
                    # Rust transformation
                    change(x, y, [3], [5])

                    # Saltwater
                    if check_fluid_swaps(x, y, [2, 6], this_cell):
                        continue

                    fluid_physics(x, y, this_cell)


# Drawing code
update_selection()
old_time = time.time()
win.set_visible(True)


@win.event
def on_draw():
    win.clear()

    # Delta timing
    new_time = time.time()
    globals()["time_delta"] += new_time - old_time
    globals()["old_time"] = new_time

    # Physics logic
    for i in range(0, int(time_delta // sim_rate)):
        if mouse_down:
            update_mouse_px()
        if mouse_erase:
            erase_mouse_px()
        update_physics()

    globals()["time_delta"] = time_delta % sim_rate

    # Visuals
    update_visuals()
    mat_batch.draw()
    cell_batch.draw()

    debug_FPS.draw()


@win.event
def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    update_current_px(x, y)


@win.event
def on_mouse_motion(x, y, dx, dy):
    update_current_px(x, y)


@win.event
def on_mouse_press(x, y, button, modifiers):
    if button == pyglet.window.mouse.LEFT:
        globals()["mouse_down"] = True
        update_current_px(x, y)
        if x < grid_offset:
            globals()["current_mat"] = min(int(((win.height - y) // mat_height) + mat_view_pointer), len(materials) - 1)
            update_selection()
    if button == pyglet.window.mouse.RIGHT:
        globals()["mouse_erase"] = True
        update_current_px(x, y)
    if button == pyglet.window.mouse.MIDDLE:
        update_current_px(x, y)
        mouse_pick()


@win.event
def on_mouse_release(x, y, button, modifiers):
    if button == pyglet.window.mouse.LEFT:
        update_current_px(x, y)
        globals()["mouse_down"] = False
    if button == pyglet.window.mouse.RIGHT:
        update_current_px(x, y)
        globals()["mouse_erase"] = False


pyglet.app.run(1 / 240)
