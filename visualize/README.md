# Visualize

The idea of this experiment is to visualize a file by converting its bytes to
pixels. This process should be fully reversible (a script for another day :P).

It uses the `pypng` package, so make sure to install that if you want to try
this script out yourself.

## Examples

The green pixels are just background pixels, not a part of the file.

Random bytes from `/dev/urandom`:
![random bytes](examples/random.png)

A short `hello world` program written in C and compiled by gcc:
![hello world](examples/hello_world.png)

The source code of the script:
![visualize](examples/visualize.png)

The source code of the script, with correct line lengths:
![visualize with correct line lengths](examples/visualize_lines.png)
