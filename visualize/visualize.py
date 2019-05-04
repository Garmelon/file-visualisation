import argparse
import math
import re
import subprocess

import png


class ArgumentException(Exception):
    pass

class Pixel:
    GRAYSCALE = "grayscale"
    COLOR = "color"

    def __init__(self, kind, value, alpha):
        self._kind = kind
        self._value = value
        self._alpha = alpha

    @classmethod
    def grayscale(cls, v, a=255):
        return cls(cls.GRAYSCALE, v, a)

    @classmethod
    def color(cls, r, g, b, a=255):
        return cls(cls.COLOR, (r, g, b), a)

    def as_grayscale(self, alpha=False):
        if self._kind == self.GRAYSCALE:
            values = [self._value]
        elif self._kind == self.COLOR:
            values = [(self._value[0] + self._value[1] + self._value[2]) // 3]

        if alpha:
            values.append(self._alpha)

        return values

    def as_rgb(self, alpha=False):
        if self._kind == self.GRAYSCALE:
            values = [self._value] * 3
        elif self._kind == self.COLOR:
            values = list(self._value)

        if alpha:
            values.append(self._alpha)

        return values

Pixel.EMPTY = Pixel.grayscale(0, a=0)
Pixel.EMPTY_GREEN = Pixel.color(0, 255, 0)

def parse_widthes(widthstr):
    widthes = []

    for width in widthstr.split(","):
        match = re.fullmatch(r"((\d+)\*)?(\d+)", width)
        if not match:
            raise ArgumentException(f"invalid width: {width!r}")

        width_nr = int(match.group(3))

        if match.group(2):
            width_times = int(match.group(2))
        else:
            width_times = 1

        widthes.extend(width_times * [width_nr])

    return widthes

def optimal_width(total):
    width = 1
    while total // width > width:
        width += 1

    return width

def arrange_by_widthes(pixels, widthes):
    rows = []

    for width in widthes:
        if pixels:
            print(f"{len(pixels): 8} pixels left")
            rows.append(pixels[:width])
            pixels = pixels[width:]


    last_width = widthes[-1]
    while pixels:
        print(f"{len(pixels): 8} pixels left")
        rows.append(pixels[:last_width])
        pixels = pixels[last_width:]

    return rows

def max_row_width(rows):
    return max(map(len, rows))

def pad_rows_to_width(rows, width, pad_with=Pixel.EMPTY): # modifies in-place
    for row in rows:
        if len(row) < width:
            delta = width - len(row)
            row.extend(delta * [pad_with])

def rows_as_grayscale(rows, alpha=True):
    new_rows = []
    for row in rows:
        values = (pixel.as_grayscale(alpha=alpha) for pixel in row)
        new_rows.append(sum(values, []))
    return new_rows

def rows_as_rgb(rows, alpha=True):
    new_rows = []
    for row in rows:
        values = (pixel.as_rgb(alpha=alpha) for pixel in row)
        new_rows.append(sum(values, []))
    return new_rows

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("infile")
    parser.add_argument("outfile")
    parser.add_argument("--width", "-w")
    parser.add_argument("--upscale", "-u", action="store_true")
    parser.add_argument("--transparent", "-t", action="store_true")
    args = parser.parse_args()

    # The following code should probably be put into separate methods 'n stuff,
    # but it works for now and this is just an experimental script, so... I'll
    # do it once I need to add more functionality.

    if args.width is not None:
        widthes = parse_widthes(args.width)
    else:
        widthes = None # to be determined after file is loaded

    with open(args.infile, "rb") as f:
        values = list(f.read())

    print(f"{len(values)} bytes total")

    # TODO check for mode (grayscale vs rgb)
    print("Loading pixels")
    pixels = [Pixel.grayscale(value) for value in values]

    if widthes is None:
        widthes = [optimal_width(len(pixels))]

    rows = arrange_by_widthes(pixels, widthes)
    max_width = max_row_width(rows)

    if args.transparent:
        print("Using transparent background")
        alpha = True
        pad_rows_to_width(rows, max_width, pad_with=Pixel.EMPTY)
    else:
        print("Using green background")
        alpha = False
        pad_rows_to_width(rows, max_width, pad_with=Pixel.EMPTY_GREEN)

    value_rows = rows_as_rgb(rows, alpha=alpha)
    writer = png.Writer(alpha=alpha, width=max_width, height=len(rows))

    with open(args.outfile, "wb") as f:
        writer.write(f, value_rows)

    if args.upscale:
        print(f"Upscaling {args.outfile!r} with convert")
        subprocess.run(["convert", args.outfile, "-filter", "point", "-resize", "1000%", args.outfile])

if __name__ == "__main__":
    main()
