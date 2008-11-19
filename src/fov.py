# Copyright (c) 2008 Mikael Lind
#
# Based on the article "FOV using recursive shadowcasting" by Bjorn Bergstrom,
# and the implementation "Python shadowcasting implementation" by EricDB, both
# at RogueBasin.
#
# http://roguebasin.roguelikedevelopment.org/
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


# Define a coordinate transformation for each octant. The transformations let
# us write a scanning algorithm for the first octant and apply it to any
# octant.
#
#       y
#
#   \ 2 | 1 /
#    \  |  /
#   3 \ | / 0 (first)
#      \|/ 
#   ----+---- x
#      /|\ 
#   4 / | \ 7
#    /  |  \
#   / 5 | 6 \

_octants = (( 1,  0,  0,  1),
            ( 0,  1,  1,  0),
            ( 0, -1,  1,  0),
            (-1,  0,  0,  1),
            (-1,  0,  0, -1),
            ( 0, -1, -1,  0),
            ( 0,  1, -1,  0),
            ( 1,  0,  0, -1))


def fov(cx, cy, r, visit, debug=None):

    """Calculate the field of view in a square grid.

    Arguments:

      cx, cy      - The view point.
      r           - The view radius.
      visit(x, y) - A function that will be called for each cell within the
                    field of view. It returns true if the cell blocks further
                    view, false otherwise.
      debug()     - A function that will be called once before each scan.
    """

    # Visit the center, ignoring whether it is a wall.
    visit(cx, cy)

    # Maintain a stack of pending beams. Store each beam as a tuple:
    #
    #   (min_x, min_y, max_y, min_dy, min_dx, max_dy, max_dx)
    #
    #   min_x          - The first column to scan.
    #   min_y, max_y   - The first and last rows to scan.
    #   min_dy, min_dx - The start slope of the beam.
    #   max_dy, max_dx - The end slope of the beam.
    #
    # We track min_y and max_y to avoid scanning all the way from top to bottom
    # for each column. Another alternative is to calculate min_y and max_y from
    # the slopes.

    stack = []

    # Scan all octants.
    for xx, xy, yx, yy in _octants:

        # Push the root beam for this octant onto the stack.
        stack.append((1, 0, 1, 0, 1, 1, 1))

        while stack:
            if debug is not None:

                # Notify the caller about the new scan.
                debug()

            # Pop the next beam from the stack.
            min_x, min_y, max_y, min_dy, min_dx, max_dy, max_dx = stack.pop()
            for x in xrange(min_x, r + 1):
                min_cell_dx, max_cell_dx = 2 * x + 1, 2 * x - 1

                # Skip any cells that are completely below or above the beam,
                # or completely outside its radius.
                while (2 * min_y + 1) * min_dx <= min_dy * max_cell_dx:
                    min_y += 1
                while (2 * max_y - 1) * max_dx >= max_dy * min_cell_dx:
                    max_y -= 1
                while (2 * x - 1) ** 2 + (2 * max_y - 1) ** 2 >= (2 * r) ** 2:
                    max_y -= 1

                # Scan the column from base to top.
                any_walls = False
                all_walls = True
                old_wall = False
                for y in xrange(min_y, max_y + 1):

                    # Transform to global coordinates and visit the cell.
                    wall = visit(cx + x * xx + y * xy, cy + x * yx + y * yy)

                    if wall:
                        if not any_walls:

                            # We have found the first wall in the column. Save
                            # the old beam.
                            any_walls = True
                            old_max_y = max_y
                            old_max_dy, old_max_dx = max_dy, max_dx

                        if not old_wall:

                            # Initially assume that the new wall spans the rest
                            # of the column.
                            old_wall = True
                            max_y = y
                            max_dy, max_dx = 2 * y - 1, min_cell_dx

                        # The second to last cell in the column may block the
                        # last cell.
                        if (y == old_max_y - 1 and (2 * y + 1) * old_max_dx 
                            > old_max_dy * max_cell_dx):
                             break

                    else:
                        if old_wall:

                            # We have finished scanning a wall.
                            old_wall = False
                            if not all_walls and x < r:

                                # The wall divides the column into two gaps.
                                # Push a child beam for the lower gap onto the
                                # stack.
                                stack.append((x + 1, min_y, max_y, min_dy,
                                             min_dx, max_dy, max_dx))

                            # Initially assume that the new gap spans the rest
                            # of the column.
                            min_y, max_y = y, old_max_y
                            min_dy, min_dx = 2 * (y - 1) + 1, max_cell_dx
                            max_dy, max_dx = old_max_dy, old_max_dx

                        all_walls = False
                if all_walls:
                    break

                # Increment max_y for the next column.
                max_y += 1
