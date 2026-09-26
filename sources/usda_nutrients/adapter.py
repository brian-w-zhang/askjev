"""USDA FoodData Central SR Legacy: pairwise "Gram for gram, which has more <nutrient>: A or B?" over a curated list
of plain, recognizable foods, truth = the food with the higher value per 100 g."""

from __future__ import annotations

import csv
import hashlib
import itertools
import re
import unicodedata
import zipfile
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "usda_nutrients"
URL = "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_sr_legacy_food_csv_2018-04.zip"
ZIP = "FoodData_Central_sr_legacy_food_csv_2018-04.zip"
DIR = "FoodData_Central_sr_legacy_food_csv_2018-04"
LICENSE = "Public domain (USDA ARS FoodData Central, CC0 1.0)"
TARGET = env_int("TARGET_USDA_NUTRIENTS", 7000)
SALT = "usda_nutrients.v1"
MAX_PER_FOOD = 22  # appearances of one food within one template

# nutrient id -> (template key, phrase, min ratio, share of TARGET, node override or None)
NUTRIENTS = {
    1003: ("protein", "protein", 1.5, 0.10, None),
    1004: ("fat", "fat", 1.5, 0.10, None),
    1008: ("calories", "calories", 1.5, 0.10, None),
    2000: ("sugar", "sugar", 2.0, 0.09, None),
    1079: ("fiber", "dietary fiber", 1.5, 0.08, None),
    1093: ("sodium", "sodium", 2.0, 0.08, None),
    1253: ("cholesterol", "cholesterol", 1.5, 0.06, None),
    1162: ("vitamin_c", "vitamin C", 2.0, 0.08, "world.health.fitness.vitamin"),
    1106: ("vitamin_a", "vitamin A", 2.0, 0.07, "world.health.fitness.vitamin"),
    1087: ("calcium", "calcium", 2.0, 0.08, "world.health.fitness.nutrition"),
    1089: ("iron", "iron", 2.0, 0.08, "world.health.fitness.nutrition"),
    1092: ("potassium", "potassium", 1.5, 0.07, "world.health.fitness.nutrition"),
    1057: ("caffeine", "caffeine", 1.5, 0.01, None),
}

GROUP_NODE = {
    "veg": "world.food.cooking.vegetable",
    "fruit": "world.food.dishes_ingredients",
    "meat": "world.food.dishes_ingredients.meat",
    "seafood": "world.food.dishes_ingredients",
    "cheese": "world.food.dishes_ingredients.cheese",
    "dairy": "world.food.dishes_ingredients.milk",
    "egg": "world.food.dishes_ingredients",
    "bread": "world.food.dishes_ingredients.bread",
    "grain": "world.food.dishes_ingredients.cereal",
    "sweets": "world.food.baking_sweets",
    "sugar": "world.food.dishes_ingredients.sugar",
    "spice": "world.food.dishes_ingredients.spice",
    "nuts": "world.food.dishes_ingredients",
    "legume": "world.food.dishes_ingredients",
    "fat": "world.food.dishes_ingredients",
    "snack": "world.food.dishes_ingredients",
    "condiment": "world.food.dishes_ingredients",
    "drink": "world.food.nonalcoholic_drinks",
    "coffee": "world.food.nonalcoholic_drinks.coffee",
    "tea": "world.food.nonalcoholic_drinks.tea",
    "alcohol": "world.food.alcoholic_drinks",
}
CROSS_NODE = "world.food.dishes_ingredients"
# the higher value of a pair must reach this per-100 g floor, so trace-level noise (0.2 vs 0.8 mg) is never asked
FLOOR = {1003: 3.0, 1004: 2.0, 1008: 40.0, 2000: 3.0, 1079: 2.0, 1093: 100.0, 1253: 30.0, 1162: 8.0, 1106: 60.0,
         1087: 60.0, 1089: 1.5, 1092: 200.0, 1057: 10.0}

