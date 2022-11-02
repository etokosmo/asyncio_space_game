import asyncio
import curses
import glob
import os
import time
from itertools import cycle
from random import choice, randint

from curses_tools import draw_frame, get_frame_size, read_controls

CANVAS_BORDER_INDENT = 2
FRAME_BORDER_INDENT = 1
STARS_AMOUNT = 50  # TODO import amount from env or as argument


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
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def blink(canvas, row, column, symbol='*'):
    """Draw flickering symbol"""
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await asyncio.sleep(0)
        for _ in range(randint(1, 20)):
            await asyncio.sleep(0)
        canvas.addstr(row, column, symbol)
        await asyncio.sleep(0)
        for _ in range(randint(1, 3)):
            await asyncio.sleep(0)
        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await asyncio.sleep(0)
        for _ in range(randint(1, 5)):
            await asyncio.sleep(0)
        canvas.addstr(row, column, symbol)
        await asyncio.sleep(0)
        for _ in range(randint(1, 3)):
            await asyncio.sleep(0)


def get_next_coordinates(canvas, frame, row, column,
                         rows_direction, columns_direction):
    """Calculate rocket coordinate after user choose"""
    height, width = curses.window.getmaxyx(canvas)
    row += rows_direction
    column += columns_direction
    frame_rows, frame_columns = get_frame_size(frame)

    row = max(
        min(height - frame_rows - FRAME_BORDER_INDENT, row),
        FRAME_BORDER_INDENT
    )

    column = max(
        min(width - frame_columns - FRAME_BORDER_INDENT, column),
        FRAME_BORDER_INDENT
    )

    return row, column


async def animate_spaceship(canvas, row, column, rockets):
    """Calculate rocket coordinates and draw rocket"""
    for rocket in cycle(rockets):
        rows_direction, columns_direction, space_pressed = read_controls(
            canvas)
        row, column = get_next_coordinates(
            canvas,
            rocket,
            row,
            column,
            rows_direction,
            columns_direction
        )

        draw_frame(canvas, row, column, rocket)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, rocket, negative=True)


def draw(canvas):
    """Create game logic and draw the game"""
    path_to_rockets = 'frames'  # TODO import path from env or as argument
    rockets = []
    for filename in glob.glob(os.path.join(path_to_rockets, '*.txt')):
        with open(os.path.join(os.getcwd(), filename), 'r') as rocket_file:
            rocket = rocket_file.read()
            rockets.append(rocket)
            rockets.append(rocket)
    height, width = curses.window.getmaxyx(canvas)
    tic_timeout = 0.1
    canvas.border()
    curses.curs_set(False)
    canvas.nodelay(True)

    coroutines = [fire(canvas, height // 2, width // 2)]
    coroutines.append(animate_spaceship(
        canvas, height // 2, width // 2, rockets))

    symbols = ['+', '*', '.', ':']
    coroutines.extend([blink(
        canvas,
        randint(CANVAS_BORDER_INDENT, height - CANVAS_BORDER_INDENT),
        randint(CANVAS_BORDER_INDENT, width - CANVAS_BORDER_INDENT),
        choice(symbols)) for i in range(STARS_AMOUNT)
    ])

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
