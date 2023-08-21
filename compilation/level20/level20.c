#include <stdio.h>

void sayHello() {
    printf("Hello, world!\n");
}

void incrementAndPrint() {
    int count = 0;

    count ++;
    printf("Count: %d\n", count);
}

int main() {
    sayHello();

    incrementAndPrint();
    incrementAndPrint();
    incrementAndPrint();

    return 0;
}