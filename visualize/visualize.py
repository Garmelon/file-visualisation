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

    _cache = {}

    def __init__(self, kind, value, alpha):
        self._kind = kind
        self._value = value
        self._alpha = alpha

    @classmethod
    def grayscale(cls, v, a=255):
        params = (cls.GRAYSCALE, v, a)
        pixel = cls._cache.get(params)

        if pixel is None:
            pixel = cls(cls.GRAYSCALE, v, a)
            cls._cache[params] = pixel

        return pixel

    @classmethod
    def color(cls, r, g, b, a=255):
        params = (cls.COLOR, r, g, b, a)
        pixel = cls._cache.get(params)

        if pixel is None:
            pixel = cls(cls.COLOR, (r, g, b), a)
            cls._cache[params] = pixel

        return pixel

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



def load_pixels(bytestr):
    for byte in bytestr:
        yield Pixel.grayscale(byte)

def arrange_by_widthes(pixels, widthes):
    index = 0
    pixel_amount = len(pixels)
    for width in widthes:
        if index < pixel_amount:
            #print(f"At pixel {index: 8}")
            yield pixels[index:index+width]
            index += width

    last_width = widthes[-1]
    while index < pixel_amount:
        #print(f"At pixel {index: 8}")
        yield pixels[index:index+last_width]
        index += last_width

def pad_rows_to_width(rows, width, pad_with=Pixel.EMPTY):
    for row in rows:
        if len(row) < width:
            delta = width - len(row)
            yield row + delta * [pad_with]
        else:
            yield row

def rows_as_grayscale(rows, alpha=True):
    for row in rows:
        combined = []
        for pixel in row:
            combined.extend(pixel.as_grayscale(alpha=alpha))
        yield combined

def rows_as_rgb(rows, alpha=True):
    for row in rows:
        combined = []
        for pixel in row:
            combined.extend(pixel.as_rgb(alpha=alpha))
        yield combined



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

    if args.transparent:
        alpha = True
        greyscale = True
        pad_with = Pixel.EMPTY
    else:
        alpha = False
        greyscale = False
        pad_with = Pixel.EMPTY_GREEN

    if args.width is not None:
        widthes = parse_widthes(args.width)
    else:
        widthes = None # determined once we know the amount of pixels

    print(f"Reading from {args.infile!r}")
    with open(args.infile, "rb") as f:
        bytestr = f.read()
    print(f"{len(bytestr)} bytes")

    pixels = list(load_pixels(bytestr))
    print(f"{len(pixels)} pixels")

    if widthes is None:
        widthes = [optimal_width(len(pixels))]

    print("Arranging pixels into rows")
    rows = list(arrange_by_widthes(pixels, widthes))
    max_width = max(map(len, rows))
    height = len(rows)
    print(f"{height} rows, maximum width is {max_width}")
    print("Padding rows to the right width")
    padded_rows = list(pad_rows_to_width(rows, max_width, pad_with))

    print("Converting rows to raw pixel values")
    if greyscale:
        value_rows = rows_as_grayscale(padded_rows, alpha=alpha)
    else:
        value_rows = rows_as_rgb(padded_rows, alpha=alpha)

    print(f"Writing to {args.outfile!r}")
    writer = png.Writer(greyscale=greyscale, alpha=alpha,
            width=max_width, height=height)
    with open(args.outfile, "wb") as f:
        writer.write(f, value_rows)

    if args.upscale:
        print(f"Upscaling {args.outfile!r} with convert")
        subprocess.run([
            "convert", args.outfile,
            "-filter", "point",
            "-resize", "1000%",
            args.outfile
        ])

if __name__ == "__main__":
    main()
