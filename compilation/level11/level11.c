extern int printf(const char *, ...);

void foo() {
    printf("This is foo\n");
    return;
}

void bar(int var) {
    printf("This is bar\n");
    return;
}

int main() {
    int x;
    int y = 2 * x + 1;
    if ( x > 10 ) {
        x = 666;
    }
    
    return 0;
}