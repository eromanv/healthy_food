import json
from datetime import datetime

from aiogram import Router, types
from aiogram.filters import Command
import logging
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
        [KeyboardButton(text="� Приготовить любое"), KeyboardButton(text="�🍴 Меню")]
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


@router.message(lambda message: message.text == "🍽 Что едим сегодня")
async def today_portions_handler(message: types.Message):
    """Показать порции на сегодня с расчетом веса"""
    recipes = await load_recipes_from_db()

    if not recipes:
        await message.answer(
            "🔍 У вас пока нет рецептов. Добавьте их через меню!",
            reply_markup=main_keyboard
        )
        return

    # Рассчитываем порции на день
    daily_portions = calculate_daily_portions(recipes)

    if not daily_portions.breakfast and not daily_portions.main_dish and not daily_portions.dessert:
        await message.answer(
            "❌ Не удалось рассчитать порции. Проверьте наличие рецептов разных категорий.",
            reply_markup=main_keyboard
        )
        return

    # Формируем сообщение
    text = "🍽 Порции на сегодня:\n\n"

    if daily_portions.breakfast:
        portion = daily_portions.breakfast
        text += f"🌅 Завтрак: {portion.recipe.name}\n"
        text += f"   📏 Вес порции: {portion.portion_weight} г\n"
        text += f"   📊 КБЖУ: {portion.nutrition_per_portion.calories}/{portion.nutrition_per_portion.protein}/{portion.nutrition_per_portion.fat}/{portion.nutrition_per_portion.carbs}\n\n"

    if daily_portions.main_dish:
        portion = daily_portions.main_dish
        text += f"🍽 Основное блюдо: {portion.recipe.name}\n"
        text += f"   📏 Вес порции: {portion.portion_weight} г (всего {portion.total_weight} г)\n"
        text += f"   📊 КБЖУ: {portion.nutrition_per_portion.calories}/{portion.nutrition_per_portion.protein}/{portion.nutrition_per_portion.fat}/{portion.nutrition_per_portion.carbs}\n\n"

    if daily_portions.dessert:
        portion = daily_portions.dessert
        text += f"🧁 Десерт: {portion.recipe.name}\n"
        text += f"   📏 Вес порции: {portion.portion_weight} г\n"
        text += f"   📊 КБЖУ: {portion.nutrition_per_portion.calories}/{portion.nutrition_per_portion.protein}/{portion.nutrition_per_portion.fat}/{portion.nutrition_per_portion.carbs}\n\n"

    # Итоговое питание
    total = daily_portions.total_nutrition
    text += f"📈 Итого за день:\n"
    text += f"   🔥 {total.calories} ккал\n"
    text += f"   💪 {total.protein} г белка\n"
    text += f"   🌾 {total.carbs} г углеводов\n"
    text += f"   🥑 {total.fat} г жиров"

    await message.answer(text, reply_markup=main_keyboard)


@router.message(lambda message: message.text == "📅 Что готовим на неделе")
async def weekly_cooking_handler(message: types.Message):
    """Показать план приготовления на неделю с возможностью просмотра рецептов"""
    recipes = await load_recipes_from_db()

    if not recipes:
        await message.answer(
            "🔍 У вас пока нет рецептов. Добавьте их через меню!",
            reply_markup=main_keyboard
        )
        return

    plan = generate_weekly_plan(recipes, datetime.now())
    cooking_plan = get_cooking_plan(plan)

    if not cooking_plan:
        await message.answer(
            "❌ Не удалось составить план приготовления.",
            reply_markup=main_keyboard
        )
        return

    # Создаем inline клавиатуру с блюдами
    keyboard_buttons = []
    text = "📅 План приготовления на неделю:\n\n"

    for i, meal in enumerate(cooking_plan):
        day_name = get_day_name_russian(meal.day)
        servings = meal.servings_to_prepare
        text += f"• {day_name}: {meal.recipe.name} ({servings} порций)\n"

        # Добавляем кнопку для просмотра рецепта
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"👀 {meal.recipe.name}",
                callback_data=f"view_recipe_{meal.recipe.id}"
            )
        ])

    keyboard_buttons.append([
        InlineKeyboardButton(text="❌ Закрыть", callback_data="close_cooking_plan")
    ])

    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await message.answer(text, reply_markup=inline_keyboard)


