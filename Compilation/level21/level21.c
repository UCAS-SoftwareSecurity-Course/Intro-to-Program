#include <stdio.h>

int findMax(int a, int b) {
    return (a > b) ? a : b;
}

int main() {
    int num1 = 10;
    int num2 = 20;
    int max_num = findMax(num1, num2);
    printf("The maximum between %d and %d is %d\n", num1, num2, max_num);
    return 0;
}
