import json
from datetime import datetime

from aiogram import Router, types
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from database import RecipeDB, async_session
from models import IngredientModel, NutritionModel, RecipeModel
from planning import (
    generate_weekly_plan,
    get_next_cooking_day,
    get_shopping_list,
    get_today_meal,
)

router = Router()

# Клавиатура с кнопками
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🍽 Сегодня"), KeyboardButton(text="📅 Неделя")],
        [KeyboardButton(text="👨‍🍳 Готовить"), KeyboardButton(text="🛒 Купить")],
    ],
    resize_keyboard=True,
)


async def load_recipes_from_db():
    async with async_session() as session:
        result = await session.execute(RecipeDB.__table__.select())
        recipes = []
        for row in result:
            ingredients = [
                IngredientModel(**ing) for ing in json.loads(row.ingredients)
            ]
            nutrition = (
                NutritionModel(**json.loads(row.nutrition)) if row.nutrition else None
            )
            recipe = RecipeModel(
                name=row.name,
                servings=row.servings,
                ingredients=ingredients,
                nutrition_per_serving=nutrition,
                instructions=row.instructions,
                image_url=row.image_url,
            )
            recipes.append(recipe)
        return recipes


@router.message(lambda message: message.text == "🍽 Сегодня")
async def today_handler(message: types.Message):
    today = datetime.now().strftime("%A")
    recipes = await load_recipes_from_db()
    plan = generate_weekly_plan(recipes, datetime.now())
    meal = get_today_meal(plan, today)
    if meal:
        nutrition = meal.nutrition_per_serving
        if nutrition:
            kbju = f"{nutrition.calories}/{nutrition.protein}/{nutrition.fat}/{nutrition.carbs}"
        else:
            kbju = "Не указано"
        text = f"🍽 Блюдо сегодня: {meal.name}\n📊 КБЖУ: {kbju}\n🍴 Порций: {meal.servings}\n🥕 Ингредиенты: {[f'{ing.name} {ing.quantity or ""} {ing.unit or ""}'.strip() for ing in meal.ingredients]}\n📝 Приготовление: {meal.instructions}"
        await message.answer(text, reply_markup=main_keyboard)
    else:
        await message.answer(
            "Нет запланированного блюда на сегодня.", reply_markup=main_keyboard
        )


@router.message(lambda message: message.text == "📅 Неделя")
async def week_handler(message: types.Message):
    recipes = await load_recipes_from_db()
    plan = generate_weekly_plan(recipes, datetime.now())
    text = "📅 Блюда на неделю:\n"
    for p in plan:
        nutrition = p.recipe.nutrition_per_serving
        kcal = nutrition.calories if nutrition else "N/A"
        text += f"{p.day}: {p.recipe.name} - {kcal} ккал\n"
    await message.answer(text, reply_markup=main_keyboard)


@router.message(lambda message: message.text == "👨‍🍳 Готовить")
async def cook_handler(message: types.Message):
    today = datetime.now().strftime("%A")
    next_day = get_next_cooking_day(today)
    recipes = await load_recipes_from_db()
    plan = generate_weekly_plan(recipes, datetime.now())
    for p in plan:
        if p.day == next_day:
            text = f"👨‍🍳 Приготовить {next_day}:\n{p.recipe.name} - {p.servings_to_prepare} порций\n🥕 Ингредиенты: {[f'{ing.name} {ing.quantity or ""} {ing.unit or ""}'.strip() for ing in p.recipe.ingredients]}"
            await message.answer(text, reply_markup=main_keyboard)
            break


@router.message(lambda message: message.text == "🛒 Купить")
async def buy_handler(message: types.Message):
    today = datetime.now().strftime("%A")
    next_day = get_next_cooking_day(today)
    recipes = await load_recipes_from_db()
    plan = generate_weekly_plan(recipes, datetime.now())
    ingredients = get_shopping_list(plan, next_day)
    text = "🛒 Купить:\n"
    for ing in ingredients:
        text += f"{ing.name} - {ing.quantity} {ing.unit}\n"
    await message.answer(text, reply_markup=main_keyboard)
