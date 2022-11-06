import asyncio
import curses
import glob
import os
import time
from itertools import cycle
from random import choice, randint

from curses_tools import draw_frame, get_frame_size, read_controls, update_speed

CANVAS_BORDER_INDENT = 2
FRAME_BORDER_INDENT = 1
STARS_AMOUNT = 50  # TODO import amount from env or as argument


class Obstacle:

    def __init__(self, row, column, rows_size=1, columns_size=1, uid=None):
        self.row = row
        self.column = column
        self.rows_size = rows_size
        self.columns_size = columns_size
        self.uid = uid

    def get_bounding_box_frame(self):
        # increment box size to compensate obstacle movement
        rows, columns = self.rows_size + 1, self.columns_size + 1
        return '\n'.join(_get_bounding_box_lines(rows, columns))

    def get_bounding_box_corner_pos(self):
        return self.row - 1, self.column - 1

    def dump_bounding_box(self):
        row, column = self.get_bounding_box_corner_pos()
        return row, column, self.get_bounding_box_frame()

    def has_collision(self, obj_corner_row, obj_corner_column, obj_size_rows=1, obj_size_columns=1):
        '''Determine if collision has occured. Return True or False.'''
        return has_collision(
            (self.row, self.column),
            (self.rows_size, self.columns_size),
            (obj_corner_row, obj_corner_column),
            (obj_size_rows, obj_size_columns),
        )


def _get_bounding_box_lines(rows, columns):

    yield ' ' + '-' * columns + ' '
    for _ in range(rows):
        yield '|' + ' ' * columns + '|'
    yield ' ' + '-' * columns + ' '


async def show_obstacles(canvas, obstacles):
    """Display bounding boxes of every obstacle in a list"""

    while True:
        boxes = []

        for obstacle in obstacles:
            boxes.append(obstacle.dump_bounding_box())

        for row, column, frame in boxes:
            draw_frame(canvas, row, column, frame)

        await asyncio.sleep(0)

        for row, column, frame in boxes:
            draw_frame(canvas, row, column, frame, negative=True)


def _is_point_inside(corner_row, corner_column, size_rows, size_columns, point_row, point_row_column):
    rows_flag = corner_row <= point_row < corner_row + size_rows
    columns_flag = corner_column <= point_row_column < corner_column + size_columns

    return rows_flag and columns_flag


def has_collision(obstacle_corner, obstacle_size, obj_corner, obj_size=(1, 1)):
    '''Determine if collision has occured. Return True or False.'''

    opposite_obstacle_corner = (
        obstacle_corner[0] + obstacle_size[0] - 1,
        obstacle_corner[1] + obstacle_size[1] - 1,
    )

    opposite_obj_corner = (
        obj_corner[0] + obj_size[0] - 1,
        obj_corner[1] + obj_size[1] - 1,
    )

    return any([
        _is_point_inside(*obstacle_corner, *obstacle_size, *obj_corner),
        _is_point_inside(*obstacle_corner, *obstacle_size,
                         *opposite_obj_corner),

        _is_point_inside(*obj_corner, *obj_size, *obstacle_corner),
        _is_point_inside(*obj_corner, *obj_size, *opposite_obstacle_corner),
    ])


async def fire(canvas, start_row, start_column, rows_speed=-0.3,
               columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        for obstacle in obstacles:
            if obstacle.has_collision(row, column):
                obstacles_in_last_collisions.append(obstacle)
                return
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def blink(canvas, row, column, symbol='*'):
    """Draw flickering symbol"""
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(20)

        canvas.addstr(row, column, symbol)
        await sleep(3)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(5)

        canvas.addstr(row, column, symbol)
        await sleep(3)


def get_next_coordinates(canvas, frame, row, column, rows_direction, columns_direction, row_speed, column_speed):
    """Calculate rocket coordinate after user choose"""
    height, width = curses.window.getmaxyx(canvas)

    row_speed, column_speed = update_speed(
        row_speed,
        column_speed,
        rows_direction,
        columns_direction
    )

    row += row_speed
    column += column_speed
    frame_rows, frame_columns = get_frame_size(frame)

    row = max(
        min(height - frame_rows - FRAME_BORDER_INDENT, row),
        FRAME_BORDER_INDENT
    )

    column = max(
        min(width - frame_columns - FRAME_BORDER_INDENT, column),
        FRAME_BORDER_INDENT
    )

    return row, column, row_speed, column_speed


async def animate_spaceship(canvas, row, column, rockets):
    """Calculate rocket coordinates and draw rocket"""
    row_speed = column_speed = 0
    for rocket in cycle(rockets):
        rows_direction, columns_direction, space_pressed = read_controls(
            canvas)
        row, column, row_speed, column_speed = get_next_coordinates(
            canvas,
            rocket,
            row,
            column,
            rows_direction,
            columns_direction,
            row_speed,
            column_speed
        )

        draw_frame(canvas, row, column, rocket)
        if space_pressed:
            frame_rows, frame_columns = get_frame_size(rocket)
            coroutines.append(fire(canvas, row, column + frame_columns // 2))
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, rocket, negative=True)


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 0
    row_size, column_size = get_frame_size(garbage_frame)

    while row < rows_number:
        obstacle = Obstacle(row, column, row_size, column_size)
        obstacles.append(obstacle)

        draw_frame(canvas, row, column, garbage_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        obstacles.remove(obstacle)
        if obstacle in obstacles_in_last_collisions:
            return
        row += speed


async def fill_orbit_with_garbage(canvas, garbages, width):
    for garbage in cycle(garbages):
        column = randint(0, width)
        coroutines.append(fly_garbage(
            canvas, column=column, garbage_frame=garbage))
        await sleep(10)


async def sleep(tics=1):
    for _ in range(tics):
        await asyncio.sleep(0)


def draw(canvas):
    """Create game logic and draw the game"""
    path_to_rockets = 'frames'  # TODO import path from env or as argument
    rockets = []
    for filename in glob.glob(os.path.join(path_to_rockets, '*.txt')):
        with open(os.path.join(os.getcwd(), filename), 'r') as rocket_file:
            rocket = rocket_file.read()
            rockets.append(rocket)
            rockets.append(rocket)

    path_to_garbage = os.path.join('frames', 'trash')
    garbages = []
    for filename in glob.glob(os.path.join(path_to_garbage, '*.txt')):
        with open(os.path.join(os.getcwd(), filename), 'r') as garbage_file:
            garbage = garbage_file.read()
            garbages.append(garbage)

    height, width = curses.window.getmaxyx(canvas)
    tic_timeout = 0.1
    canvas.border()
    curses.curs_set(False)
    canvas.nodelay(True)

    global obstacles
    obstacles = []

    global obstacles_in_last_collisions
    obstacles_in_last_collisions = []

    global coroutines
    coroutines = [fire(canvas, height // 2, width // 2)]
    coroutines.append(animate_spaceship(
        canvas, height // 2, width // 2, rockets))
    coroutines.append(fill_orbit_with_garbage(canvas, garbages, width))
    symbols = ['+', '*', '.', ':']
    coroutines.extend([blink(
        canvas,
        randint(CANVAS_BORDER_INDENT, height - CANVAS_BORDER_INDENT),
        randint(CANVAS_BORDER_INDENT, width - CANVAS_BORDER_INDENT),
        choice(symbols)) for i in range(STARS_AMOUNT)
    ])
    coroutines.append(show_obstacles(canvas, obstacles))

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)

            except StopIteration:
                coroutines.remove(coroutine)
        canvas.refresh()
        time.sleep(tic_timeout)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
