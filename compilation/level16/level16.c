int main() {
    int array_1[0x10];
    int array_2[0x10] = {1, 2, 3, 4, 5};
    
    array_1[0] = 1;
    array_1[1] = 2;

    int* p_1 = array_1;
    int* p_2 = array_2;
    int** p_3 = &p_1;

    *(p_1 + 2) = 3;
    **p_3 = 4;

    return 0; 
}