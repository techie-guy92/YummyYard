"""
Module to define categories and products data for testing purposes.
"""

#======================================= Category Database =============================================

primary_category_1 = {"name": "Junkfood", "parent": None}
primary_category_2 = {"name": "Dairy", "parent": None}
primary_category_3 = {"name": "Cream", "parent": primary_category_2}
primary_category_4 = {"name": "Cheese", "parent": primary_category_2}
primary_category_5 = {"name": "Milk", "parent": primary_category_2}
primary_category_6 = {"name": "Snack", "parent": primary_category_3}
primary_category_7 = {"name": "Chips", "parent": primary_category_3}


#======================================= Products Database =============================================

primary_product_1 = {"name": "Mihan 1000 ml", "category": primary_category_5, "price": 23500}
primary_product_2 = {"name": "Kaleh 990 ml", "category": primary_category_5, "price": 22800}
primary_product_3 = {"name": "Mihan 100 gm", "category": primary_category_3, "price": 44000}
primary_product_4 = {"name": "Kale 440 gm", "category": primary_category_4, "price": 64000}
primary_product_5 = {"name": "Cheetoze 100 gm", "category": primary_category_6, "price": 34000}
primary_product_6 = {"name": "Mazmaz 120 gm", "category": primary_category_6, "price": 31000}
primary_product_7 = {"name": "Cheetoze 100 gm", "category": primary_category_7, "price": 29000}
primary_product_8 = {"name": "Mazmaz 120 gm", "category": primary_category_7, "price": 56000}


#=======================================================================================================
