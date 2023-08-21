extern int printf(const char *, ...);

void foo() {
    printf("This is foo\n");
    return;
}

void bar(int var) {
    printf("This is bar %d\n", var);
    return;
}

int main() {
    int x;
    int y = 2 * x + 1;
    if ( y > 11 ) {
        x = 666;
        foo();
    }
    
    return 0;
}