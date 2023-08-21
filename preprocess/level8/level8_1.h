#include "solve_level8.h"

struct myMachine {
    struct myCPU cpu[4];
    unsigned long stack_mem[4][1024];
    unsigned long heap_mem[4][1024];
    unsigned long global_mem[1024];
};