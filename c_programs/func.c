#include "rt.h"

int fact(int n) {
    if (n == 1) return 1;
    return n * fact(n - 1);
}

int main(int argc, char** argv) {
    _bril_print_int(fact(argc));
    _bril_print_end();
}