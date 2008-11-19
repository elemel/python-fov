from fov import fov
import curses, random


DUNGEON = """
    #####   #########
                    #
                    #           ###########
                                          #
##  #########                             #
#
#
#          ########   ########            #
#                            #            #
                             #            #
                             #       #    #
#                ######### ###       #    #
#                                    #
###############                      #          #
                                                #
                                     #          #
                                     #          #
                           #############   ######
"""

HEIGHT, WIDTH = 22, 79
MAX_RADIUS = 80
COLOR = True
DEBUG = False


class Cell(object):
    def __init__(self, char):
        self.char = char
        self.tag = 0
        self.color = 0


class Grid(object):

    def __init__(self, cells):
        self.height, self.width = len(cells), len(cells[0])
        self.cells = cells

    def __contains__(self, yx):
        y, x = yx
        return 0 <= y < self.height and 0 <= x < self.width

    def __getitem__(self, yx):
        y, x = yx
        if y < 0 or x < 0:
            raise IndexError('negative index')
        return self.cells[y][x]


def parse_grid(grid_str, width, height):

    # Split the grid string into lines.
    lines = [line.rstrip() for line in grid_str.splitlines()[1:]]

    # Pad the top and bottom.
    top = (height - len(lines)) // 2
    bottom = (height - len(lines) + 1) // 2
    lines = ([''] * top + lines + [''] * bottom)[:height]

    # Pad the left and right sides.
    max_len = max(len(line) for line in lines)
    left = (width - max_len) // 2
    lines = [' ' * left + line.ljust(width - left)[:width - left]
             for line in lines]

    # Create the grid.
    cells = [[Cell(char) for char in line] for line in lines]
    return Grid(cells)


class Engine(object):

    def __init__(self, grid):
        self.grid = grid
        self.y = random.randrange(self.grid.height)
        self.x = random.randrange(self.grid.width)
        self.radius = 7
        self.tag = 1
        self.color = COLOR
        self.debug = DEBUG
        self.lights = 0
        self.scans = 0

    def move_cursor(self, dy, dx):
        y, x = self.y + dy, self.x + dx
        if (y, x) in self.grid:
            self.y, self.x = y, x

    def update_light(self):
        self.tag += 1
        self.lights = 0
        self.scans = 0
        def visit(y, x):
            self.lights += 1
            if (y, x) not in self.grid:
                return True
            cell = self.grid[y, x]
            cell.tag = self.tag
            cell.color = self.scans
            return self.grid[y, x].char == '#'
        def scan(*args):
            self.scans += 1
        fov(self.y, self.x, self.radius, visit, scan if self.debug else None)


def update_view(stdscr, engine):

    # Update the grid view.
    if engine.color:
        colors = [curses.COLOR_RED, curses.COLOR_YELLOW, curses.COLOR_GREEN,
                  curses.COLOR_CYAN, curses.COLOR_BLUE, curses.COLOR_MAGENTA]
        colors = [curses.COLOR_RED, curses.COLOR_YELLOW,
                  curses.COLOR_GREEN, curses.COLOR_BLUE]
    for y, line in enumerate(engine.grid.cells):
        for x, cell in enumerate(line):
            char = (cell.char if cell.tag else ' ')
            if char == ' ' and cell.tag == engine.tag:
                if engine.debug and cell.color:
                    char = chr((ord('a') + (cell.color - 1) % 26))
                else:
                    char = '.'
            if engine.color:
                if cell.tag == engine.tag:
                    if engine.debug:
                        color = colors[(cell.color - 1) % len(colors)]
                    else:
                        color = (curses.COLOR_YELLOW if char == '.'
                                 else curses.COLOR_GREEN)
                else:
                    color = (curses.COLOR_BLACK if engine.debug
                             else curses.COLOR_BLUE)
                attr = curses.color_pair(color)
                stdscr.addch(y, x, char, attr)
            else:
                stdscr.addch(y, x, char)

    # Update the status lines.
    blocked = (engine.grid[engine.y, engine.x].char == '#')
    status_1 = ['[+-] Radius = %d' % engine.radius,
                '[SPACE] %s' % ('Unblock' if blocked else 'Block')]
    if COLOR:
        status_1.append('[C]olor = %s' % 'NY'[engine.color])
    status_1.append('[D]ebug = %s' % 'NY'[engine.debug])
    status_1.append('[Q]uit')
    status_2 = 'Lit %d cells' % engine.lights
    if engine.debug:
        status_2 += ' during %d scans' % engine.scans
    stdscr.addstr(HEIGHT, 0, ('  '.join(status_1)).ljust(WIDTH)[:WIDTH],
                  curses.A_STANDOUT)
    stdscr.addstr(HEIGHT + 1, 0, (status_2 + '.').ljust(WIDTH)[:WIDTH])

    # Update the cursor.
    cell = engine.grid[engine.y, engine.x]
    char = ('#' if cell.char == '#' else '@')
    stdscr.addch(engine.y, engine.x, char)
    stdscr.move(engine.y, engine.x)


def handle_command(key, engine):

    # Move the cursor.
    if key == ord('7'):                     engine.move_cursor(-1, -1)
    if key in (ord('8'), curses.KEY_UP):    engine.move_cursor(-1,  0)
    if key == ord('9'):                     engine.move_cursor(-1,  1)
    if key in (ord('4'), curses.KEY_LEFT):  engine.move_cursor( 0, -1)
    if key in (ord('6'), curses.KEY_RIGHT): engine.move_cursor( 0,  1)
    if key == ord('1'):                     engine.move_cursor( 1, -1)
    if key in (ord('2'), curses.KEY_DOWN):  engine.move_cursor( 1,  0)
    if key == ord('3'):                     engine.move_cursor( 1,  1)

    # Change the light radius.
    if key == ord('+'): engine.radius = min(MAX_RADIUS, engine.radius + 1)
    if key == ord('-'): engine.radius = max(0, engine.radius - 1)

    # Insert or delete a block at the cursor.
    if key == ord(' '):
        blocked = (engine.grid[engine.y, engine.x].char == '#')
        engine.grid[engine.y, engine.x].char = (' ' if blocked else '#')

    # Toggle options.
    if key in (ord('c'), ord('C')) and COLOR: engine.color = not engine.color
    if key in (ord('d'), ord('D')):           engine.debug = not engine.debug


def main(stdscr):
    if COLOR:
        curses.use_default_colors()
        for i in xrange(curses.COLOR_RED, curses.COLOR_WHITE + 1):
            curses.init_pair(i, i, -1)
    grid = parse_grid(DUNGEON, WIDTH, HEIGHT)
    engine = Engine(grid)
    while True:
        engine.update_light()
        update_view(stdscr, engine)
        key = stdscr.getch()
        if key in (ord('q'), ord('Q')):
            break
        handle_command(key, engine)


if __name__ == '__main__':
    curses.wrapper(main)
