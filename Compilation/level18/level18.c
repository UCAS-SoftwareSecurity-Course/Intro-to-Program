extern void* malloc(unsigned long);

struct Node {
    int data;
    struct Node* next;
};

int main() {
    struct Node* node_1 = (struct Node*)malloc(sizeof(struct Node));
    node_1->data = 0x1;
    node_1->next = 0;

    struct Node* node_2 = (struct Node*)malloc(sizeof(struct Node));
    node_2->data = 0x2;
    node_2->next = 0;
    
    struct Node header;

    return 0;
}