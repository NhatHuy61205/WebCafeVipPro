
import hashlib
from dataclasses import dataclass
from typing import List, Tuple

from CafeApp.models import NhanVienCuaHang


@dataclass
class DrinkContext:
    name: str
    base_price: float
    desc: List[str]

class DrinkComponent:
    def get_price(self) -> float:
        raise NotImplementedError

    def get_desc(self) -> List[str]:
        raise NotImplementedError

class BaseDrink(DrinkComponent):
    def __init__(self, name: str, base_price: float):
        self.ctx = DrinkContext(name=name, base_price=base_price, desc=[])

    def get_price(self) -> float:
        return self.ctx.base_price

    def get_desc(self) -> List[str]:
        return list(self.ctx.desc)

class DrinkDecorator(DrinkComponent):
    def __init__(self, component: DrinkComponent):
        self.component = component

    def get_price(self) -> float:
        return self.component.get_price()

    def get_desc(self) -> List[str]:
        return self.component.get_desc()

class SizeDecorator(DrinkDecorator):
    # S: +0, M: +5000, L: +10000
    PRICE = {"S": 0, "M": 5000, "L": 10000}
    LABEL = {"S": "Size S", "M": "Size M (+5k)", "L": "Size L (+10k)"}

    def __init__(self, component: DrinkComponent, size: str):
        super().__init__(component)
        self.size = size if size in self.PRICE else "S"

    def get_price(self) -> float:
        return super().get_price() + self.PRICE[self.size]

    def get_desc(self) -> List[str]:
        return super().get_desc() + [self.LABEL[self.size]]

class SugarDecorator(DrinkDecorator):
    LABEL = {"0": "0% đường", "30": "30% đường", "50": "50% đường", "70": "70% đường", "100": "100% đường"}

    def __init__(self, component: DrinkComponent, sugar: str):
        super().__init__(component)
        self.sugar = sugar if sugar in self.LABEL else "70"

    def get_desc(self) -> List[str]:
        return super().get_desc() + [self.LABEL[self.sugar]]

class IceDecorator(DrinkDecorator):
    LABEL = {"0": "0% đá", "50": "50% đá", "70": "70% đá", "100": "100% đá"}

    def __init__(self, component: DrinkComponent, ice: str):
        super().__init__(component)
        self.ice = ice if ice in self.LABEL else "70"

    def get_desc(self) -> List[str]:
        return super().get_desc() + [self.LABEL[self.ice]]

class ToppingDecorator(DrinkDecorator):
    PRICE = {"TRAN_CHAU": 5000, "PUDDING": 7000, "KEM_CHEESE": 10000}
    LABEL = {"TRAN_CHAU": "Trân châu (+5k)", "PUDDING": "Pudding (+7k)", "KEM_CHEESE": "Kem cheese (+10k)"}

    def __init__(self, component: DrinkComponent, topping_code: str):
        super().__init__(component)
        self.topping_code = topping_code

    def get_price(self) -> float:
        return super().get_price() + self.PRICE.get(self.topping_code, 0)

    def get_desc(self) -> List[str]:
        label = self.LABEL.get(self.topping_code)
        return super().get_desc() + ([label] if label else [])

def build_drink(mon, size: str, duong: str, da: str, toppings: List[str]):
    drink = BaseDrink(name=mon.name, base_price=float(mon.gia))
    drink = SizeDecorator(drink, size)
    drink = SugarDecorator(drink, duong)
    drink = IceDecorator(drink, da)

    for t in toppings:
        drink = ToppingDecorator(drink, t)

    unit_price = drink.get_price()
    desc_list = drink.get_desc()
    return unit_price, desc_list

# def auth_user(username, password):
#     password = hashlib.md5(password.encode("utf-8")).hexdigest()
#     return NhanVienCuaHang.query.filter(
#         NhanVienCuaHang.tenDangNhap == username,
#         NhanVienCuaHang.matKhau == password
#     ).first()

def auth_user(username, password):
    return NhanVienCuaHang.query.filter(
        NhanVienCuaHang.tenDangNhap == username,
        NhanVienCuaHang.matKhau == password
    ).first()
