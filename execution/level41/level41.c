#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <assert.h>

int backdoor() {
    printf("This function is useful!\n");
    return 0;
}

int main() {
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);

    void *got_strlen = (void *)0x404008;
    void *target, *value;

    char key_buffer[0x20] = "PoSSLab_is_Easy!";
    unsigned int buffer_len;

    printf("Welcome to level40!\n");
    printf("Current process's PID: %d\n", getpid());

    printf("Following is a demo for plt lazy binding.\n");
    printf("The value in `strlen@got` before first call: %p\n", *(void **)got_strlen);
    printf("The value in `strlen@got` is the 2nd instruction of `strlen@plt`.\n");
    printf("Now we call strlen(\"%s\")\n", key_buffer);
    buffer_len = strlen(key_buffer);
    printf("The value in `strlen@got` after first call: %p\n", *(void **)got_strlen);
    printf("The value in `strlen@got` is the address of `strlen` function in libc.so.\n");

    printf("--------------------\n");

    printf("Now we will try how to hijack the got table.\n");
    printf("Please input the target memory address you want to hijack: \n");
    scanf("%p", &target);
    printf("Please input the value you want to write: \n");
    scanf("%p", &value);

    printf("Old value at %p: %p\n", target, *(void **)target);
    *(void **)target = value;
    printf("New value at %p: %p\n", target, *(void **)target);
    
    if (strcmp(key_buffer, "PoSSLab_is_Hard!")) {
        printf("You are not allowed to execute this program!\n");
    } else {
        printf("Congratulation!\n");
    }

    return 0;
}