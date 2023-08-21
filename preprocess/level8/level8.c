#include "level8_1.h"
#include "solve_level8.h"

int main() {
    struct myMachine machine;
    struct myCPU cpu;
    cpu.rsp = 0x7fffffff;
    
    machine.cpu[0] = cpu;

    return 0;
}