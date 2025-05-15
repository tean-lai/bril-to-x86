#pragma once

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// Print routines
void _bril_print_int(int64_t i);
void _bril_print_bool(char i);
void _bril_print_float(double f);
void _bril_print_sep(void);
void _bril_print_end(void);

// Parsing routines
int64_t _bril_parse_int(char **args, int64_t idx);
char    _bril_parse_bool(char **args, int64_t idx);
double  _bril_parse_float(char **args, int64_t idx);

// Memory management
void * _bril_alloc(int64_t size, int64_t bytes);
void   _bril_free(void *ptr);

#ifdef __cplusplus
}
#endif