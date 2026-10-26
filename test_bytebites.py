"""Tests for ByteBites models, based on the spec and UML class diagram.

Run with: python -m unittest test_bytebites -v  (also compatible with pytest)
"""

import unittest
from datetime import datetime, timezone
from decimal import Decimal

from models import MenuItem, Menu, Order, Customer, Category


def make_item(name="Spicy Burger", price="9.99", category=Category.MAINS, rating=4.5):
    return MenuItem(name, price, category, rating)


class TestMenuItem(unittest.TestCase):
    def test_stores_name_price_category_rating(self):
        item = make_item()
        self.assertEqual(item.name, "Spicy Burger")
        self.assertEqual(item.price, Decimal("9.99"))
        self.assertIs(item.category, Category.MAINS)
        self.assertEqual(item.popularity_rating, 4.5)

    def test_price_accepts_int_float_str_decimal(self):
        for price in (5, 5.5, "5.50", Decimal("5.50")):
            self.assertIsInstance(make_item(price=price).price, Decimal)

    def test_float_price_has_no_binary_error(self):
        self.assertEqual(make_item(price=0.1).price, Decimal("0.1"))

    def test_boundary_values_allowed(self):
        self.assertEqual(make_item(price=0, rating=0).price, 0)
        self.assertEqual(make_item(rating=5).popularity_rating, 5)

    def test_empty_name_rejected(self):
        with self.assertRaises(ValueError):
            make_item(name="")

    def test_invalid_category_rejected(self):
        with self.assertRaises(TypeError):
            make_item(category="drinks")

    def test_negative_price_rejected(self):
        with self.assertRaises(ValueError):
            make_item(price=-1)

    def test_non_numeric_price_rejected(self):
        with self.assertRaises(ValueError):
            make_item(price="abc")

    def test_non_finite_price_rejected(self):
        for bad in ("NaN", "Infinity", float("inf")):
            with self.assertRaises(ValueError):
                make_item(price=bad)

    def test_rating_out_of_range_rejected(self):
        for bad in (-0.1, 5.1):
            with self.assertRaises(ValueError):
                make_item(rating=bad)


class TestCategory(unittest.TestCase):
    def test_has_expected_members(self):
        self.assertEqual(
            {c.name for c in Category}, {"DRINKS", "DESSERTS", "MAINS", "SIDES"}
        )


class TestMenu(unittest.TestCase):
    def setUp(self):
        self.menu = Menu()
        self.burger = make_item("Spicy Burger", "9.99", Category.MAINS, 4.8)
        self.soda = make_item("Large Soda", "2.50", Category.DRINKS, 4.0)
        self.cake = make_item("Cake", "5.00", Category.DESSERTS, 4.2)
        self.tea = make_item("Iced Tea", "2.00", Category.DRINKS, 3.5)

    def test_new_menu_is_empty(self):
        self.assertEqual(self.menu.get_all_items(), [])

    def test_add_and_get_all_items_preserves_order(self):
        for item in (self.burger, self.soda, self.cake):
            self.menu.add_item(item)
        self.assertEqual(self.menu.get_all_items(), [self.burger, self.soda, self.cake])

    def test_filter_by_category(self):
        for item in (self.burger, self.soda, self.cake, self.tea):
            self.menu.add_item(item)
        self.assertEqual(self.menu.filter_by_category(Category.DRINKS), [self.soda, self.tea])
        self.assertEqual(self.menu.filter_by_category(Category.DESSERTS), [self.cake])

    def test_filter_with_no_matches_returns_empty(self):
        self.menu.add_item(self.burger)
        self.assertEqual(self.menu.filter_by_category(Category.SIDES), [])

    def test_filter_on_empty_menu(self):
        self.assertEqual(self.menu.filter_by_category(Category.DRINKS), [])

    def test_filter_does_not_modify_menu(self):
        self.menu.add_item(self.burger)
        self.menu.add_item(self.soda)
        self.menu.filter_by_category(Category.DRINKS)
        self.assertEqual(len(self.menu.get_all_items()), 2)

    def test_filter_rejects_non_category(self):
        with self.assertRaises(TypeError):
            self.menu.filter_by_category("drinks")

    def test_add_item_rejects_non_menu_item(self):
        with self.assertRaises(TypeError):
            self.menu.add_item("burger")

    def test_returned_list_is_a_copy(self):
        self.menu.add_item(self.burger)
        self.menu.get_all_items().clear()
        self.menu.items.append(self.soda)
        self.assertEqual(self.menu.get_all_items(), [self.burger])


