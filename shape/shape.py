import argparse
import PIL.Image

def convert_tabs(line, tabwidth):
    result = []
    for char in line:
        if char == "\t":
            result.append(" " * tabwidth)
        else:
            result.append(char)
    return "".join(result)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("infile",
            help="input source file")
    parser.add_argument("outfile",
            help="output image file (image format detected based on extension)")
    parser.add_argument("--tabwidth", "-w", type=int, default=8,
            help="the amount of spaces per tab")
    parser.add_argument("--upscale", "-u", action="store_true",
            help="increase the output image's size by 10")
    args = parser.parse_args()

    with open(args.infile) as f:
        text = f.read()

    lines = [convert_tabs(line, args.tabwidth) for line in text.splitlines()]
    width = max(map(len, lines))
    height = len(lines)

    image = PIL.Image.new("RGB", (width, height), (255, 255, 255))

    # Algorithm for drawing the "shape" of code, to be improved later
    for y, line in enumerate(lines):
        for x, char in enumerate(line):
            if not char.isspace():
                image.putpixel((x, y), (0, 0, 0))

    if args.upscale:
        image = image.resize((width * 10, height * 10),
                resample=PIL.Image.NEAREST)

    with open(args.outfile, "wb") as f:
        image.save(f)

if __name__ == "__main__":
    main()
