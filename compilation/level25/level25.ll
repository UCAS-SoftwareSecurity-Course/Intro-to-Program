; ModuleID = 'level25.c'
source_filename = "level25.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-pc-linux-gnu"

@global_var = dso_local global i32 0, align 4
@global_array = dso_local global [16 x i8] zeroinitializer, align 16
@global_bar_var = internal global i32 666, align 4
@.str = private unnamed_addr constant [23 x i8] c"This is var in bar %d\0A\00", align 1
@.str.1 = private unnamed_addr constant [30 x i8] c"This is global_var in bar %d\0A\00", align 1
@.str.2 = private unnamed_addr constant [13 x i8] c"This is foo\0A\00", align 1

; Function Attrs: noinline nounwind optnone sspstrong uwtable
define dso_local void @bar(i32 noundef %0) #0 {
  %2 = alloca i32, align 4
  store i32 %0, ptr %2, align 4
  %3 = load i32, ptr %2, align 4
  %4 = load i32, ptr @global_bar_var, align 4
  %5 = add nsw i32 %4, %3
  store i32 %5, ptr @global_bar_var, align 4
  %6 = load i32, ptr %2, align 4
  %7 = call i32 (ptr, ...) @printf(ptr noundef @.str, i32 noundef %6)
  %8 = load i32, ptr @global_bar_var, align 4
  %9 = call i32 (ptr, ...) @printf(ptr noundef @.str.1, i32 noundef %8)
  ret void
}

declare i32 @printf(ptr noundef, ...) #1

; Function Attrs: noinline nounwind optnone sspstrong uwtable
define dso_local i32 @main() #0 {
  %1 = alloca i32, align 4
  %2 = alloca i32, align 4
  %3 = alloca i32, align 4
  %4 = alloca i32, align 4
  %5 = alloca i32, align 4
  store i32 0, ptr %1, align 4
  store i32 10, ptr %2, align 4
  %6 = load i32, ptr %2, align 4
  %7 = mul nsw i32 2, %6
  %8 = add nsw i32 %7, 1
  store i32 %8, ptr %3, align 4
  %9 = load i32, ptr %3, align 4
  %10 = icmp slt i32 %9, 11
  br i1 %10, label %11, label %12

11:                                               ; preds = %0
  store i32 666, ptr %2, align 4
  call void @foo()
  br label %14

12:                                               ; preds = %0
  store i32 888, ptr %3, align 4
  %13 = load i32, ptr %3, align 4
  call void @bar(i32 noundef %13)
  br label %14

14:                                               ; preds = %12, %11
  br label %15

15:                                               ; preds = %18, %14
  %16 = load i32, ptr %3, align 4
  %17 = icmp sgt i32 %16, 0
  br i1 %17, label %18, label %25

18:                                               ; preds = %15
  %19 = load i32, ptr %2, align 4
  %20 = add nsw i32 %19, 1
  store i32 %20, ptr %4, align 4
  %21 = load i32, ptr %3, align 4
  %22 = load i32, ptr %4, align 4
  %23 = srem i32 %22, 2
  %24 = sub nsw i32 %21, %23
  store i32 %24, ptr %3, align 4
  br label %15, !llvm.loop !6

25:                                               ; preds = %15
  store i32 0, ptr %5, align 4
  br label %26

26:                                               ; preds = %35, %25
  %27 = load i32, ptr %5, align 4
  %28 = icmp slt i32 %27, 16
  br i1 %28, label %29, label %38

29:                                               ; preds = %26
  %30 = load i32, ptr %5, align 4
  %31 = trunc i32 %30 to i8
  %32 = load i32, ptr %5, align 4
  %33 = sext i32 %32 to i64
  %34 = getelementptr inbounds [16 x i8], ptr @global_array, i64 0, i64 %33
  store i8 %31, ptr %34, align 1
  br label %35

35:                                               ; preds = %29
  %36 = load i32, ptr %5, align 4
  %37 = add nsw i32 %36, 1
  store i32 %37, ptr %5, align 4
  br label %26, !llvm.loop !8

38:                                               ; preds = %26
  ret i32 0
}

; Function Attrs: noinline nounwind optnone sspstrong uwtable
define internal void @foo() #0 {
  store i32 1638, ptr @global_var, align 4
  %1 = call i32 (ptr, ...) @printf(ptr noundef @.str.2)
  ret void
}

attributes #0 = { noinline nounwind optnone sspstrong uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #1 = { "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }

!llvm.module.flags = !{!0, !1, !2, !3, !4}
!llvm.ident = !{!5}

!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{i32 7, !"PIC Level", i32 2}
!2 = !{i32 7, !"PIE Level", i32 2}
!3 = !{i32 7, !"uwtable", i32 2}
!4 = !{i32 7, !"frame-pointer", i32 2}
!5 = !{!"clang version 15.0.7"}
!6 = distinct !{!6, !7}
!7 = !{!"llvm.loop.mustprogress"}
!8 = distinct !{!8, !7}