@router.callback_query(lambda c: c.data.startswith("view_recipe_"))
async def view_recipe_callback(callback: types.CallbackQuery):
    """Показать подробную информацию о рецепте"""
    recipe_id = int(callback.data.replace("view_recipe_", ""))

    # Получаем рецепт по ID
    recipes = await get_all_recipes()
    recipe = next((r for r in recipes if hasattr(r, 'id') and r.id == recipe_id), None)

    if not recipe:
        await callback.answer("❌ Рецепт не найден")
        return

    # Формируем текст с рецептом
    ingredients_list = '\n'.join([
        f"• {ing.name} - {ing.quantity or ''} {ing.unit or ''}".strip()
        for ing in recipe.ingredients
    ])

    text = (
        f"🍽 {recipe.name}\n\n"
        f"📊 КБЖУ на порцию: {recipe.calories}/{recipe.protein}/{recipe.fat}/{recipe.carbs}\n"
        f"🏷 Категория: {recipe.category.value}\n\n"
        f"🥕 Ингредиенты:\n{ingredients_list}\n\n"
        f"📝 Приготовление:\n{recipe.instructions}"
    )

    # Клавиатура для возврата
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад к плану", callback_data="back_to_cooking_plan")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="close_recipe")]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(lambda c: c.data == "back_to_cooking_plan")
async def back_to_cooking_plan_callback(callback: types.CallbackQuery):
    """Вернуться к плану приготовления"""
    # Повторно вызываем обработчик недельного плана
    recipes = await get_all_recipes()
    plan = generate_weekly_plan(recipes, datetime.now())
    cooking_plan = get_cooking_plan(plan)

    keyboard_buttons = []
    text = "📅 План приготовления на неделю:\n\n"

    for i, meal in enumerate(cooking_plan):
        day_name = get_day_name_russian(meal.day)
        servings = meal.servings_to_prepare
        text += f"• {day_name}: {meal.recipe.name} ({servings} порций)\n"

        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"👀 {meal.recipe.name}",
                callback_data=f"view_recipe_{meal.recipe.id}"
            )
        ])

    keyboard_buttons.append([
        InlineKeyboardButton(text="❌ Закрыть", callback_data="close_cooking_plan")
    ])

    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await callback.message.edit_text(text, reply_markup=inline_keyboard)


@router.callback_query(lambda c: c.data in ["close_cooking_plan", "close_recipe"])
async def close_callback(callback: types.CallbackQuery):
    """Закрыть текущее меню"""
    await callback.message.delete()


def get_day_name_russian(day: str) -> str:
    """Перевод дней недели на русский"""
    days_map = {
        "Monday": "Понедельник",
        "Tuesday": "Вторник",
        "Wednesday": "Среда",
        "Thursday": "Четверг",
        "Friday": "Пятница",
        "Saturday": "Суббота",
        "Sunday": "Воскресенье"
    }
    return days_map.get(day, day)


