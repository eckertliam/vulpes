# This is a messy prototype of a Vulpes compiler.
# It is a loose example of what the final C++ compiler will look like.
# It is not intended to be a full implementation of the language.
# It is only intended to be a minimal proof of concept.


import sys
from prototype.parser import parse, Program


def main():
    # read the file input from the command line
    if len(sys.argv) != 2:
        print("Usage: python main.py <file> [--aot]")
        sys.exit(1)
    file = sys.argv[1]
    aot = "--aot" in sys.argv
    # read the file input from the command line
    with open(file, "r") as f:
        source = f.read()
    # parse the source code
    program = parse(source)
    # TODO: run program through passes
    # TODO: convert program to bytecode IR
    if aot:
        # TODO: convert bytecode IR to C++
        pass
    else:
        # TODO: run bytecode IR through the VM
        pass
