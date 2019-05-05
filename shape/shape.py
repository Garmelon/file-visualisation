import argparse
import json

import PIL.Image
import PIL.ImageColor
import pygments
import pygments.formatter
import pygments.lexers


class JsonFormatter(pygments.formatter.Formatter):
    def __init__(self, **options):
        super().__init__(**options)

        # Probably unnecessary, but hey, it works (hopefully)
        self.styles = {}
        for token, style in self.style:
            info = {"color": style["color"], "bgcolor": style["bgcolor"]}
            self.styles[token] = info

    def format(self, tokensource, outfile):
        tokens = []
        for ttype, value in tokensource:
            while ttype not in self.styles:
                ttype = ttype.parent
            info = {"value": value, "style": self.styles[ttype]}
            tokens.append(info)
        outfile.write(json.dumps(tokens))

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
            help=("output image file (image format detected based on"
                " extension)"))
    parser.add_argument("--tabwidth", "-w", type=int, default=8,
            help="the amount of spaces per tab")
    parser.add_argument("--upscale", "-u", action="store_true",
            help="increase the output image's size by 10")
    parser.add_argument("--textcolor", "-t", default="000000",
            help=("default text color for all sections that pygment doesn't"
                " specify a color for"))
    parser.add_argument("--bgcolor", "-b", default="FFFFFF",
            help=("default background color for all sections that pygment"
                " doesn't specify a color for"))
    args = parser.parse_args()

    with open(args.infile) as f:
        text = f.read()

    lines = [convert_tabs(line, args.tabwidth) for line in text.splitlines()]
    width = max(map(len, lines))
    height = len(lines)

    image = PIL.Image.new("RGB", (width, height),
            PIL.ImageColor.getrgb("#" + args.bgcolor))

    tokens = json.loads(pygments.highlight(text, pygments.lexers.PythonLexer(),
        JsonFormatter()))

    x, y = 0, 0
    for token in tokens:
        value, style = token["value"], token["style"]

        colorstr = "#" + (style["color"] or args.textcolor)
        color = PIL.ImageColor.getrgb(colorstr)

        bgcolorstr = "#" + (style["bgcolor"] or args.bgcolor)
        bgcolor = PIL.ImageColor.getrgb(bgcolorstr)

        for char in value:
            if char == "\n":
                x = 0
                y += 1
            elif char.isspace():
                image.putpixel((x, y), bgcolor)
                x += 1
            else:
                image.putpixel((x, y), color)
                x += 1

    if args.upscale:
        image = image.resize((width * 10, height * 10),
                resample=PIL.Image.NEAREST)

    with open(args.outfile, "wb") as f:
        image.save(f)

if __name__ == "__main__":
    main()
