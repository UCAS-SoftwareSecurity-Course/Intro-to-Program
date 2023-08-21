extern int printf(const char *, ...);

char hello_world_str[] = "Hello World";

int main() {
    char hello_hackers_str[20] = "Hello Hackers";
    char *hello_level_str = "Hello Level 15";

    printf("This is format string: %s\n", hello_hackers_str);

    char hello_llvm_str[20] = "Hello ????";

    return 0;
}