import unittest

from shipping import shipping_fee


class ShippingTests(unittest.TestCase):
    def test_below_threshold(self):
        self.assertEqual(shipping_fee(29999), 3000)

    def test_at_threshold(self):
        self.assertEqual(shipping_fee(30000), 0)

    def test_above_threshold(self):
        self.assertEqual(shipping_fee(30001), 0)

    def test_zero(self):
        self.assertEqual(shipping_fee(0), 3000)

    def test_negative(self):
        with self.assertRaises(ValueError):
            shipping_fee(-1)


if __name__ == "__main__":
    unittest.main()
