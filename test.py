# while True:
#     n = int(input("請輸入一個正偶數："))
#     if n % 2 == 0 and n > 0:
#         break
#     else:
#         print("請重新輸入偶數！")
# m = 2
# summ = 0
# while m <= n:
#     summ += m
#     m += 2
# print(f"從 2 到 {n} 的所有正偶數的總和是：{summ}")  # 輸出總和

# ll = 3000
# n = 0
# while ll > 5:
#     ll /= 2
#     n += 1
# print("花了", n, "天")

# n = 0
# summ = 0
# while summ < 1000:
#     n += 1
#     summ += n
# print(summ, n)

# while True:
#     n = int(input("請輸入一個數："))
#     for i in range(n - 1, 0, -1):
#         m = True
#         for j in range(2, i):
#             if i % j == 0:
#                 m = False
#                 break
#         if m:
#             print(i, "是質數")
#             break
x = 0
while True:
    if x % 3 == 1 and x % 5 == 3 and x % 7 == 2:
        print(f"最少有 {x} 隻兔子")
        break
    x += 1