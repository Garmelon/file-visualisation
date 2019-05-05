import argparse
import json
import sys

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

class Shaper:
    def __init__(self, args):
        self.args = args

    def convert_tabs(self, string):
        return string.replace("\t", " " * self.args.tabwidth)

    def get_dimensions(self, text):
        lines = self.convert_tabs(text).splitlines()
        width = max(map(len, lines))
        height = len(lines)
        return width, height

    def to_color(self, colorstr):
        return PIL.ImageColor.getrgb("#" + colorstr)

    def figure_out_lexer(self, text):
        if self.args.lexer is not None:
            return pygments.lexers.get_lexer_by_name(self.args.lexer)
        else:
            return pygments.lexers.guess_lexer_for_filename(self.args.infile, text)

    def get_style(self):
        if self.args.style is not None:
            return pygments.styles.get_style_by_name(self.args.style)

    def draw_to_image(self, image, tokens):
        x, y = 0, 0
        for token in tokens:
            value, style = token["value"], token["style"]
            color = self.to_color(style["color"] or self.args.textcolor)
            bgcolor = self.to_color(style["bgcolor"] or self.args.bgcolor)

            for char in value:
                if char == "\n":
                    x = 0
                    y += 1
                elif char == "\t":
                    image.putpixel((x, y), bgcolor)
                    x += 1
                    while x % self.args.tabwidth != 0:
                        image.putpixel((x, y), bgcolor)
                        x += 1
                elif char.isspace():
                    image.putpixel((x, y), bgcolor)
                    x += 1
                else:
                    image.putpixel((x, y), color)
                    x += 1

    def find_shape(self):
        with open(self.args.infile) as f:
            text = f.read()

        width, height = self.get_dimensions(text)
        print(f"Image dimensions: {width}x{height}")
        image = PIL.Image.new( "RGB", (width, height),
                self.to_color(self.args.bgcolor))

        lexer = self.figure_out_lexer(text)
        print(f"Using lexer: {lexer.name}")
        style = self.get_style()
        if style is None:
            print("Using default style")
            formatter = JsonFormatter()
        else:
            print(f"Using style: {self.args.style}")
            formatter = JsonFormatter(style=style)
        tokens = json.loads(pygments.highlight(text, lexer, formatter))

        self.draw_to_image(image, tokens)

        if self.args.upscale:
            print("Scaling up the image by a factor of 10")
            image = image.resize((width * 10, height * 10),
                    resample=PIL.Image.NEAREST)
            print(f"New image dimensions: {image.width}x{image.height}")

        with open(self.args.outfile, "wb") as f:
            image.save(f)

def list_lexers():
    print("Available lexers:")

    short_names = [info[1] for info in pygments.lexers.get_all_lexers()]
    for names in sorted(short_names):
        print("    " + ", ".join(names))

def list_styles():
    print("Available styles:")

    for style in sorted(pygments.styles.get_all_styles()):
        print("    " + style)

def main():
    # Workaround because I don't know how to do this with argparse
    lexers = "--list-lexers" in sys.argv
    styles = "--list-styles" in sys.argv
    if lexers or styles:
        if lexers:
            list_lexers()
        if lexers and styles:
            print()
        if styles:
            list_styles()
        return

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
    parser.add_argument("--lexer", "-l",
            help="the lexer to use (for a list, see --list-lexers)")
    parser.add_argument("--list-lexers", action="store_true",
            help="a list of all lexers available")
    parser.add_argument("--style", "-s",
            help="the color scheme to use (for a list, see --list-styles)")
    parser.add_argument("--list-styles", action="store_true",
            help="a list of all color schemes available")

    args = parser.parse_args()
    shaper = Shaper(args)
    shaper.find_shape()

if __name__ == "__main__":
    main()
