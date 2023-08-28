#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <stdlib.h>
#include <assert.h>

unsigned long main_rbp = 0;

int test_call_convention(int a, int b, int c, int d, int e, int f, int g, int h, int choice) {
    unsigned long rdi, rsi, rdx, rcx, r8, r9;

    asm volatile ("mov %%rdi, %0" : "=r" (rdi));
    asm volatile ("mov %%rsi, %0" : "=r" (rsi));
    asm volatile ("mov %%rdx, %0" : "=r" (rdx));
    asm volatile ("mov %%rcx, %0" : "=r" (rcx));
    asm volatile ("mov %%r8, %0" : "=r" (r8));
    asm volatile ("mov %%r9, %0" : "=r" (r9));


    assert(r9 == 66);
    assert(r8 == 55);
    assert(rdx == 33);
    assert(rdi == 11);
    assert(rcx == 44);
    assert(rsi == 22);

    assert(*(int *)((void **)(&rdi) + 5) == 88);
    assert(*(int *)((void **)(&rdi) + 4) == 77);

    if (choice == 1)
        return a + b + c + d + e + f + g + h;
    else if (choice == 2)
        return a * b * c + d * e * f - g * h;
    else
        return 0;
}


int main(int argc, char *argv[]) {

    if (argc != 10) {
        printf("Usage: %s <a> <b> <c> <d> <e> <f> <g> <h> <choice>\n", argv[0]);
        exit(0);
    }

    int a = atoi(argv[1]);
    int b = atoi(argv[2]);
    int c = atoi(argv[3]);
    int d = atoi(argv[4]);
    int e = atoi(argv[5]);
    int f = atoi(argv[6]);
    int g = atoi(argv[7]);
    int h = atoi(argv[8]);
    int choice = atoi(argv[9]);

    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);

    printf("Welcome to level44!\n");
    printf("Current process's PID: %d\n", getpid());

    test_call_convention(a, b, c, d, e, f, g, h, choice);
    unsigned long rax;
    asm volatile ("mov %%rax, %0" : "=r" (rax));
    assert(rax == 160930);

    printf("Congratulation!\n");
    
    return 0;
}