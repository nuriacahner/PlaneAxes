"""Draw the toolbar icons (a plane seen at an angle with its X / Y axes). Pure Python PNG.

    py -3.10 tools/make_icons.py
"""

import math
import os
import struct
import zlib

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'resources', 'PlaneAxes')
INK = (60, 60, 60)
ORANGE = (255, 120, 0)
BLUE = (30, 110, 230)


def png(path, size, px):
    raw = b''.join(b'\x00' + bytes(c for p in row for c in p) for row in px)

    def chunk(tag, data):
        return (struct.pack('>I', len(data)) + tag + data
                + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff))

    with open(path, 'wb') as fh:
        fh.write(b'\x89PNG\r\n\x1a\n')
        fh.write(chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0)))
        fh.write(chunk(b'IDAT', zlib.compress(raw, 9)))
        fh.write(chunk(b'IEND', b''))


def _seg_dist(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / (vx * vx + vy * vy)))
    return math.hypot(px - ax - t * vx, py - ay - t * vy)


def draw(size):
    ss = 4
    n = size * ss
    w = max(1.2, n / 16.0)
    # plane: a parallelogram outline; origin near its lower left; X (orange) along the
    # long side, Y (blue) along the short side
    quad = [(0.10, 0.62), (0.62, 0.92), (0.90, 0.40), (0.38, 0.10)]
    quad = [(x * n, y * n) for x, y in quad]
    o = (0.30 * n, 0.62 * n)
    xe = (0.74 * n, 0.82 * n)
    ye = (0.50 * n, 0.26 * n)
    cov = [[None] * n for _ in range(n)]
    for y in range(n):
        for x in range(n):
            fx, fy = x + 0.5, y + 0.5
            for i in range(4):
                a, b = quad[i], quad[(i + 1) % 4]
                if _seg_dist(fx, fy, a[0], a[1], b[0], b[1]) < w / 2.6:
                    cov[y][x] = INK
            if _seg_dist(fx, fy, o[0], o[1], xe[0], xe[1]) < w / 1.6:
                cov[y][x] = ORANGE
            if _seg_dist(fx, fy, o[0], o[1], ye[0], ye[1]) < w / 1.6:
                cov[y][x] = BLUE
    rows = []
    for y in range(size):
        row = []
        for x in range(size):
            acc = [0, 0, 0, 0]
            for sy in range(ss):
                for sx in range(ss):
                    c = cov[y * ss + sy][x * ss + sx]
                    if c:
                        acc[0] += c[0]
                        acc[1] += c[1]
                        acc[2] += c[2]
                        acc[3] += 1
            k = acc[3]
            row.append((acc[0] // k, acc[1] // k, acc[2] // k, 255 * k // (ss * ss))
                       if k else (0, 0, 0, 0))
        rows.append(row)
    return rows


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for s in (16, 32, 64):
        png(os.path.join(OUT, '%dx%d.png' % (s, s)), s, draw(s))
    print('icons written to', OUT)
