; ModuleID = './solve_level16.c'
source_filename = "./solve_level16.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-pc-linux-gnu"

; Function Attrs: noinline nounwind optnone sspstrong uwtable
define dso_local i32 @main() #0 {
  %1 = alloca i32, align 4
  %2 = alloca [16 x i32], align 16
  %3 = alloca [16 x i32], align 16
  %4 = alloca ptr, align 8
  %5 = alloca ptr, align 8
  %6 = alloca ptr, align 8
  store i32 0, ptr %1, align 4
  call void @llvm.memset.p0.i64(ptr align 16 %3, i8 0, i64 64, i1 false)
  %7 = getelementptr inbounds <{ i32, i32, i32, i32, i32, [11 x i32] }>, ptr %3, i32 0, i32 0
  store i32 1, ptr %7, align 16
  %8 = getelementptr inbounds <{ i32, i32, i32, i32, i32, [11 x i32] }>, ptr %3, i32 0, i32 1
  store i32 2, ptr %8, align 4
  %9 = getelementptr inbounds <{ i32, i32, i32, i32, i32, [11 x i32] }>, ptr %3, i32 0, i32 2
  store i32 3, ptr %9, align 8
  %10 = getelementptr inbounds <{ i32, i32, i32, i32, i32, [11 x i32] }>, ptr %3, i32 0, i32 3
  store i32 4, ptr %10, align 4
  %11 = getelementptr inbounds <{ i32, i32, i32, i32, i32, [11 x i32] }>, ptr %3, i32 0, i32 4
  store i32 5, ptr %11, align 16
  %12 = getelementptr inbounds [16 x i32], ptr %2, i64 0, i64 0
  store i32 1, ptr %12, align 16
  %13 = getelementptr inbounds [16 x i32], ptr %2, i64 0, i64 1
  store i32 2, ptr %13, align 4
  %14 = getelementptr inbounds [16 x i32], ptr %2, i64 0, i64 0
  store ptr %14, ptr %4, align 8
  %15 = getelementptr inbounds [16 x i32], ptr %3, i64 0, i64 0
  store ptr %15, ptr %5, align 8
  store ptr %4, ptr %6, align 8
  %16 = load ptr, ptr %4, align 8
  %17 = getelementptr inbounds i32, ptr %16, i64 2
  store i32 3, ptr %17, align 4
  %18 = load ptr, ptr %6, align 8
  %19 = load ptr, ptr %18, align 8
  store i32 4, ptr %19, align 4
  %20 = load ptr, ptr %5, align 8
  %21 = getelementptr inbounds i32, ptr %20, i64 8
  store i32 8, ptr %21, align 4
  ret i32 0
}

; Function Attrs: argmemonly nocallback nofree nounwind willreturn writeonly
declare void @llvm.memset.p0.i64(ptr nocapture writeonly, i8, i64, i1 immarg) #1

attributes #0 = { noinline nounwind optnone sspstrong uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #1 = { argmemonly nocallback nofree nounwind willreturn writeonly }

!llvm.module.flags = !{!0, !1, !2, !3, !4}
!llvm.ident = !{!5}

!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{i32 7, !"PIC Level", i32 2}
!2 = !{i32 7, !"PIE Level", i32 2}
!3 = !{i32 7, !"uwtable", i32 2}
!4 = !{i32 7, !"frame-pointer", i32 2}
!5 = !{!"clang version 15.0.7"}
