num1 = int(input("enter a number: "))
num2 = int(input("enter a number: "))
sign = input("enter + - * / any of these: ")
if sign == '+':
    print(num1+num2)
elif sign == '-':
    print(num1-num2)
elif sign == '*':
    print(num1*num2)
elif sign == '/':
    print(num1/num2)
else:
    print("invalid sign try again!")