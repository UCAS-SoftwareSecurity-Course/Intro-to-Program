; ModuleID = 'level23.ll'
source_filename = "level23.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-pc-linux-gnu"

@.str = private unnamed_addr constant [13 x i8] c"This is foo\0A\00", align 1
@.str.1 = private unnamed_addr constant [16 x i8] c"This is bar %d\0A\00", align 1

; Function Attrs: noinline nounwind sspstrong uwtable
define dso_local void @foo() #0 {
  %1 = call i32 (ptr, ...) @printf(ptr noundef @.str)
  ret void
}

declare i32 @printf(ptr noundef, ...) #1

; Function Attrs: noinline nounwind sspstrong uwtable
define dso_local void @bar(i32 noundef %0) #0 {
  %2 = call i32 (ptr, ...) @printf(ptr noundef @.str.1, i32 noundef %0)
  ret void
}

; Function Attrs: noinline nounwind sspstrong uwtable
define dso_local i32 @main() #0 {
  br label %1

1:                                                ; preds = %0
  call void @foo()
  br label %2

2:                                                ; preds = %1
  br label %3

3:                                                ; preds = %5, %2
  %.1 = phi i32 [ 21, %2 ], [ %6, %5 ]
  %4 = icmp sgt i32 %.1, 0
  br i1 %4, label %5, label %7

5:                                                ; preds = %3
  %6 = sub nsw i32 %.1, 1
  br label %3, !llvm.loop !6

7:                                                ; preds = %3
  ret i32 0
}

attributes #0 = { noinline nounwind sspstrong uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
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
