#include "rt.h"

int main(int argc, char** argv) {
    int b = _bril_parse_bool(argv, 1);
    _bril_print_bool(b);
    _bril_print_end();
}