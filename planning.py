from datetime import datetime
from typing import List, Optional

from models import IngredientModel, MealPlanModel, RecipeModel
from portion_calculator import generate_weekly_plan_with_portions


def generate_weekly_plan(
    recipes: List[RecipeModel], start_date: datetime
) -> List[MealPlanModel]:
    """Генерация недельного плана с новой логикой"""
    return generate_weekly_plan_with_portions(recipes, start_date)


def get_today_meal(plan: List[MealPlanModel], today: str) -> Optional[RecipeModel]:
    for meal in plan:
        if meal.day == today:
            return meal.recipe
    return None


def get_next_cooking_day(today: str) -> str:
    days = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    cooking_days = ["Saturday", "Monday"]
    today_index = days.index(today)
    for i in range(7):
        day = days[(today_index + i) % 7]
        if day in cooking_days:
            return day
    return "Monday"


def get_shopping_list(
    plan: List[MealPlanModel], next_cooking_day: str
) -> List[IngredientModel]:
    for meal in plan:
        if meal.day == next_cooking_day:
            ingredients = []
            for ing in meal.recipe.ingredients:
                if ing.quantity:
                    scaled_qty = ing.quantity * (
                        meal.servings_to_prepare / meal.recipe.servings
                    )
                    ingredients.append(
                        IngredientModel(
                            name=ing.name, quantity=scaled_qty, unit=ing.unit
                        )
                    )
            return ingredients
    return []
