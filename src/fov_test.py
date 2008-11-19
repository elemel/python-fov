from fov import fov
import sys


TEST_CASES = ("""
             .....
       ...  .......
  ... ..... .......
0 .1. ..2.. ...3...
  ... ..... .......
       ...  .......
             .....
""", """
    ....
 .  ......
 .. ......
....#.....
 .......#..
   #.5.....
 .....#....
.......   .
 ......
 ......
   .....
""", """
  ######
  #    #
###..###
#@...#
######
""")


def parse_test_case(test_case):
    lines = [line.rstrip() for line in test_case.splitlines()[1:]]
    width = max(len(line) for line in lines)
    if width != min(len(line) for line in lines):
        lines = [line.ljust(width) for line in lines]
    cells = [list(line.replace('.', ' ')) for line in lines]
    return lines, cells


def do_fov(cells):
    width, height = len(cells[0]), len(cells)
    def visit(x, y):
        if not (0 <= x < width and 0 <= y < height):
            raise IndexError('grid position (%d, %d) out of range'
                                 % (x, y))
        if cells[y][x] == ' ':
            cells[y][x] = '.'
        return cells[y][x] == '#'
    for y, row in enumerate(cells):
        for x, cell in enumerate(row):
            if cell.isdigit() or cell == '@':
                fov(x, y, 1000 if cell == '@' else int(cell), visit)


def validate_result(cells, lines):
    return [''.join(row) for row in cells] == lines


def print_fail_message(n, cells, lines):
    width = len(cells[0])
    print 'Failed test case #%d:' % (n)
    print
    print '  %s | %s | %s' % ('RESULT'.ljust(width)[:width],
                              'EXPECTED'.ljust(width)[:width],
                              'STATUS')
    for row, line in zip(cells, lines):
        assert len(row) == width and len(line) == width
        for x in xrange(width):
            if row[x] != line[x]:
                status = 'Column %d differs.' % x
                break
        else:
            status = 'OK.'
        print '  %s | %s | %s' % (''.join(row), line, status)
    print


def print_summary(failed, passed):
    if failed:
        print 'Failed %d test case(s).' % failed
    if passed:
        print 'Passed %d test case(s).' % passed


def main():
    failed = 0
    for n, test_case in enumerate(TEST_CASES):
        lines, cells = parse_test_case(test_case)
        try:
            do_fov(cells)
        except Exception, e:
            print 'Exception in test case %d: %s' % (n, e)
            raise e
        if not validate_result(cells, lines):
            failed += 1
            print_fail_message(n, cells, lines)
    print_summary(failed, len(TEST_CASES) - failed)
    return failed


if __name__ == '__main__':
    sys.exit(main())