# SR Legacy description (exact, minus the "(Includes foods for USDA's ...)" note) | display name | group
FOODS = """
Broccoli, raw | raw broccoli | veg
Spinach, raw | raw spinach | veg
Kale, raw | raw kale | veg
Carrots, raw | raw carrots | veg
Cabbage, raw | raw cabbage | veg
Cabbage, red, raw | raw red cabbage | veg
Cauliflower, raw | raw cauliflower | veg
Celery, raw | raw celery | veg
Cucumber, with peel, raw | raw cucumber | veg
Lettuce, iceberg (includes crisphead types), raw | iceberg lettuce | veg
Lettuce, cos or romaine, raw | romaine lettuce | veg
Arugula, raw | arugula | veg
Asparagus, raw | raw asparagus | veg
Beets, raw | raw beets | veg
Brussels sprouts, raw | raw Brussels sprouts | veg
Eggplant, raw | raw eggplant | veg
Garlic, raw | raw garlic | veg
Ginger root, raw | raw ginger root | veg
Onions, raw | raw onions | veg
Onions, spring or scallions (includes tops and bulb), raw | scallions | veg
Shallots, raw | raw shallots | veg
Leeks, (bulb and lower leaf-portion), raw | raw leeks | veg
Okra, raw | raw okra | veg
Parsnips, raw | raw parsnips | veg
Radishes, raw | raw radishes | veg
Turnips, raw | raw turnips | veg
Rutabagas, raw | raw rutabaga | veg
Kohlrabi, raw | raw kohlrabi | veg
Fennel, bulb, raw | raw fennel bulb | veg
Watercress, raw | watercress | veg
Collards, raw | raw collard greens | veg
Chard, swiss, raw | raw Swiss chard | veg
Mustard greens, raw | raw mustard greens | veg
Dandelion greens, raw | raw dandelion greens | veg
Artichokes, (globe or french), raw | raw artichokes | veg
Peas, green, raw | raw green peas | veg
Soybeans, green, raw | raw edamame (green soybeans) | veg
Corn, sweet, yellow, raw | raw sweet corn | veg
Tomatoes, red, ripe, raw, year round average | raw tomatoes | veg
Tomatoes, sun-dried | sun-dried tomatoes | veg
Peppers, sweet, red, raw | raw red bell pepper | veg
Peppers, sweet, green, raw | raw green bell pepper | veg
Peppers, jalapeno, raw | raw jalapeño peppers | veg
Squash, summer, zucchini, includes skin, raw | raw zucchini | veg
Squash, winter, butternut, raw | raw butternut squash | veg
Pumpkin, raw | raw pumpkin | veg
Sweet potato, raw, unprepared | raw sweet potato | veg
Potatoes, flesh and skin, raw | raw potatoes | veg
Potatoes, baked, flesh and skin, without salt | baked potato with skin | veg
Cassava, raw | raw cassava | veg
Taro, raw | raw taro | veg
Yam, raw | raw yam | veg
Yambean (jicama), raw | raw jicama | veg
Bamboo shoots, raw | raw bamboo shoots | veg
Lotus root, raw | raw lotus root | veg
Mushrooms, white, raw | raw white mushrooms | veg
Mushrooms, shiitake, raw | raw shiitake mushrooms | veg
Mushrooms, portabella, raw | raw portobello mushrooms | veg
Mushrooms, oyster, raw | raw oyster mushrooms | veg
Mushrooms, shiitake, dried | dried shiitake mushrooms | veg
Seaweed, kelp, raw | raw kelp | veg
Seaweed, wakame, raw | raw wakame seaweed | veg
Seaweed, spirulina, dried | dried spirulina | veg
Alfalfa seeds, sprouted, raw | alfalfa sprouts | veg
Cabbage, kimchi | kimchi | veg
Sauerkraut, canned, solids and liquids | sauerkraut | veg
Pickles, cucumber, dill or kosher dill | dill pickles | veg
Olives, ripe, canned (small-extra large) | canned black olives | veg
Olives, pickled, canned or bottled, green | green olives | veg
Apples, raw, with skin | raw apples with skin | fruit
Bananas, raw | raw bananas | fruit
Oranges, raw, all commercial varieties | raw oranges | fruit
Tangerines, (mandarin oranges), raw | raw tangerines | fruit
Grapefruit, raw, pink and red, all areas | raw pink grapefruit | fruit
Lemons, raw, without peel | raw lemons | fruit
Limes, raw | raw limes | fruit
Grapes, red or green (European type, such as Thompson seedless), raw | raw grapes | fruit
Strawberries, raw | raw strawberries | fruit
Blueberries, raw | raw blueberries | fruit
Raspberries, raw | raw raspberries | fruit
Blackberries, raw | raw blackberries | fruit
Cranberries, raw | raw cranberries | fruit
Cherries, sweet, raw | raw sweet cherries | fruit
Peaches, yellow, raw | raw peaches | fruit
Nectarines, raw | raw nectarines | fruit
Plums, raw | raw plums | fruit
Apricots, raw | raw apricots | fruit
Pears, raw | raw pears | fruit
Mangos, raw | raw mangoes | fruit
Papayas, raw | raw papaya | fruit
Pineapple, raw, all varieties | raw pineapple | fruit
Kiwifruit, green, raw | raw kiwifruit | fruit
Watermelon, raw | raw watermelon | fruit
Melons, cantaloupe, raw | raw cantaloupe | fruit
Melons, honeydew, raw | raw honeydew melon | fruit
Avocados, raw, all commercial varieties | raw avocado | fruit
Pomegranates, raw | raw pomegranate | fruit
Figs, raw | raw figs | fruit
Figs, dried, uncooked | dried figs | fruit
Dates, medjool | Medjool dates | fruit
Plums, dried (prunes), uncooked | prunes | fruit
Raisins, dark, seedless | raisins | fruit
Guavas, common, raw | raw guava | fruit
Passion-fruit, (granadilla), purple, raw | raw passion fruit | fruit
Persimmons, japanese, raw | raw persimmons | fruit
Litchis, raw | raw lychees | fruit
Jackfruit, raw | raw jackfruit | fruit
Durian, raw or frozen | durian | fruit
Nuts, coconut meat, raw | raw coconut meat | fruit
Rhubarb, raw | raw rhubarb | fruit
Carambola, (starfruit), raw | raw starfruit | fruit
Plantains, green, raw | raw green plantains | fruit
Goji berries, dried | dried goji berries | fruit
Cranberries, dried, sweetened | sweetened dried cranberries | fruit
Mango, dried, sweetened | sweetened dried mango | fruit
Tamarinds, raw | raw tamarind | fruit
Quinces, raw | raw quince | fruit
Gooseberries, raw | raw gooseberries | fruit
Currants, european black, raw | raw blackcurrants | fruit
Acerola, (west indian cherry), raw | raw acerola cherries | fruit
Beef, ground, 80% lean meat / 20% fat, raw | raw ground beef (80% lean) | meat
Beef, variety meats and by-products, liver, raw | raw beef liver | meat
Beef, variety meats and by-products, tongue, raw | raw beef tongue | meat
Beef, variety meats and by-products, heart, raw | raw beef heart | meat
Beef, cured, corned beef, brisket, cooked | cooked corned beef | meat
Chicken, broilers or fryers, breast, meat only, cooked, roasted | roasted skinless chicken breast | meat
Chicken, liver, all classes, raw | raw chicken liver | meat
Chicken, ground, raw | raw ground chicken | meat
Turkey, whole, meat only, raw | raw turkey meat | meat
Duck, domesticated, meat only, raw | raw duck meat | meat
Goose, liver, raw | raw goose liver | meat
Quail, meat only, raw | raw quail meat | meat
Ostrich, ground, raw | raw ground ostrich | meat
Lamb, ground, raw | raw ground lamb | meat
Veal, ground, raw | raw ground veal | meat
Pork, fresh, ground, raw | raw ground pork | meat
Pork, fresh, loin, tenderloin, separable lean only, raw | raw pork tenderloin | meat
Pork, cured, bacon, unprepared | raw bacon | meat
Pork, cured, ham, whole, separable lean and fat, unheated | cured ham | meat
Game meat, rabbit, domesticated, composite of cuts, raw | raw rabbit meat | meat
Salami, dry or hard, pork | dry pork salami | meat
Pepperoni, beef and pork, sliced | pepperoni | meat
Bologna, beef | beef bologna | meat
Frankfurter, beef, unheated | beef hot dogs | meat
Pate de foie gras, canned (goose liver pate), smoked | foie gras pâté | meat
Fish, salmon, Atlantic, wild, raw | raw wild Atlantic salmon | seafood
Fish, salmon, Atlantic, farmed, raw | raw farmed Atlantic salmon | seafood
Fish, tuna, fresh, bluefin, raw | raw bluefin tuna | seafood
Fish, tuna, light, canned in water, drained solids | canned light tuna in water | seafood
Fish, sardine, Atlantic, canned in oil, drained solids with bone | canned sardines in oil | seafood
Fish, cod, Atlantic, raw | raw Atlantic cod | seafood
Fish, herring, Atlantic, raw | raw Atlantic herring | seafood
Fish, anchovy, european, raw | raw anchovies | seafood
Fish, trout, rainbow, farmed, raw | raw farmed rainbow trout | seafood
Fish, catfish, channel, farmed, raw | raw farmed catfish | seafood
Fish, halibut, Atlantic and Pacific, raw | raw halibut | seafood
Fish, tilapia, raw | raw tilapia | seafood
Fish, swordfish, raw | raw swordfish | seafood
Fish, haddock, raw | raw haddock | seafood
Fish, mahimahi, raw | raw mahi-mahi | seafood
Fish, carp, raw | raw carp | seafood
Fish, pollock, Alaska, raw | raw Alaska pollock | seafood
Fish, mackerel, Atlantic, raw | raw Atlantic mackerel | seafood
Fish, eel, mixed species, raw | raw eel | seafood
Fish, caviar, black and red, granular | caviar | seafood
Fish, surimi | surimi (imitation crab) | seafood
Crustaceans, shrimp, raw | raw shrimp | seafood
Crustaceans, crab, blue, raw | raw blue crab | seafood
Crustaceans, crab, alaska king, raw | raw Alaska king crab | seafood
Crustaceans, lobster, northern, raw | raw lobster | seafood
Mollusks, oyster, eastern, wild, raw | raw oysters | seafood
Mollusks, clam, mixed species, raw | raw clams | seafood
Mollusks, mussel, blue, raw | raw mussels | seafood
Mollusks, scallop, mixed species, raw | raw scallops | seafood
Mollusks, squid, mixed species, raw | raw squid | seafood
Mollusks, octopus, common, raw | raw octopus | seafood
Mollusks, snail, raw | raw snails | seafood
Frog legs, raw | raw frog legs | seafood
Cheese, cheddar | cheddar cheese | cheese
Cheese, parmesan, hard | hard Parmesan cheese | cheese
Cheese, mozzarella, whole milk | whole-milk mozzarella | cheese
Cheese, feta | feta cheese | cheese
Cheese, brie | Brie cheese | cheese
Cheese, camembert | Camembert cheese | cheese
Cheese, swiss | Swiss cheese | cheese
Cheese, gouda | Gouda cheese | cheese
Cheese, edam | Edam cheese | cheese
Cheese, gruyere | Gruyère cheese | cheese
Cheese, provolone | provolone cheese | cheese
Cheese, blue | blue cheese | cheese
Cheese, roquefort | Roquefort cheese | cheese
Cheese, romano | Romano cheese | cheese
Cheese, ricotta, whole milk | whole-milk ricotta | cheese
Cheese, cream | cream cheese | cheese
Cheese, cottage, creamed, large or small curd | cottage cheese | cheese
Cheese, goat, soft type | soft goat cheese | cheese
Cheese, monterey | Monterey Jack cheese | cheese
Cheese, muenster | Muenster cheese | cheese
Cheese, colby | Colby cheese | cheese
Cheese, limburger | Limburger cheese | cheese
Cheese, fontina | fontina cheese | cheese
Cheese, fresh, queso fresco | queso fresco | cheese
Cheese, mexican, queso cotija | cotija cheese | cheese
Cheese, neufchatel | Neufchâtel cheese | cheese
Cheese, gjetost | gjetost (brown cheese) | cheese
Milk, whole, 3.25% milkfat, with added vitamin D | whole cow's milk | dairy
Milk, nonfat, fluid, with added vitamin A and vitamin D (fat free or skim) | skim milk | dairy
Milk, goat, fluid, with added vitamin D | goat's milk | dairy
Milk, sheep, fluid | sheep's milk | dairy
Milk, indian buffalo, fluid | water buffalo milk | dairy
Milk, buttermilk, fluid, cultured, lowfat | cultured buttermilk | dairy
Yogurt, plain, whole milk | plain whole-milk yogurt | dairy
Yogurt, Greek, plain, whole milk | plain whole-milk Greek yogurt | dairy
Cream, fluid, heavy whipping | heavy whipping cream | dairy
Cream, fluid, half and half | half-and-half | dairy
Cream, sour, cultured | sour cream | dairy
Butter, salted | salted butter | dairy
Butter, Clarified butter (ghee) | ghee | dairy
Ice creams, vanilla | vanilla ice cream | dairy
Ice creams, chocolate | chocolate ice cream | dairy
Egg, whole, raw, fresh | raw whole egg | egg
Egg, whole, cooked, hard-boiled | hard-boiled egg | egg
Egg, white, raw, fresh | raw egg white | egg
Egg, yolk, raw, fresh | raw egg yolk | egg
Egg, duck, whole, fresh, raw | raw duck egg | egg
Egg, quail, whole, fresh, raw | raw quail egg | egg
Bread, white, commercially prepared (includes soft bread crumbs) | white bread | bread
Bread, whole-wheat, commercially prepared | whole-wheat bread | bread
Bread, rye | rye bread | bread
Bread, pumpernickel | pumpernickel bread | bread
Bread, french or vienna (includes sourdough) | French bread | bread
Bread, pita, white, enriched | white pita bread | bread
Bread, multi-grain (includes whole-grain) | multigrain bread | bread
Bagels, plain, enriched, with calcium propionate (includes onion, poppy, sesame) | plain bagels | bread
Croissants, butter | butter croissants | bread
English muffins, plain, unenriched, with calcium propionate (includes sourdough) | English muffins | bread
Tortillas, ready-to-bake or -fry, corn | corn tortillas | bread
Tortillas, ready-to-bake or -fry, flour, refrigerated | flour tortillas | bread
Crackers, saltines (includes oyster, soda, soup) | saltine crackers | bread
Crackers, matzo, plain | plain matzo | bread
Crackers, crispbread, rye | rye crispbread | bread
Rice, white, long-grain, regular, cooked, enriched, with salt | cooked white rice | grain
Rice, brown, long-grain, cooked | cooked brown rice | grain
Wild rice, cooked | cooked wild rice | grain
Quinoa, cooked | cooked quinoa | grain
Couscous, cooked | cooked couscous | grain
Bulgur, cooked | cooked bulgur | grain
Millet, cooked | cooked millet | grain
Barley, pearled, cooked | cooked pearl barley | grain
Buckwheat groats, roasted, cooked | cooked buckwheat groats | grain
Amaranth grain, cooked | cooked amaranth | grain
Teff, cooked | cooked teff | grain
Spelt, cooked | cooked spelt | grain
Pasta, cooked, enriched, without added salt | cooked pasta | grain
Pasta, whole-wheat, cooked | cooked whole-wheat pasta | grain
Rice noodles, cooked | cooked rice noodles | grain
Oats | rolled oats | grain
Oat bran, raw | oat bran | grain
Wheat bran, crude | wheat bran | grain
Wheat germ, crude | wheat germ | grain
Wheat flour, white, all-purpose, enriched, bleached | all-purpose white flour | grain
Wheat flour, whole-grain | whole-wheat flour | grain
Cornmeal, whole-grain, yellow | yellow cornmeal | grain
Cornstarch | cornstarch | grain
Rye flour, dark | dark rye flour | grain
Semolina, enriched | semolina | grain
Tapioca, pearl, dry | dry tapioca pearls | grain
Snacks, popcorn, air-popped | air-popped popcorn | snack
Snacks, potato chips, plain, salted | salted potato chips | snack
Snacks, tortilla chips, plain, white corn, salted | salted tortilla chips | snack
Snacks, pretzels, hard, plain, salted | hard salted pretzels | snack
Snacks, rice cakes, brown rice, plain, unsalted | plain brown rice cakes | snack
Snacks, trail mix, regular | trail mix | snack
Snacks, beef jerky, chopped and formed | beef jerky | snack
Snacks, pork skins, plain | pork rinds | snack
Snacks, banana chips | banana chips | snack
Nuts, almonds | almonds | nuts
Nuts, walnuts, english | walnuts | nuts
Nuts, pecans | pecans | nuts
Nuts, cashew nuts, raw | raw cashews | nuts
Nuts, macadamia nuts, raw | raw macadamia nuts | nuts
Nuts, pistachio nuts, raw | raw pistachios | nuts
Nuts, hazelnuts or filberts | hazelnuts | nuts
Nuts, brazilnuts, dried, unblanched | Brazil nuts | nuts
Nuts, pine nuts, dried | pine nuts | nuts
Nuts, chestnuts, european, roasted | roasted chestnuts | nuts
Nuts, coconut water (liquid from coconuts) | coconut water | drink
Nuts, coconut milk, canned (liquid expressed from grated meat and water) | canned coconut milk | fat
Seeds, chia seeds, dried | chia seeds | nuts
Seeds, flaxseed | flaxseed | nuts
Seeds, hemp seed, hulled | hulled hemp seeds | nuts
Seeds, sunflower seed kernels, dried | sunflower seeds | nuts
Seeds, pumpkin and squash seed kernels, dried | pumpkin seeds | nuts
Seeds, sesame seeds, whole, dried | sesame seeds | nuts
Seeds, sesame butter, tahini, from roasted and toasted kernels (most common type) | tahini | nuts
Nuts, almond butter, plain, without salt added | almond butter | nuts
Peanuts, all types, raw | raw peanuts | legume
Peanut butter, smooth style, with salt | smooth peanut butter | legume
Lentils, mature seeds, cooked, boiled, without salt | cooked lentils | legume
Beans, black, mature seeds, cooked, boiled, without salt | cooked black beans | legume
Beans, kidney, red, mature seeds, cooked, boiled, without salt | cooked red kidney beans | legume
Beans, navy, mature seeds, cooked, boiled, without salt | cooked navy beans | legume
Beans, pinto, mature seeds, cooked, boiled, without salt | cooked pinto beans | legume
Chickpeas (garbanzo beans, bengal gram), mature seeds, cooked, boiled, without salt | cooked chickpeas | legume
Soybeans, mature cooked, boiled, without salt | cooked soybeans | legume
Mung beans, mature seeds, cooked, boiled, without salt | cooked mung beans | legume
Beans, adzuki, mature seeds, cooked, boiled, without salt | cooked adzuki beans | legume
Broadbeans (fava beans), mature seeds, cooked, boiled, without salt | cooked fava beans | legume
Peas, split, mature seeds, cooked, boiled, without salt | cooked split peas | legume
Refried beans, canned, traditional style | canned refried beans | legume
Hummus, commercial | store-bought hummus | legume
Falafel, home-prepared | falafel | legume
Tofu, raw, firm, prepared with calcium sulfate | firm tofu | legume
Tempeh | tempeh | legume
Miso | miso | legume
Natto | natto | legume
Soymilk, original and vanilla, unfortified | unfortified soy milk | drink
Oil, olive, salad or cooking | olive oil | fat
Oil, coconut | coconut oil | fat
Oil, canola | canola oil | fat
Oil, sesame, salad or cooking | sesame oil | fat
Lard | lard | fat
Fat, beef tallow | beef tallow | fat
Fish oil, cod liver | cod liver oil | fat
Salad dressing, mayonnaise, regular | regular mayonnaise | condiment
Catsup | ketchup | condiment
Mustard, prepared, yellow | yellow mustard | condiment
Soy sauce made from soy and wheat (shoyu) | soy sauce | condiment
Vinegar, balsamic | balsamic vinegar | condiment
Horseradish, prepared | prepared horseradish | condiment
Salt, table | table salt | condiment
Yeast extract spread | yeast extract spread (Marmite-style) | condiment
Sauce, pesto, ready-to-serve, refrigerated | refrigerated pesto sauce | condiment
Sauce, salsa, ready-to-serve | jarred salsa | condiment
Spices, cinnamon, ground | ground cinnamon | spice
Spices, turmeric, ground | ground turmeric | spice
Spices, cumin seed | cumin seed | spice
Spices, paprika | paprika | spice
Spices, pepper, black | black pepper | spice
Spices, pepper, red or cayenne | cayenne pepper | spice
Spices, ginger, ground | ground ginger | spice
Spices, nutmeg, ground | ground nutmeg | spice
Spices, cloves, ground | ground cloves | spice
Spices, oregano, dried | dried oregano | spice
Spices, basil, dried | dried basil | spice
Spices, thyme, dried | dried thyme | spice
Spices, rosemary, dried | dried rosemary | spice
Spices, parsley, dried | dried parsley | spice
Spices, garlic powder | garlic powder | spice
Spices, onion powder | onion powder | spice
Spices, curry powder | curry powder | spice
Spices, chili powder | chili powder | spice
Spices, cardamom | cardamom | spice
Spices, saffron | saffron | spice
Spices, bay leaf | bay leaves | spice
Spices, fennel seed | fennel seed | spice
Spices, mustard seed, ground | ground mustard seed | spice
Spices, poppy seed | poppy seeds | spice
Spices, allspice, ground | ground allspice | spice
Basil, fresh | fresh basil | spice
Parsley, fresh | fresh parsley | spice
Coriander (cilantro) leaves, raw | fresh cilantro | spice
Peppermint, fresh | fresh peppermint | spice
Dill weed, fresh | fresh dill | spice
Vanilla extract | vanilla extract | spice
Honey | honey | sugar
Sugars, granulated | white sugar | sugar
Sugars, brown | brown sugar | sugar
Syrups, maple | maple syrup | sugar
Molasses | molasses | sugar
Sweetener, syrup, agave | agave syrup | sugar
Syrups, corn, light | light corn syrup | sugar
Jams and preserves | fruit jam | sugar
Candies, milk chocolate | milk chocolate | sweets
Candies, white chocolate | white chocolate | sweets
Candies, semisweet chocolate | semisweet chocolate | sweets
Chocolate, dark, 70-85% cacao solids | dark chocolate (70-85% cacao) | sweets
Cocoa, dry powder, unsweetened | unsweetened cocoa powder | sweets
Candies, marshmallows | marshmallows | sweets
Candies, jellybeans | jelly beans | sweets
Candies, caramels | caramels | sweets
Candies, hard | hard candy | sweets
Candies, halavah, plain | halva | sweets
Chocolate-flavored hazelnut spread | chocolate hazelnut spread | sweets
Cookies, chocolate chip, commercially prepared, regular, higher fat, enriched | chocolate chip cookies | sweets
Cookies, oatmeal, commercially prepared, regular | oatmeal cookies | sweets
Cookies, shortbread, commercially prepared, plain | shortbread cookies | sweets
Cookies, gingersnaps | gingersnaps | sweets
Cookies, fig bars | fig bars | sweets
Cookies, brownies, commercially prepared | brownies | sweets
Doughnuts, cake-type, plain (includes unsugared, old-fashioned) | plain cake doughnuts | sweets
Cake, angelfood, commercially prepared | angel food cake | sweets
Cake, cheesecake, commercially prepared | cheesecake | sweets
Cake, sponge, commercially prepared | sponge cake | sweets
Cake, fruitcake, commercially prepared | fruitcake | sweets
Pie, apple, commercially prepared, enriched flour | apple pie | sweets
Pie, pecan, commercially prepared | pecan pie | sweets
Pie, pumpkin, commercially prepared | pumpkin pie | sweets
Puddings, chocolate, ready-to-eat | chocolate pudding | sweets
Sherbet, orange | orange sherbet | sweets
Frozen yogurts, flavors other than chocolate | frozen yogurt | sweets
Beverages, coffee, brewed, prepared with tap water | brewed coffee | coffee
Beverages, coffee, brewed, espresso, restaurant-prepared | espresso | coffee
Beverages, coffee, instant, regular, powder | instant coffee powder | coffee
Beverages, tea, black, brewed, prepared with tap water | brewed black tea | tea
Beverages, tea, green, brewed, regular | brewed green tea | tea
Beverages, carbonated, cola, regular | regular cola | drink
Beverages, carbonated, ginger ale | ginger ale | drink
Beverages, carbonated, root beer | root beer | drink
Beverages, carbonated, tonic water | tonic water | drink
Beverages, Energy drink, RED BULL | Red Bull energy drink | drink
Orange juice, raw | fresh orange juice | drink
Apple juice, canned or bottled, unsweetened, without added ascorbic acid | unsweetened apple juice | drink
Grape juice, canned or bottled, unsweetened, without added ascorbic acid | unsweetened grape juice | drink
Cranberry juice, unsweetened | unsweetened cranberry juice | drink
Pomegranate juice, bottled | pomegranate juice | drink
Tomato juice, canned, with salt added | tomato juice | drink
Lemon juice, raw | fresh lemon juice | drink
Prune juice, canned | prune juice | drink
Carrot juice, canned | carrot juice | drink
Beverages, almond milk, unsweetened, shelf stable | unsweetened almond milk | drink
Beverages, rice milk, unsweetened | unsweetened rice milk | drink
Beverages, Horchata, as served in restaurant | horchata | drink
Alcoholic beverage, beer, regular, all | regular beer | alcohol
Alcoholic beverage, beer, light | light beer | alcohol
Alcoholic beverage, wine, table, red | red table wine | alcohol
Alcoholic beverage, wine, table, white | white table wine | alcohol
Alcoholic beverage, rice (sake) | sake | alcohol
Alcoholic beverage, distilled, all (gin, rum, vodka, whiskey) 80 proof | distilled spirits (80 proof) | alcohol
Alcoholic beverage, liqueur, coffee, 53 proof | coffee liqueur | alcohol
Alcoholic beverage, pina colada, prepared-from-recipe | piña colada | alcohol
"""


