# -*- coding: utf-8 -*-
import unittest
import sqlite3
import os
from gilded_rose import Item, GildedRose, ItemUpdater
from contextlib import closing

class GildedRoseTest(unittest.TestCase):
    def test_regular_item_before_sell_date(self):
        item = Item(name="Regular Item", sell_in=10, quality=20)
        gilded_rose = GildedRose([item])
        gilded_rose.update_quality()
        self.assertEqual(item.sell_in, 9)
        self.assertEqual(item.quality, 19)

    def test_regular_item_on_sell_date(self):
        item = Item(name="Regular Item", sell_in=0, quality=20)
        gilded_rose = GildedRose([item])
        gilded_rose.update_quality()
        self.assertEqual(item.sell_in, -1)
        self.assertEqual(item.quality, 18)

    def test_regular_item_after_sell_date(self):
        item = Item(name="Regular Item", sell_in=-1, quality=20)
        gilded_rose = GildedRose([item])
        gilded_rose.update_quality()
        self.assertEqual(item.sell_in, -2)
        self.assertEqual(item.quality, 18)

    def test_quality_never_negative(self):
        item = Item(name="Regular Item", sell_in=5, quality=0)
        gilded_rose = GildedRose([item])
        gilded_rose.update_quality()
        self.assertEqual(item.sell_in, 4)
        self.assertEqual(item.quality, 0)

    def test_aged_brie_before_sell_date(self):
        item = Item(name="Aged Brie", sell_in=2, quality=0)
        gilded_rose = GildedRose([item])
        gilded_rose.update_quality()
        self.assertEqual(item.sell_in, 1)
        self.assertEqual(item.quality, 1)

    def test_aged_brie_after_sell_date(self):
        item = Item(name="Aged Brie", sell_in=0, quality=10)
        gilded_rose = GildedRose([item])
        gilded_rose.update_quality()
        self.assertEqual(item.sell_in, -1)
        self.assertEqual(item.quality, 12)

    def test_quality_maximum_limit(self):
        item = Item(name="Aged Brie", sell_in=5, quality=50)
        gilded_rose = GildedRose([item])
        gilded_rose.update_quality()
        self.assertEqual(item.sell_in, 4)
        self.assertEqual(item.quality, 50)

    def test_sulfuras_never_changes(self):
        item = Item(name="Sulfuras, Hand of Ragnaros", sell_in=0, quality=80)
        gilded_rose = GildedRose([item])
        gilded_rose.update_quality()
        self.assertEqual(item.sell_in, 0)
        self.assertEqual(item.quality, 80)

    def test_backstage_passes_more_than_10_days(self):
        item = Item(name="Backstage passes to a TAFKAL80ETC concert", sell_in=11, quality=20)
        gilded_rose = GildedRose([item])
        gilded_rose.update_quality()
        self.assertEqual(item.sell_in, 10)
        self.assertEqual(item.quality, 21)

    def test_backstage_passes_10_days_or_less(self):
        item = Item(name="Backstage passes to a TAFKAL80ETC concert", sell_in=10, quality=20)
        gilded_rose = GildedRose([item])
        gilded_rose.update_quality()
        self.assertEqual(item.sell_in, 9)
        self.assertEqual(item.quality, 22)

    def test_backstage_passes_5_days_or_less(self):
        item = Item(name="Backstage passes to a TAFKAL80ETC concert", sell_in=5, quality=20)
        gilded_rose = GildedRose([item])
        gilded_rose.update_quality()
        self.assertEqual(item.sell_in, 4)
        self.assertEqual(item.quality, 23)

    def test_backstage_passes_after_concert(self):
        item = Item(name="Backstage passes to a TAFKAL80ETC concert", sell_in=0, quality=20)
        gilded_rose = GildedRose([item])
        gilded_rose.update_quality()
        self.assertEqual(item.sell_in, -1)
        self.assertEqual(item.quality, 0)

    def test_conjured_items_degrade_twice_as_fast(self):
        item = Item(name="Conjured Mana Cake", sell_in=3, quality=6)
        gilded_rose = GildedRose([item])
        gilded_rose.update_quality()
        self.assertEqual(item.sell_in, 2)
        self.assertEqual(item.quality, 4)

    def test_conjured_items_after_sell_date(self):
        item = Item(name="Conjured Mana Cake", sell_in=0, quality=6)
        gilded_rose = GildedRose([item])
        gilded_rose.update_quality()
        self.assertEqual(item.sell_in, -1)
        self.assertEqual(item.quality, 2)



   

if __name__ == '__main__':
    unittest.main()