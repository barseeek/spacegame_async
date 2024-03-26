import asyncio
import curses
import itertools
import os
import random
import time

from curses_tools import draw_frame, get_frame_size, read_controls
from physics import update_speed


TIC_TIMEOUT = 0.1
STARS_COUNT = 100
STAR_SYMBOLS = '+*.:'
SPEED = 0
BORDER_SIZE = 1


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


async def animate_spaceship(canvas, coroutines, start_row, start_column, frames):
  frames = itertools.cycle(frames)
  row, column = start_row, start_column
  row_speed = column_speed = SPEED
  for frame in frames:
    for _ in range(2):
      rows, columns = get_frame_size(frame)
      rows_direction, columns_direction, space_pressed = read_controls(canvas)
      if space_pressed:
        shot_column = column + columns / 2
        shot = fire(canvas, row, shot_column)
        coroutines.append(shot)
      row_speed, column_speed = update_speed(row_speed, column_speed, rows_direction, columns_direction)
      new_row = row + row_speed
      new_column = column + column_speed
      max_row, max_column = canvas.getmaxyx()
      new_row = min(max(new_row, BORDER_SIZE), max_row - rows - BORDER_SIZE)
      new_column = min(max(new_column, BORDER_SIZE),
                       max_column - columns - BORDER_SIZE)
      row, column = new_row, new_column
      draw_frame(canvas, row, column, frame)
      await do_ticking(0.1)
      draw_frame(canvas, row, column, frame, negative=True)





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


def read_frame(filename):
  with open(filename, 'r') as file:
    return file.read()
    
def read_frames_from_dir(frames_dir):
  return [read_frame(os.path.join(frames_dir, file)) 
          for file in os.listdir(frames_dir)]

async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
  """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
  rows_number, columns_number = canvas.getmaxyx()

  column = max(column, 0)
  column = min(column, columns_number - 1)

  row = 0

  while row < rows_number:
      draw_frame(canvas, row, column, garbage_frame)
      await asyncio.sleep(0)
      draw_frame(canvas, row, column, garbage_frame, negative=True)
      row += speed


async def fill_orbit_with_garbage(canvas, coroutines, frames):
  height, width = canvas.getmaxyx()
  while True:
    frame = random.choice(frames)
    _, trash_column_size = get_frame_size(frame)
    column = random.randint(BORDER_SIZE, width - trash_column_size - BORDER_SIZE)
    coroutine = fly_garbage(canvas, column=column,
                            garbage_frame=frame)
    coroutines.append(coroutine)
    await do_ticking(1)


def draw(canvas):
  curses.curs_set(False)
  canvas.nodelay(True)
  canvas.border()
  height, width = canvas.getmaxyx()
  frames = []
  frames.append(read_frame('animations/rocket/rocket_frame_1.txt'))
  frames.append(read_frame('animations/rocket/rocket_frame_2.txt'))
  coroutines = [
      blink(canvas, row, column, symbol, random.randint(0, 3))
      for row, column, symbol in generate_stars(height, width)
  ]
  spaceship = animate_spaceship(canvas, coroutines, height // 2, width // 2, frames)
  garbage_frames = read_frames_from_dir('animations/garbage')
  garbage = fill_orbit_with_garbage(canvas, coroutines, garbage_frames)
  coroutines.append(spaceship)
  coroutines.append(garbage)
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