def fetch(raw_dir: Path) -> None:
    out = raw_dir / ZIP
    if not out.exists():
        with httpx.stream("GET", URL, timeout=600, follow_redirects=True) as r:
            r.raise_for_status()
            with open(out, "wb") as fh:
                for chunk in r.iter_bytes(1 << 20):
                    fh.write(chunk)
    if not (raw_dir / DIR / "food.csv").exists():
        with zipfile.ZipFile(out) as z:
            z.extractall(raw_dir)


def _clean_desc(d: str) -> str:
    return re.sub(r"\s*\(Includes foods for USDA's Food Distribution Program\)", "", d).strip()


def _foods(raw_dir: Path) -> dict[str, dict]:
    """fdc_id -> {name, group, desc} for the curated list; every curated description must exist exactly once."""
    wanted: dict[str, tuple[str, str]] = {}
    for line in FOODS.strip().splitlines():
        desc, name, group = (p.strip() for p in line.split(" | "))
        wanted[desc] = (name, group)
    found: dict[str, dict] = {}
    seen_desc: set[str] = set()
    with open(raw_dir / DIR / "food.csv", newline="") as fh:
        for row in csv.DictReader(fh):
            d = _clean_desc(row["description"])
            if d in wanted and d not in seen_desc:
                seen_desc.add(d)
                name, group = wanted[d]
                found[row["fdc_id"]] = {"name": name, "group": group, "desc": row["description"]}
    missing = sorted(set(wanted) - seen_desc)
    if missing:
        # curated rows absent from this SR release are skipped, not fatal
        print(f"[usda_nutrients] {len(missing)} curated foods not in SR Legacy: {missing}")
    # one fdc per display name (the first curated description wins)
    by_name: dict[str, str] = {}
    for fid, f in found.items():
        by_name.setdefault(f["name"], fid)
    return {fid: found[fid] for fid in by_name.values()}


