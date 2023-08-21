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
    int x = 10;
    int y = 2 * x + 1;
    int z;
    if ( y > 11 ) {
        x = 666;
        foo();
    } else {
        y = 888;
        bar(y);
    }
    
    while (y > 0) {
        z = x + 1;
        y = y - (z % 2);
    }

    return 0;
}