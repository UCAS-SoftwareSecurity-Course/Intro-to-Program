#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <stdlib.h>
#include <assert.h>

int *stack_addr_foo;
int *stack_addr_bar;
int *stack_addr_boo;

int *heap_addr_foo;
int *heap_addr_bar;
int *heap_addr_boo;

void execute_function(char* func_name, char* remaining_input);

void foo(char* remaining_input) {
    int var = 0x1337;
    stack_addr_foo = &var;
    heap_addr_foo = malloc(0x100);
    printf("This is function foo.\n");
    printf("The address of `stack_addr_foo`: %p\n", stack_addr_foo);
    printf("The address of `heap_addr_foo`: %p\n", heap_addr_foo);
    execute_function(remaining_input, strtok(NULL, "-"));
}

void bar(char* remaining_input) {
    int var = 0x1337;
    stack_addr_bar = &var;
    heap_addr_bar = malloc(0x100);
    printf("This is function bar.\n");
    printf("The address of `stack_addr_bar`: %p\n", stack_addr_bar);
    printf("The address of `heap_addr_bar`: %p\n", heap_addr_bar);
    execute_function(remaining_input, strtok(NULL, "-"));
}

void boo(char* remaining_input) {
    int var = 0x1337;
    stack_addr_boo = &var;
    heap_addr_boo = malloc(0x100);
    printf("This is function boo.\n");
    printf("The address of `stack_addr_boo`: %p\n", stack_addr_boo);
    printf("The address of `heap_addr_boo`: %p\n", heap_addr_boo);
    execute_function(remaining_input, strtok(NULL, "-"));
}

void execute_function(char* func_name, char* remaining_input) {
    if (func_name == NULL) {
        return;
    }
    if (strcmp(func_name, "foo") == 0) {
        foo(remaining_input);
    } else if (strcmp(func_name, "bar") == 0) {
        bar(remaining_input);
    } else if (strcmp(func_name, "boo") == 0) {
        boo(remaining_input);
    } else {
        printf("Invalid function name: %s\n", func_name);
    }
}

int main() {
    char buffer[0x100];

    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);

    printf("Welcome to level42!\n");
    printf("Current process's PID: %d\n", getpid());

    for (int i = 0; i < 6; i++) {
        if (i == 0) printf("Current assertion is: `stack_addr_foo < stack_addr_bar && stack_addr_foo > stack_addr_boo`\n");
        else if (i == 1) printf("Current assertion is: `stack_addr_foo > stack_addr_bar && stack_addr_foo < stack_addr_boo`\n");
        else if (i == 2) printf("Current assertion is: `stack_addr_foo < stack_addr_bar && stack_addr_bar < stack_addr_boo`\n");
        else if (i == 3) printf("Current assertion is: `heap_addr_foo < heap_addr_bar && heap_addr_foo > heap_addr_boo`\n");
        else if (i == 4) printf("Current assertion is: `heap_addr_foo > heap_addr_bar && heap_addr_foo < heap_addr_boo`\n");
        else if (i == 5) printf("Current assertion is: `heap_addr_foo < heap_addr_bar && heap_addr_bar < heap_addr_boo`\n");

        printf("Please input the correct function chain to pass the assertion (e.g. foo-bar-boo): \n");
        scanf("%20s", buffer);

        char* token = strtok(buffer, "-");
        execute_function(token, strtok(NULL, "-"));

        if (i == 0) {
            assert(stack_addr_foo < stack_addr_bar);
            assert(stack_addr_foo > stack_addr_boo);
        } else if (i == 1) {
            assert(stack_addr_foo > stack_addr_bar);
            assert(stack_addr_foo < stack_addr_boo);
        } else if (i == 2) {
            assert(stack_addr_foo < stack_addr_bar);
            assert(stack_addr_bar < stack_addr_boo);
        } else if (i == 3) {
            assert(heap_addr_foo < heap_addr_bar);
            assert(heap_addr_foo > heap_addr_boo);
        } else if (i == 4) {
            assert(heap_addr_foo > heap_addr_bar);
            assert(heap_addr_foo < heap_addr_boo);
        } else if (i == 5) {
            assert(heap_addr_foo < heap_addr_bar);
            assert(heap_addr_bar < heap_addr_boo);
        }

        printf("Good job!\n");
        printf("Next assertion!\n");
    }

    printf("Congratulation!\n");
    
    return 0;
}