def _values(raw_dir: Path, fids: set[str]) -> dict[int, dict[str, float]]:
    vals: dict[int, dict[str, float]] = {nid: {} for nid in NUTRIENTS}
    with open(raw_dir / DIR / "food_nutrient.csv", newline="") as fh:
        for row in csv.DictReader(fh):
            if row["fdc_id"] not in fids:
                continue
            nid = int(row["nutrient_id"])
            if nid in vals and row["amount"] not in ("", None):
                vals[nid][row["fdc_id"]] = float(row["amount"])
    return vals


def _slug(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\(.*?\)", "", s)
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s[:40].rsplit("_", 1)[0] if len(s) > 40 else s


def normalize(raw_dir: Path) -> Iterator[Question]:
    foods = _foods(raw_dir)
    vals = _values(raw_dir, set(foods))
    for nid, (key, phrase, min_ratio, share, node_override) in NUTRIENTS.items():
        v = {fid: x for fid, x in vals[nid].items() if x > 0}
        text = f"Gram for gram, which has more {phrase}: A or B?"
        pairs = []
        for a, b in itertools.combinations(sorted(v), 2):
            hi, lo = (a, b) if v[a] >= v[b] else (b, a)
            if v[hi] / v[lo] >= min_ratio and v[hi] >= FLOOR[nid]:
                pairs.append((a, b))
        quota = max(1, round(TARGET * share))
        # half the quota from same-group pairs (harder), the rest from any pair
        same = [p for p in pairs if foods[p[0]]["group"] == foods[p[1]]["group"]]
        taken: list[tuple[str, str]] = []
        uses: dict[str, int] = {}
        for pool, cap in ((same, quota // 2), (pairs, quota)):
            for p in hash_order(pool, key=lambda p: f"{p[0]}|{p[1]}", salt=f"{SALT}|{key}"):
                if len(taken) >= cap:
                    break
                if p in taken or uses.get(p[0], 0) >= MAX_PER_FOOD or uses.get(p[1], 0) >= MAX_PER_FOOD:
                    continue
                taken.append(p)
                uses[p[0]] = uses.get(p[0], 0) + 1
                uses[p[1]] = uses.get(p[1], 0) + 1
        for a, b in taken:
            fa, fb = foods[a], foods[b]
            # A/B order by salted hash so the truth is not always first
            flip = int(hashlib.sha256(f"{SALT}|{key}|{a}|{b}".encode()).hexdigest(), 16) % 2
            first, second = (a, b) if flip else (b, a)
            na, nb = foods[first]["name"], foods[second]["name"]
            ka, kb = _slug(na), _slug(nb)
            if ka == kb:
                continue
            truth = ka if v[first] > v[second] else kb
            if node_override:
                node = node_override
            elif fa["group"] == fb["group"]:
                node = GROUP_NODE[fa["group"]]
            else:
                node = CROSS_NODE
            yield Question(
                text=text.replace("A or B", f"{na} or {nb}"),
                primitive="choice",
                hemisphere="world",
                kind="factual",
                origin="template",
                source=NAME,
                options={ka: na, kb: nb},
                node_hint=node,
                source_item_id=f"{key}:{first}:{second}",
                license=LICENSE,
                truth=truth,
                template_id=f"usda_nutrients.{key}",
                meta={
                    "nutrient_id": nid,
                    "values_per_100g": {ka: v[first], kb: v[second]},
                    "sr_descriptions": {ka: foods[first]["desc"], kb: foods[second]["desc"]},
                    "groups": [fa["group"], fb["group"]],
                },
            )
