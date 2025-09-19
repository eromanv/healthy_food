#!/usr/bin/env python3

import asyncio
import sys
sys.path.append('/home/roman/healthy_food')

from datetime import datetime
from planning import generate_weekly_plan, get_next_cooking_day, get_shopping_list
from recipe_service import get_all_recipes

async def test_shopping_list():
    recipes = await get_all_recipes()
    print(f"Loaded {len(recipes)} recipes")

    today = datetime.now().strftime("%A")
    print(f"Today: {today}")

    next_day = get_next_cooking_day(today)
    print(f"Next cooking day: {next_day}")

    plan = generate_weekly_plan(recipes, datetime.now())
    print("Plan:")
    for meal in plan:
        print(f"  {meal.day}: {meal.recipe.name}, servings_to_prepare={meal.servings_to_prepare}")

    ingredients = get_shopping_list(plan, next_day)
    print(f"Shopping list for {next_day}:")
    for ing in ingredients:
        print(f"  {ing.name}: {ing.quantity} {ing.unit}")

if __name__ == "__main__":
    asyncio.run(test_shopping_list())