# Остальные обработчики (готовить, купить) остаются без изменений
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
                f"👨‍🍳 Готовим в {get_day_name_russian(next_day)}:\n\n"
                f"🍽 {p.recipe.name}\n"
                f"📊 КБЖУ: {p.recipe.calories}/{p.recipe.protein}/{p.recipe.fat}/{p.recipe.carbs}\n"
                f"🥕 Ингредиенты:\n{ingredients_list}\n\n"
                f"📝 Рецепт:\n{p.recipe.instructions}"
            )
            await message.answer(text, reply_markup=main_keyboard)
            return

    await message.answer(
        f"На {get_day_name_russian(next_day)} не запланировано готовки.",
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
        text = f"🛒 Список покупок для {get_day_name_russian(next_day)}:\n\n"
        for ing in ingredients:
            quantity_unit = f"{ing.quantity or ''} {ing.unit or ''}".strip()
            text += f"• {ing.name} - {quantity_unit}\n"
        await message.answer(text, reply_markup=main_keyboard)
    else:
        await message.answer(
            f"На {get_day_name_russian(next_day)} не запланированы покупки.",
            reply_markup=main_keyboard
        )


@router.message(lambda message: message.text == "🍳 Приготовить любое")
async def cook_any_handler(message: types.Message):
    """Показать список всех рецептов для выбора"""
    recipes = await load_recipes_from_db()

    if not recipes:
        await message.answer(
            "🔍 У вас пока нет рецептов. Добавьте их через меню!",
            reply_markup=main_keyboard
        )
        return

    # Создаем inline клавиатуру со всеми рецептами
    keyboard_buttons = []
    text = "🍳 Выберите рецепт для приготовления:\n\n"

    for i, recipe in enumerate(recipes):
        text += f"• {recipe.name}\n"
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"👨‍🍳 {recipe.name[:30]}...",
                callback_data=f"cook_recipe_{recipe.id}"
            )
        ])

    keyboard_buttons.append([
        InlineKeyboardButton(text="❌ Закрыть", callback_data="close_recipe_list")
    ])

    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await message.answer(text, reply_markup=inline_keyboard)


@router.callback_query(lambda c: c.data.startswith("cook_recipe_"))
async def cook_recipe_callback(callback: types.CallbackQuery):
    """Показать карточку рецепта для приготовления"""
    recipe_id = int(callback.data.replace("cook_recipe_", ""))

    # Получаем рецепт по ID
    recipes = await get_all_recipes()
    recipe = next((r for r in recipes if hasattr(r, 'id') and r.id == recipe_id), None)

    if not recipe:
        await callback.answer("❌ Рецепт не найден")
        return

    # Формируем текст с рецептом
    ingredients_list = '\n'.join([
        f"• {ing.name} - {ing.quantity or ''} {ing.unit or ''}".strip()
        for ing in recipe.ingredients
    ])

    text = (
        f"👨‍🍳 {recipe.name}\n\n"
        f"📊 КБЖУ на порцию: {recipe.calories}/{recipe.protein}/{recipe.fat}/{recipe.carbs}\n"
        f"🏷 Категория: {recipe.category.value}\n"
        f"👥 Количество порций: {recipe.servings}\n\n"
        f"🥕 Ингредиенты:\n{ingredients_list}\n\n"
        f"📝 Приготовление:\n{recipe.instructions}"
    )

    # Клавиатура для возврата
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="back_to_recipe_list")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="close_recipe")]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(lambda c: c.data == "back_to_recipe_list")
async def back_to_recipe_list_callback(callback: types.CallbackQuery):
    """Вернуться к списку рецептов"""
    recipes = await get_all_recipes()

    keyboard_buttons = []
    text = "🍳 Выберите рецепт для приготовления:\n\n"

    for i, recipe in enumerate(recipes):
        text += f"• {recipe.name}\n"
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"👨‍🍳 {recipe.name[:30]}...",
                callback_data=f"cook_recipe_{recipe.id}"
            )
        ])

    keyboard_buttons.append([
        InlineKeyboardButton(text="❌ Закрыть", callback_data="close_recipe_list")
    ])

    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await callback.message.edit_text(text, reply_markup=inline_keyboard)


@router.callback_query(lambda c: c.data == "close_recipe_list")
async def close_recipe_list_callback(callback: types.CallbackQuery):
    """Закрыть список рецептов"""
    await callback.message.delete()


# Fallback handler to ensure main keyboard buttons work regardless of FSM state
@router.message()
async def fallback_menu_handler(message: types.Message):
    text = message.text or ""
    # Delegate to existing handlers based on exact text
    if text == "🍴 Меню":
        await menu_handler(message)
        return
    if text == "🍽 Что едим сегодня":
        await today_portions_handler(message)
        return
    if text == "📅 Что готовим на неделе":
        await weekly_cooking_handler(message)
        return
    if text == "👨‍🍳 Готовить":
        await cook_handler(message)
        return
    if text == "🛒 Купить":
        await buy_handler(message)
        return
    if text == "🍳 Приготовить любое":
        await cook_any_handler(message)
        return
