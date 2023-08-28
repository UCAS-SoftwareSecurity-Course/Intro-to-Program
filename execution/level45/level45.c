#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <stdlib.h>
#include <assert.h>

struct poss_st {
    unsigned int index;
    char name[0x10];
    struct poss_st *next;
};

void test_stack_variables() {
    void *rbp = NULL;
    asm volatile ("mov %%rbp, %0" : "=r" (rbp));
    printf("RBP of function `test_stack_variables` is: %p\n", rbp); 

    // stack variables declaration
    unsigned int a = 0x11;
    unsigned long b = 0x22;
    char buf[0x10] = "Hello World!";
    struct poss_st header = {0x33, "PoSS", NULL};
    struct poss_st tail = {0x44, "PoSS", &header};

    void *range_start, *range_end;

    // assertions
    printf("Input the range of stack variable `a`\n");
    scanf("%p-%p", &range_start, &range_end);
    int size = range_end - range_start;
    unsigned int value = *(unsigned int*)(range_start);
    assert(size == 4);
    assert(value == a);

    printf("Input the range of stack variable `b`\n");
    scanf("%p-%p", &range_start, &range_end);
    size = range_end - range_start;
    unsigned long value2 = *(unsigned long*)(range_start);
    assert(size == 8);
    assert(value2 == b);

    printf("Input the range of stack variable `buf`\n");
    scanf("%p-%p", &range_start, &range_end);
    size = range_end - range_start;
    char *value3 = (char*)(range_start);
    assert(size == 0x10);
    assert(strcmp(value3, buf) == 0);

    printf("Input the range of stack variable `header.index`\n");
    scanf("%p-%p", &range_start, &range_end);
    size = range_end - range_start;
    unsigned int value4 = *(unsigned int*)(range_start);
    assert(size == 4);
    assert(value4 == header.index);

    printf("Input the range of stack variable `tail.next`\n");
    scanf("%p-%p", &range_start, &range_end);
    size = range_end - range_start;
    struct poss_st *value5 = *(struct poss_st**)(range_start);
    assert(size == 8);
    assert(tail.next == &header);
    assert(value5 == tail.next);

    return;
}

int main() {

    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);

    printf("Welcome to level45!\n");
    printf("Current process's PID: %d\n", getpid());

    test_stack_variables();

    printf("Congratulation!\n");
    
    return 0;
}