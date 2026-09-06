# OOPs learning in python
class Car:
    def __init__(self, userbrand , usermodel):
        self.brand = userbrand
        self.model = usermodel
my_car = Car("toyota", "corolla")
print(my_car.brand, my_car.model)