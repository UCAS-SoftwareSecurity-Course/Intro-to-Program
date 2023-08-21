; ModuleID = './solve_level15.c'
source_filename = "./solve_level15.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-pc-linux-gnu"

@hello_world_str = dso_local global [12 x i8] c"Hello World\00", align 1
@__const.main.hello_hackers_str = private unnamed_addr constant [20 x i8] c"Hello Hackers\00\00\00\00\00\00\00", align 16
@.str = private unnamed_addr constant [15 x i8] c"Hello Level 15\00", align 1
@.str.1 = private unnamed_addr constant [27 x i8] c"This is format string: %s\0A\00", align 1
@__const.main.hello_llvm_str = private unnamed_addr constant [20 x i8] c"Hello llvm ir\00\00\00\00\00\00\00", align 16

; Function Attrs: noinline nounwind optnone sspstrong uwtable
define dso_local i32 @main() #0 {
  %1 = alloca i32, align 4
  %2 = alloca [20 x i8], align 16
  %3 = alloca ptr, align 8
  %4 = alloca [20 x i8], align 16
  store i32 0, ptr %1, align 4
  call void @llvm.memcpy.p0.p0.i64(ptr align 16 %2, ptr align 16 @__const.main.hello_hackers_str, i64 20, i1 false)
  store ptr @.str, ptr %3, align 8
  %5 = getelementptr inbounds [20 x i8], ptr %2, i64 0, i64 0
  %6 = call i32 (ptr, ...) @printf(ptr noundef @.str.1, ptr noundef %5)
  call void @llvm.memcpy.p0.p0.i64(ptr align 16 %4, ptr align 16 @__const.main.hello_llvm_str, i64 20, i1 false)
  %7 = getelementptr inbounds [20 x i8], ptr %4, i64 0, i64 0
  %8 = call i32 (ptr, ...) @printf(ptr noundef @.str.1, ptr noundef %7)
  ret i32 0
}

; Function Attrs: argmemonly nocallback nofree nounwind willreturn
declare void @llvm.memcpy.p0.p0.i64(ptr noalias nocapture writeonly, ptr noalias nocapture readonly, i64, i1 immarg) #1

declare i32 @printf(ptr noundef, ...) #2

attributes #0 = { noinline nounwind optnone sspstrong uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #1 = { argmemonly nocallback nofree nounwind willreturn }
attributes #2 = { "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }

!llvm.module.flags = !{!0, !1, !2, !3, !4}
!llvm.ident = !{!5}

!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{i32 7, !"PIC Level", i32 2}
!2 = !{i32 7, !"PIE Level", i32 2}
!3 = !{i32 7, !"uwtable", i32 2}
!4 = !{i32 7, !"frame-pointer", i32 2}
!5 = !{!"clang version 15.0.7"}
