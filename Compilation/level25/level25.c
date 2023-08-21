extern int printf(const char *format, ...);

static int global_bar_var = 666; 
int global_var = 0;
char global_array[0x10] = {0};

static void foo() {
    global_var = 0x666;
    printf("This is foo\n");
    return;
}

void bar(int var) {
    global_bar_var += var;
    printf("This is var in bar %d\n", var);
    printf("This is global_var in bar %d\n", global_bar_var);
    return;
}

int main() {
    int x = 10;
    int y = 2 * x + 1;
    int z;
    if ( y < 11 ) {
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

    for (int i = 0; i < 0x10; i++)
        global_array[i] = i;
    

    return 0;
}