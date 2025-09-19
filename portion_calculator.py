"""Логика расчета порций и планирования питания"""

from typing import Dict, List, Optional
from datetime import datetime

from models import (
    CategoryENUM,
    DailyPortionsModel,
    MealPlanModel,
    NutritionModel,
    PortionModel,
    RecipeModel
)
from config import (
    COOKING_DAYS,
    COOKING_PERIODS,
    DAILY_CALORIES,
    DAILY_CARBS,
    DAILY_FAT,
    DAILY_PROTEIN,
    MEAL_PORTIONS,
    SERVINGS_PER_DAY
)


def calculate_daily_portions(recipes: List[RecipeModel]) -> DailyPortionsModel:
    """Расчет порций на день с учетом дневных норм"""
    # Группируем рецепты по категориям
    categorized_recipes = _categorize_recipes(recipes)

    # Выбираем рецепты для каждого приема пищи
    selected_recipes = _select_daily_recipes(categorized_recipes)

    # Рассчитываем порции
    portions = {}
    total_nutrition = NutritionModel(calories=0, protein=0, fat=0, carbs=0)

    for category, recipe in selected_recipes.items():
        if recipe:
            portion = _calculate_portion_weight(recipe, category)
            portions[category] = portion

            # Добавляем к общему питанию
            total_nutrition.calories += portion.nutrition_per_portion.calories
            total_nutrition.protein += portion.nutrition_per_portion.protein
            total_nutrition.fat += portion.nutrition_per_portion.fat
            total_nutrition.carbs += portion.nutrition_per_portion.carbs

    return DailyPortionsModel(
        breakfast=portions.get("завтрак"),
        main_dish=portions.get("основное блюдо"),
        dessert=portions.get("десерт"),
        total_nutrition=total_nutrition
    )


def _categorize_recipes(recipes: List[RecipeModel]) -> Dict[str, List[RecipeModel]]:
    """Группировка рецептов по категориям"""
    categories = {}
    for recipe in recipes:
        category = recipe.category.value
        if category not in categories:
            categories[category] = []
        categories[category].append(recipe)
    return categories


def _select_daily_recipes(categorized_recipes: Dict[str, List[RecipeModel]]) -> Dict[str, Optional[RecipeModel]]:
    """Выбор рецептов для каждого приема пищи"""
    selected = {}

    for category in ["завтрак", "основное блюдо", "десерт"]:
        recipes = categorized_recipes.get(category, [])
        if recipes:
            # Выбираем первый рецепт (можно улучшить логику выбора)
            selected[category] = recipes[0]
        else:
            selected[category] = None

    return selected


def _calculate_portion_weight(recipe: RecipeModel, category: str) -> PortionModel:
    """Расчет веса порции на основе дневных норм"""
    portions_count = MEAL_PORTIONS[category]

    # Целевые значения для категории
    target_calories = DAILY_CALORIES * (portions_count / sum(MEAL_PORTIONS.values()))
    target_protein = DAILY_PROTEIN * (portions_count / sum(MEAL_PORTIONS.values()))
    target_carbs = DAILY_CARBS * (portions_count / sum(MEAL_PORTIONS.values()))
    target_fat = DAILY_FAT * (portions_count / sum(MEAL_PORTIONS.values()))

    # Расчет коэффициента для достижения целевых значений
    if recipe.calories > 0:
        calories_ratio = target_calories / recipe.calories
    else:
        calories_ratio = 1.0

    # Используем среднее значение коэффициентов для баланса
    adjustment_ratio = calories_ratio

    # Рассчитываем скорректированные значения на порцию
    portion_calories = recipe.calories * adjustment_ratio
    portion_protein = recipe.protein * adjustment_ratio
    portion_fat = recipe.fat * adjustment_ratio
    portion_carbs = recipe.carbs * adjustment_ratio

    # Оцениваем вес порции (примерная оценка на основе калорийности)
    # Предполагаем, что 100г продукта содержит примерно 100-300 ккал
    estimated_weight_per_100g = 200  # среднее значение
    portion_weight = (portion_calories / estimated_weight_per_100g) * 100

    # Общий вес для приготовления
    total_weight = portion_weight * portions_count

    return PortionModel(
        recipe=recipe,
        portion_weight=round(portion_weight, 1),
        portions_count=portions_count,
        total_weight=round(total_weight, 1),
        nutrition_per_portion=NutritionModel(
            calories=round(portion_calories, 1),
            protein=round(portion_protein, 1),
            fat=round(portion_fat, 1),
            carbs=round(portion_carbs, 1)
        )
    )


def generate_weekly_plan_with_portions(
    recipes: List[RecipeModel],
    start_date: datetime
) -> List[MealPlanModel]:
    """Генерация недельного плана с учетом новых требований"""
    plan = []
    days = [
        "Monday", "Tuesday", "Wednesday", "Thursday",
        "Friday", "Saturday", "Sunday"
    ]

    # Группируем рецепты по категориям
    categorized_recipes = _categorize_recipes(recipes)

    # Выбираем рецепты для каждого дня готовки
    cooking_recipes = {}
    recipe_index = 0

    for day in COOKING_DAYS:
        if day in days:
            # Выбираем рецепт для этого дня готовки
            available_recipes = []
            for category_recipes in categorized_recipes.values():
                available_recipes.extend(category_recipes)

            if available_recipes:
                cooking_recipes[day] = available_recipes[recipe_index % len(available_recipes)]
                recipe_index += 1

    # Создаем план для каждого дня
    for i, day in enumerate(days):
        if day in COOKING_DAYS and day in cooking_recipes:
            # День готовки
            recipe = cooking_recipes[day]
            servings = COOKING_PERIODS[day] * SERVINGS_PER_DAY

            plan.append(
                MealPlanModel(
                    day=day,
                    recipe=recipe,
                    servings_to_prepare=servings
                )
            )
        else:
            # День использования приготовленного
            # Находим ближайший предыдущий день готовки
            cooking_day = None
            for cooking_d in COOKING_DAYS:
                if cooking_d in cooking_recipes:
                    cooking_day = cooking_d
                    break

            if cooking_day and cooking_day in cooking_recipes:
                recipe = cooking_recipes[cooking_day]
                plan.append(
                    MealPlanModel(
                        day=day,
                        recipe=recipe,
                        servings_to_prepare=0  # Уже приготовлено
                    )
                )

    return plan


def get_today_portions(plan: List[MealPlanModel], today: str) -> Optional[RecipeModel]:
    """Получение блюда для сегодняшнего дня"""
    for meal in plan:
        if meal.day == today:
            return meal.recipe
    return None


def get_cooking_plan(plan: List[MealPlanModel]) -> List[MealPlanModel]:
    """Получение списка блюд для приготовления на неделю"""
    return [meal for meal in plan if meal.servings_to_prepare > 0]
