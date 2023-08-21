int main() {
    int syscall_success = 1;
    if (!syscall_success) {
        int syscall_ret = 0;
        do { if (syscall_ret) { printf("Error message\n"); return 1; } } while (0);
    } else {
        printf("syscall success\n");
    }
    return 0;
}