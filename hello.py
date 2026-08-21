numbers = [10, -5, 20, -3, 30]
for i in range(len(numbers)):
    if numbers[i] < 0:
        continue
    print(numbers[i])