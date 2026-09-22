# OOPs learning in python
class Car:
    def __init__(self, userbrand , usermodel):
        self.brand = userbrand
        self.model = usermodel
my_car = Car("toyota", "corolla")
print(my_car.brand, my_car.model)

my_new_car = Car("tata" , "safari")
print(my_new_car.model , my_new_car.brand)

class Student:
    def __init__(self):
        self.name = "hridyansh"

s1 = Student()
print(s1.name)