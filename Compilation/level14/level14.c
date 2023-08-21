extern char c;
int global_var = 10;

int main() {
    int x = 3;
    int y = 2;
    char *ptr = &c;

    global_var = 20;
    x = 1;
    y = x + (y * 2);

    return 0;
}