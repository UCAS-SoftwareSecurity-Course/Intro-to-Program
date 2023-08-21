void SoftwareSecCourse() {
    int total_students = 90;
    int passing_students = 0;
    int failing_students = 0;
    int grades[90];
    for(int i = 0; i < 90; i++) {
        if(grades[i] >= 60) {
            passing_students++;
        } else {
            failing_students++;
        }
    }
    float pass_rate = (float)passing_students / total_students;
    float fail_rate = (float)failing_students / total_students;
    printf("%d students passed the grade limit of %d\n", passing_students, 60);
}