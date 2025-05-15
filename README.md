# Bril to x86 Compiler

## About

This is a compiler translating [Bril](https://capra.cs.cornell.edu/bril/) to x86_64. This was my final project for [CS 6120](https://www.cs.cornell.edu/courses/cs6120/2025sp/), which I took in Spring 2025. 


## Running the Compiler

The compiler is all implemented in bril2x86.py. The program expects a Bril program as stdin, and outputs x86_64 assembly to stdout.

The instructions below depend on you following relevant install instructinos for [Bril](https://github.com/sampsyo/bril).

I have some Bril programs in the bril_programs/ directory. An example run of the compiler would be:
`bril2json < bril_programs/binpow.bril | python3 bril2x86.py > main.s`

This would compile the binary exponentiation Bril program into a file of x86 code `main.s`.

To handle prints and command line arguments, the compiler relies on linking with `rt.c` ([original soure](https://github.com/sampsyo/bril/blob/main/brilift/rt.c)). Finally, run the following code to build the executable:
`gcc -c rt.c -o main`.

For `binpow.bril`, we can run `./main 2 10`, and you should get an output of 1024.

I wrote and tested this compiler on my M1 MacbookPro, so I'm not 100% confident it works for other OS/CPU configurations.

Currently, programs do not support `Ctrl+C` to interrupt the program, I didn't know this was something was something that needed to be implemented.


