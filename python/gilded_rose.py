import json
import logging
import os
import glob
import sqlite3
from contextlib import closing


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")



class Item:
    def __init__(self, id=None, name=None, sell_in=None, quality=None):
        self.id = id
        self.name = name
        self.sell_in = sell_in
        self.quality = quality

    def __repr__(self):
        return f"{self.id}: {self.name}, {self.sell_in}, {self.quality}"

    @classmethod
    def from_db_row(cls, row):
        return cls(row['id'], row['name'], row['sell_in'], row['quality'])

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'sell_in': self.sell_in,
            'quality': self.quality
        }

class ItemUpdater:
    CONFIG_DIR = os.path.join(os.path.dirname(__file__), "configs")
    _rules_cache = {}
    RULES = {}  

    @classmethod
    def _load_configs(cls):
        merged_config = {}
        config_files = sorted(glob.glob(os.path.join(cls.CONFIG_DIR, "items_config_v*.json")))

        for path in config_files:
            try:
                with open(path, "r") as file:
                    config = json.load(file)
                    for key, rule in config.items():
                        if key not in merged_config:  # Only extend, don't override existing
                            merged_config[key] = rule

                        # Set default max_quality if not specified
                        if "max_quality" not in merged_config[key]:
                            merged_config[key]["max_quality"] = 50

                        # Convert string lambda expressions to functions
                        if isinstance(rule.get("quality_change"), str) and "lambda" in rule["quality_change"]:
                            merged_config[key]["quality_change"] = eval(rule["quality_change"])
                        if isinstance(rule.get("after_sell_in_quality_change"), str) and "lambda" in rule["after_sell_in_quality_change"]:
                            merged_config[key]["after_sell_in_quality_change"] = eval(rule["after_sell_in_quality_change"])

                logging.info(f"Loaded config: {path}")
            except Exception as e:
                logging.error(f"Error loading config {path}: {e}")
        return merged_config

    @classmethod
    def initialize(cls):
        cls.RULES = cls._load_configs()

    @classmethod
    def update(cls, item):
        rules = cls._get_rules(item)

        item.sell_in += rules["sell_in_change"]
        if item.sell_in <= 0:
            cls._apply_quality_change(item, rules["after_sell_in_quality_change"])
        else:
            cls._apply_quality_change(item, rules["quality_change"])

        # Use the max_quality from rules instead of hardcoded 50
        item.quality = max(0, min(rules["max_quality"], item.quality))

        logging.info(f"Updated: {item}")

    @staticmethod
    def _apply_quality_change(item, change):
        if callable(change):
            item.quality += change(item)
        else:
            item.quality += change

    @classmethod
    def _get_rules(cls, item):
        if item.name in cls._rules_cache:
            return cls._rules_cache[item.name]

        for key in cls.RULES:
            if key in item.name:
                cls._rules_cache[item.name] = cls.RULES[key]
                return cls.RULES[key]

        cls._rules_cache[item.name] = cls.RULES["default"]
        return cls.RULES["default"]

ItemUpdater.initialize()

DATABASE = 'inventory.db'
SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    sell_in INTEGER NOT NULL,
    quality INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

class DatabaseManager:
    @staticmethod
    def get_db():
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn
    
    @staticmethod
    def initialize_db():
        with closing(DatabaseManager.get_db()) as conn:
            with conn:
                conn.executescript(SCHEMA)  # Ensure schema is set up
    
    @staticmethod
    def reset_items(items=None):
        DatabaseManager.initialize_db()
        with closing(DatabaseManager.get_db()) as conn:
            with conn:
                conn.execute("DELETE FROM items")  
                conn.execute("UPDATE sqlite_sequence SET seq=0 WHERE name='items'")  # Reset auto-increment
                if items:
                    conn.executemany(
                        "INSERT INTO items (name, sell_in, quality) VALUES (?, ?, ?)",
                        [(item.name, item.sell_in, item.quality) for item in items]
                    )
    
    @staticmethod
    def fetch_items_by_type():
        DatabaseManager.initialize_db()
        with closing(DatabaseManager.get_db()) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT name FROM items")  # Get all unique item types
            item_types = [row["name"] for row in cursor.fetchall()]
            
            for item_type in item_types:
                cursor.execute("SELECT * FROM items WHERE name = ?", (item_type,))
                yield item_type, [Item.from_db_row(row) for row in cursor.fetchall()]
    
    @staticmethod
    def bulk_update_items(items):
        DatabaseManager.initialize_db()
        with closing(DatabaseManager.get_db()) as conn:
            with conn:
                conn.executemany(
                    "UPDATE items SET sell_in = ?, quality = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    [(item.sell_in, item.quality, item.id) for item in items]
                )


class GildedRose:
    def __init__(self, items=None):
        # DatabaseManager.reset_items(items)
        self.items = items

    def update_quality(self):
        for item in self.items:
            ItemUpdater.update(item)
        # for item_type, items in DatabaseManager.fetch_items_by_type():            
        #     for item in items:
        #         ItemUpdater.update(item)
        #     DatabaseManager.bulk_update_items(items)
    



