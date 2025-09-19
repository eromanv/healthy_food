import json
from datetime import datetime

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from add_recipe_handlers import add_recipe_router
from models import IngredientModel, RecipeModel
from planning import (
    generate_weekly_plan,
    get_next_cooking_day,
    get_shopping_list,
    get_today_meal,
)
from recipe_service import get_all_recipes
from portion_calculator import calculate_daily_portions, get_cooking_plan

router = Router()

from add_recipe_handlers import add_recipe_router
from models import IngredientModel, RecipeModel
from planning import (
    generate_weekly_plan,
    get_next_cooking_day,
    get_shopping_list,
    get_today_meal,
)
from recipe_service import get_all_recipes
from portion_calculator import calculate_daily_portions, get_cooking_plan

router = Router()

from add_recipe_handlers import add_recipe_router
from models import IngredientModel, RecipeModel
from planning import (
    generate_weekly_plan,
    get_next_cooking_day,
    get_shopping_list,
    get_today_meal,
)
from recipe_service import get_all_recipes
from portion_calculator import calculate_daily_portions, get_cooking_plan

router = Router()
router.include_router(add_recipe_router)


@router.message(Command("start"))
async def start_handler(message: types.Message):
    # Send welcome message with main keyboard
    await message.answer(
        "Привет! Я помогу спланировать блюда на неделю. Используй кнопки ниже.",
        reply_markup=main_keyboard,
    )


# Inline keyboard for main menu
main_inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="➕ Добавить рецепт", callback_data="add_recipe")]
])

# Main keyboard with buttons
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🍽 Что едим сегодня"), KeyboardButton(text="📅 Что готовим на неделе")],
        [KeyboardButton(text="👨‍🍳 Готовить"), KeyboardButton(text="🛒 Купить")],
        [KeyboardButton(text="🍴 Меню")]
    ],
    resize_keyboard=True,
)


@router.message(lambda message: message.text == "🍴 Меню")
async def menu_handler(message: types.Message):
    """Show main menu"""
    await message.answer(
        "📋 Главное меню:",
        reply_markup=main_inline_keyboard
    )


async def load_recipes_from_db():
    """Load recipes from database using new structure"""
    return await get_all_recipes()


@router.message(lambda message: message.text == "🍽 Сегодня")
async def today_handler(message: types.Message):
    today = datetime.now().strftime("%A")
    recipes = await load_recipes_from_db()
    
    if not recipes:
        await message.answer(
            "🔍 У вас пока нет рецептов. Добавьте их через меню!",
            reply_markup=main_keyboard
        )
        return
        
    plan = generate_weekly_plan(recipes, datetime.now())
    meal = get_today_meal(plan, today)
    
    if meal:
        kbju = f"{meal.calories}/{meal.protein}/{meal.fat}/{meal.carbs}"
        ingredients_list = '\n'.join([
            f"• {ing.name} - {ing.quantity or ''} {ing.unit or ''}".strip() 
            for ing in meal.ingredients
        ])
        
        text = (
            f"🍽 Блюдо сегодня: {meal.name}\n"
            f"📊 КБЖУ: {kbju}\n"
            f"� Категория: {meal.category.value}\n"
            f"🥕 Ингредиенты:\n{ingredients_list}\n\n"
            f"📝 Приготовление:\n{meal.instructions}"
        )
        await message.answer(text, reply_markup=main_keyboard)
    else:
        await message.answer(
            "Нет запланированного блюда на сегодня.", reply_markup=main_keyboard
        )


@router.message(lambda message: message.text == "📅 Неделя")
async def week_handler(message: types.Message):
    recipes = await load_recipes_from_db()
    
    if not recipes:
        await message.answer(
            "🔍 У вас пока нет рецептов. Добавьте их через меню!",
            reply_markup=main_keyboard
        )
        return
    
    plan = generate_weekly_plan(recipes, datetime.now())
    text = "📅 Блюда на неделю:\n\n"
    
    for p in plan:
        kcal = p.recipe.calories
        text += f"• {p.day}: {p.recipe.name} - {kcal} ккал\n"
    
    await message.answer(text, reply_markup=main_keyboard)


@router.message(lambda message: message.text == "👨‍🍳 Готовить")
async def cook_handler(message: types.Message):
    today = datetime.now().strftime("%A")
    next_day = get_next_cooking_day(today)
    recipes = await load_recipes_from_db()
    
    if not recipes:
        await message.answer(
            "🔍 У вас пока нет рецептов. Добавьте их через меню!",
            reply_markup=main_keyboard
        )
        return
    
    plan = generate_weekly_plan(recipes, datetime.now())
    
    for p in plan:
        if p.day == next_day:
            ingredients_list = '\n'.join([
                f"• {ing.name} - {ing.quantity or ''} {ing.unit or ''}".strip() 
                for ing in p.recipe.ingredients
            ])
            
            text = (
                f"👨‍🍳 Готовим в {next_day}:\n\n"
                f"🍽 {p.recipe.name}\n"
                f"📊 КБЖУ: {p.recipe.calories}/{p.recipe.protein}/{p.recipe.fat}/{p.recipe.carbs}\n"
                f"🥕 Ингредиенты:\n{ingredients_list}\n\n"
                f"📝 Рецепт:\n{p.recipe.instructions}"
            )
            await message.answer(text, reply_markup=main_keyboard)
            return
            
    await message.answer(
        f"На {next_day} не запланировано готовки.",
        reply_markup=main_keyboard
    )


@router.message(lambda message: message.text == "🛒 Купить")
async def buy_handler(message: types.Message):
    today = datetime.now().strftime("%A")
    next_day = get_next_cooking_day(today)
    recipes = await load_recipes_from_db()
    
    if not recipes:
        await message.answer(
            "🔍 У вас пока нет рецептов. Добавьте их через меню!",
            reply_markup=main_keyboard
        )
        return
    
    plan = generate_weekly_plan(recipes, datetime.now())
    ingredients = get_shopping_list(plan, next_day)
    
    if ingredients:
        text = "🛒 Список покупок:\n\n"
        for ing in ingredients:
            quantity_unit = f"{ing.quantity or ''} {ing.unit or ''}".strip()
            text += f"• {ing.name} - {quantity_unit}\n"
        await message.answer(text, reply_markup=main_keyboard)
    else:
        await message.answer(
            f"На {next_day} не запланированы покупки.",
            reply_markup=main_keyboard
        )
