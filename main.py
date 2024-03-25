import asyncio
import curses
import itertools
import random
import time

from curses_tools import draw_frame, get_frame_size, read_controls

TIC_TIMEOUT = 0.1
STARS_COUNT = 100
STAR_SYMBOLS = '+*.:'
SPEED = 1
BORDER_SIZE = 1


async def animate_spaceship(canvas, start_row, start_column, frames):
  frames = itertools.cycle(frames)
  row, column = start_row, start_column
  for frame in frames:

    for _ in range(2):
      rows, columns = get_frame_size(frame)
      rows_direction, columns_direction, _ = read_controls(canvas)
      new_row = row + rows_direction * SPEED
      new_column = column + columns_direction * SPEED
      max_row, max_column = canvas.getmaxyx()
      new_row = min(max(new_row, BORDER_SIZE), max_row - rows - BORDER_SIZE)
      new_column = min(max(new_column, BORDER_SIZE),
                       max_column - columns - BORDER_SIZE)
      row, column = new_row, new_column
      draw_frame(canvas, row, column, frame)
      await do_ticking(0.1)
      draw_frame(canvas, row, column, frame, negative=True)


async def fire(canvas,
               start_row,
               start_column,
               rows_speed=-0.3,
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


async def do_ticking(seconds):
  tick_counter = int(10 * seconds)
  for _ in range(tick_counter):
    await asyncio.sleep(0)


async def blink(canvas, row, column, symbol, step):
  while True:
    if step == 0:
      canvas.addstr(row, column, symbol, curses.A_DIM)
      await do_ticking(2)
      step += 1
    elif step == 1:
      canvas.addstr(row, column, symbol)
      await do_ticking(0.3)
      step += 1
    elif step == 2:
      canvas.addstr(row, column, symbol, curses.A_BOLD)
      await do_ticking(0.5)
      step += 1
    elif step == 3:
      canvas.addstr(row, column, symbol)
      await do_ticking(0.3)
      step = 0


def generate_stars(height, width):
  for _ in range(STARS_COUNT):
    row = random.randint(1, height - 2)
    column = random.randint(1, width - 2)
    symbol = random.choice(STAR_SYMBOLS)
    yield row, column, symbol


def draw(canvas):
  curses.curs_set(False)
  canvas.nodelay(True)
  canvas.border()
  height, width = canvas.getmaxyx()
  frames = []
  with open('animations/rocket_frame_1.txt', 'r') as file:
    frames.append(file.read())
  with open('animations/rocket_frame_2.txt', 'r') as file:
    frames.append(file.read())
  coroutines = [
      blink(canvas, row, column, symbol, random.randint(0, 3))
      for row, column, symbol in generate_stars(height, width)
  ]
  shot = fire(canvas, height // 2, width // 2)
  coroutines.append(shot)
  spaceship = animate_spaceship(canvas, height // 2, width // 2, frames)
  coroutines.append(spaceship)
  while True:
    for coroutine in coroutines.copy():
      try:
        coroutine.send(None)
      except StopIteration:
        coroutines.remove(coroutine)
    canvas.refresh()
    time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
  curses.update_lines_cols()
  curses.wrapper(draw)
