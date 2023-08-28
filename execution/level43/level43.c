#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <stdlib.h>
#include <assert.h>

unsigned long main_rbp = 0;

void test_stack_frame() {
    char buffer[0x10];
    int offset;
    unsigned long rbp;

    asm volatile ("mov %%rbp, %0" : "=r" (rbp));
    printf("`test_stack_frame` rbp: %p\n", (void *)rbp);

    printf("Please input the offset of variable `buffer` and current stack frame's rbp: \n");
    scanf("%d", &offset);
    char* rbp_calc = buffer + offset;
    assert(rbp_calc == (char *)rbp);

    printf("Please input the offset of variable `buffer` and variable `offset`: \n");
    scanf("%d", &offset);
    char *offset_addr = buffer + offset;
    assert((void *)offset_addr == (void *)&offset);

    printf("Please input the offset of variable `buffer` and stack address where return address stored: \n");
    scanf("%d", &offset);
    unsigned long *ret_addr = *(unsigned long **)(buffer + offset);
    assert(ret_addr == (unsigned long *)0x4013f7);

    void* old_rbp;
    printf("Please input the value which stored in current stack frame's rbp: \n");
    scanf("%p", &old_rbp);
    assert(old_rbp == *(void **)rbp);

    return;
}


int main() {

    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);

    printf("Welcome to level43!\n");
    printf("Current process's PID: %d\n", getpid());

    asm volatile ("mov %%rbp, %0" : "=r" (main_rbp));

    printf("`main` rbp: %p\n", (void *)main_rbp);

    test_stack_frame();


    printf("Congratulation!\n");
    
    return 0;
}