class TestOrder(unittest.TestCase):
    def test_new_order_is_empty_with_zero_total(self):
        order = Order()
        self.assertEqual(order.items, [])
        self.assertEqual(order.calculate_total(), Decimal("0"))

    def test_created_at_is_timezone_aware_and_recent(self):
        before = datetime.now(timezone.utc)
        order = Order()
        after = datetime.now(timezone.utc)
        self.assertIsNotNone(order.created_at.tzinfo)
        self.assertTrue(before <= order.created_at <= after)

    def test_add_items_and_total(self):
        order = Order()
        order.add_item(make_item("Spicy Burger", "9.99"))
        order.add_item(make_item("Large Soda", "2.50", Category.DRINKS))
        self.assertEqual(len(order.items), 2)
        self.assertEqual(order.calculate_total(), Decimal("12.49"))

    def test_total_is_exact_decimal(self):
        order = Order()
        for _ in range(3):
            order.add_item(make_item(price=0.1))
        self.assertEqual(order.calculate_total(), Decimal("0.3"))

    def test_duplicate_items_counted_each_time(self):
        order = Order()
        soda = make_item("Large Soda", "2.50", Category.DRINKS)
        order.add_item(soda)
        order.add_item(soda)
        self.assertEqual(order.calculate_total(), Decimal("5.00"))

    def test_free_item_does_not_change_total(self):
        order = Order()
        order.add_item(make_item(price="4.00"))
        order.add_item(make_item("Free Sample", 0))
        self.assertEqual(order.calculate_total(), Decimal("4.00"))

    def test_remove_item_updates_total(self):
        order = Order()
        burger = make_item(price="9.99")
        soda = make_item("Large Soda", "2.50", Category.DRINKS)
        order.add_item(burger)
        order.add_item(soda)
        order.remove_item(burger)
        self.assertEqual(order.items, [soda])
        self.assertEqual(order.calculate_total(), Decimal("2.50"))

    def test_remove_one_of_duplicates_removes_single_copy(self):
        order = Order()
        soda = make_item("Large Soda", "2.50", Category.DRINKS)
        order.add_item(soda)
        order.add_item(soda)
        order.remove_item(soda)
        self.assertEqual(order.items, [soda])

    def test_remove_missing_item_raises(self):
        with self.assertRaises(ValueError):
            Order().remove_item(make_item())

    def test_add_item_rejects_non_menu_item(self):
        with self.assertRaises(TypeError):
            Order().add_item("burger")

    def test_items_returns_copy(self):
        order = Order()
        order.add_item(make_item())
        order.items.clear()
        self.assertEqual(len(order.items), 1)


class TestCustomer(unittest.TestCase):
    def make_order(self):
        order = Order()
        order.add_item(make_item())
        return order

    def test_stores_name_and_age(self):
        customer = Customer("Alex", 20)
        self.assertEqual(customer.name, "Alex")
        self.assertEqual(customer.age, 20)

    def test_new_customer_has_no_history(self):
        customer = Customer("Alex", 20)
        self.assertFalse(customer.has_purchase_history())
        self.assertEqual(customer.purchase_history, [])

    def test_add_order_records_history(self):
        customer = Customer("Alex", 20)
        order = self.make_order()
        customer.add_order(order)
        self.assertTrue(customer.has_purchase_history())
        self.assertEqual(customer.purchase_history, [order])

    def test_history_keeps_multiple_orders_in_sequence(self):
        customer = Customer("Alex", 20)
        first, second = self.make_order(), self.make_order()
        customer.add_order(first)
        customer.add_order(second)
        self.assertEqual(customer.purchase_history, [first, second])

    def test_empty_name_rejected(self):
        with self.assertRaises(ValueError):
            Customer("", 20)

    def test_non_integer_age_rejected(self):
        for bad in ("20", 20.5, None, True):
            with self.assertRaises(TypeError):
                Customer("Alex", bad)

    def test_add_non_order_rejected(self):
        with self.assertRaises(TypeError):
            Customer("Alex", 20).add_order("order")

    def test_empty_order_rejected(self):
        customer = Customer("Alex", 20)
        with self.assertRaises(ValueError):
            customer.add_order(Order())
        self.assertFalse(customer.has_purchase_history())

    def test_history_returns_copy(self):
        customer = Customer("Alex", 20)
        customer.add_order(self.make_order())
        customer.purchase_history.clear()
        self.assertTrue(customer.has_purchase_history())


class TestHappyPath(unittest.TestCase):
    def test_browse_filter_order_and_record_purchase(self):
        menu = Menu()
        burger = make_item("Spicy Burger", "9.99", Category.MAINS, 4.8)
        soda = make_item("Large Soda", "2.50", Category.DRINKS, 4.0)
        cake = make_item("Cake", "5.00", Category.DESSERTS, 4.2)
        for item in (burger, soda, cake):
            menu.add_item(item)

        customer = Customer("Alex", 20)
        self.assertFalse(customer.has_purchase_history())

        order = Order()
        order.add_item(burger)
        for drink in menu.filter_by_category(Category.DRINKS):
            order.add_item(drink)
        self.assertEqual(order.calculate_total(), Decimal("12.49"))

        customer.add_order(order)
        self.assertTrue(customer.has_purchase_history())
        self.assertEqual(customer.purchase_history[0].calculate_total(), Decimal("12.49"))


if __name__ == "__main__":
    unittest.main()