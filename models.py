"""Core data models for the ByteBites application."""

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum


class Category(Enum):
    DRINKS = "drinks"
    DESSERTS = "desserts"
    MAINS = "mains"
    SIDES = "sides"


class MenuItem:
    def __init__(
        self,
        name: str,
        price: Decimal | int | float | str,
        category: Category,
        popularity_rating: float,
    ) -> None:
        if not name:
            raise ValueError("Menu item name cannot be empty.")
        if not isinstance(category, Category):
            raise TypeError("category must be a Category.")

        try:
            normalized_price = Decimal(str(price))
        except (InvalidOperation, ValueError) as error:
            raise ValueError("price must be a valid decimal amount.") from error
        if not normalized_price.is_finite() or normalized_price < 0:
            raise ValueError("price must be a finite, non-negative amount.")
        if not 0 <= popularity_rating <= 5:
            raise ValueError("popularity_rating must be between 0 and 5.")

        self.name = name
        self.price = normalized_price
        self.category = category
        self.popularity_rating = popularity_rating


class Menu:
    def __init__(self) -> None:
        self._items: list[MenuItem] = []

    @property
    def items(self) -> list[MenuItem]:
        return self._items.copy()

    def add_item(self, item: MenuItem) -> None:
        if not isinstance(item, MenuItem):
            raise TypeError("item must be a MenuItem.")
        self._items.append(item)

    def get_all_items(self) -> list[MenuItem]:
        return self.items

    def filter_by_category(self, category: Category) -> list[MenuItem]:
        if not isinstance(category, Category):
            raise TypeError("category must be a Category.")
        return [item for item in self._items if item.category is category]


class Order:
    def __init__(self) -> None:
        self._items: list[MenuItem] = []
        self._created_at = datetime.now(timezone.utc)

    @property
    def items(self) -> list[MenuItem]:
        return self._items.copy()

    @property
    def created_at(self) -> datetime:
        return self._created_at

    def add_item(self, item: MenuItem) -> None:
        if not isinstance(item, MenuItem):
            raise TypeError("item must be a MenuItem.")
        self._items.append(item)

    def remove_item(self, item: MenuItem) -> None:
        try:
            self._items.remove(item)
        except ValueError as error:
            raise ValueError("item is not in this order.") from error

    def calculate_total(self) -> Decimal:
        return sum((item.price for item in self._items), Decimal("0"))


class Customer:
    def __init__(self, name: str, age: int) -> None:
        if not name:
            raise ValueError("Customer name cannot be empty.")
        if not isinstance(age, int) or isinstance(age, bool):
            raise TypeError("age must be an integer.")

        self.name = name
        self.age = age
        self._purchase_history: list[Order] = []

    @property
    def purchase_history(self) -> list[Order]:
        return self._purchase_history.copy()

    def add_order(self, order: Order) -> None:
        if not isinstance(order, Order):
            raise TypeError("order must be an Order.")
        if not order.items:
            raise ValueError("Cannot add an empty order to purchase history.")
        self._purchase_history.append(order)

    def has_purchase_history(self) -> bool:
        return bool(self._purchase_history)
