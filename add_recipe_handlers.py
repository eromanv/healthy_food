import re
from typing import List

from aiogram import F, Router, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from models import AddRecipeSchema, CategoryENUM, IngredientModel
from recipe_service import add_recipe
from states import AddRecipeStates

add_recipe_router = Router()

# Inline keyboard for categories
category_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🌅 Завтрак", callback_data="category_завтрак")],
    [InlineKeyboardButton(text="🍽 Основное блюдо", callback_data="category_основное блюдо")],
    [InlineKeyboardButton(text="🧁 Десерт", callback_data="category_десерт")]
])

# Cancel keyboard
cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_recipe")]
])


@add_recipe_router.callback_query(F.data == "add_recipe")
async def start_add_recipe(callback: types.CallbackQuery, state: FSMContext):
    """Start recipe addition process"""
    await state.set_state(AddRecipeStates.waiting_for_name)
    await callback.message.edit_text(
        "🍽 Добавление нового рецепта\n\n"
        "Введите название рецепта:",
        reply_markup=cancel_keyboard
    )


@add_recipe_router.message(StateFilter(AddRecipeStates.waiting_for_name))
async def process_recipe_name(message: types.Message, state: FSMContext):
    """Process recipe name input"""
    recipe_name = message.text.strip()
    if not recipe_name or len(recipe_name) < 3:
        await message.answer(
            "❌ Название рецепта должно содержать минимум 3 символа. "
            "Попробуйте еще раз:",
            reply_markup=cancel_keyboard
        )
        return

    await state.update_data(name=recipe_name)
    await state.set_state(AddRecipeStates.waiting_for_category)
    
    await message.answer(
        f"✅ Название: {recipe_name}\n\n"
        "Выберите категорию блюда:",
        reply_markup=category_keyboard
    )


@add_recipe_router.callback_query(F.data.startswith("category_"))
async def process_category(callback: types.CallbackQuery, state: FSMContext):
    """Process category selection"""
    category_name = callback.data.replace("category_", "")
    category = CategoryENUM(category_name)
    
    await state.update_data(category=category)
    await state.set_state(AddRecipeStates.waiting_for_calories)
    
    await callback.message.edit_text(
        f"✅ Категория: {category_name}\n\n"
        "Введите количество калорий на порцию (ккал):",
        reply_markup=cancel_keyboard
    )


@add_recipe_router.message(StateFilter(AddRecipeStates.waiting_for_calories))
async def process_calories(message: types.Message, state: FSMContext):
    """Process calories input"""
    try:
        calories = float(message.text.strip().replace(",", "."))
        if calories <= 0 or calories > 5000:
            raise ValueError()
    except ValueError:
        await message.answer(
            "❌ Введите корректное количество калорий (от 1 до 5000):",
            reply_markup=cancel_keyboard
        )
        return

    await state.update_data(calories=calories)
    await state.set_state(AddRecipeStates.waiting_for_protein)
    
    await message.answer(
        f"✅ Калории: {calories} ккал\n\n"
        "Введите количество белков на порцию (г):",
        reply_markup=cancel_keyboard
    )


@add_recipe_router.message(StateFilter(AddRecipeStates.waiting_for_protein))
async def process_protein(message: types.Message, state: FSMContext):
    """Process protein input"""
    try:
        protein = float(message.text.strip().replace(",", "."))
        if protein < 0 or protein > 500:
            raise ValueError()
    except ValueError:
        await message.answer(
            "❌ Введите корректное количество белков (от 0 до 500 г):",
            reply_markup=cancel_keyboard
        )
        return

    await state.update_data(protein=protein)
    await state.set_state(AddRecipeStates.waiting_for_fat)
    
    await message.answer(
        f"✅ Белки: {protein} г\n\n"
        "Введите количество жиров на порцию (г):",
        reply_markup=cancel_keyboard
    )


@add_recipe_router.message(StateFilter(AddRecipeStates.waiting_for_fat))
async def process_fat(message: types.Message, state: FSMContext):
    """Process fat input"""
    try:
        fat = float(message.text.strip().replace(",", "."))
        if fat < 0 or fat > 300:
            raise ValueError()
    except ValueError:
        await message.answer(
            "❌ Введите корректное количество жиров (от 0 до 300 г):",
            reply_markup=cancel_keyboard
        )
        return

    await state.update_data(fat=fat)
    await state.set_state(AddRecipeStates.waiting_for_carbs)
    
    await message.answer(
        f"✅ Жиры: {fat} г\n\n"
        "Введите количество углеводов на порцию (г):",
        reply_markup=cancel_keyboard
    )


@add_recipe_router.message(StateFilter(AddRecipeStates.waiting_for_carbs))
async def process_carbs(message: types.Message, state: FSMContext):
    """Process carbs input"""
    try:
        carbs = float(message.text.strip().replace(",", "."))
        if carbs < 0 or carbs > 800:
            raise ValueError()
    except ValueError:
        await message.answer(
            "❌ Введите корректное количество углеводов (от 0 до 800 г):",
            reply_markup=cancel_keyboard
        )
        return

    await state.update_data(carbs=carbs)
    await state.set_state(AddRecipeStates.waiting_for_ingredients)
    
    await message.answer(
        f"✅ Углеводы: {carbs} г\n\n"
        "Введите ингредиенты (каждый с новой строки в формате):\n"
        "Название ингредиента - количество единица\n\n"
        "Например:\n"
        "Курица - 300 г\n"
        "Рис - 100 г\n"
        "Лук - 1 шт",
        reply_markup=cancel_keyboard
    )


@add_recipe_router.message(StateFilter(AddRecipeStates.waiting_for_ingredients))
async def process_ingredients(message: types.Message, state: FSMContext):
    """Process ingredients input"""
    ingredients_text = message.text.strip()
    ingredients = parse_ingredients(ingredients_text)
    
    if not ingredients:
        await message.answer(
            "❌ Не удалось распознать ингредиенты. Проверьте формат:\n"
            "Название - количество единица\n\n"
            "Попробуйте еще раз:",
            reply_markup=cancel_keyboard
        )
        return

    await state.update_data(ingredients=ingredients)
    await state.set_state(AddRecipeStates.waiting_for_instructions)
    
    ingredients_list = '\n'.join([
        f"• {ing.name} - {ing.quantity or ''} {ing.unit or ''}".strip() 
        for ing in ingredients
    ])
    
    await message.answer(
        f"✅ Ингредиенты:\n{ingredients_list}\n\n"
        "Введите рецепт приготовления:",
        reply_markup=cancel_keyboard
    )


@add_recipe_router.message(StateFilter(AddRecipeStates.waiting_for_instructions))
async def process_instructions(message: types.Message, state: FSMContext):
    """Process instructions input and save recipe"""
    instructions = message.text.strip()
    if not instructions or len(instructions) < 10:
        await message.answer(
            "❌ Рецепт должен содержать минимум 10 символов. "
            "Попробуйте еще раз:",
            reply_markup=cancel_keyboard
        )
        return

    # Get all data from state
    data = await state.get_data()
    
    try:
        # Create recipe schema
        recipe_schema = AddRecipeSchema(
            name=data['name'],
            category=data['category'],
            calories=data['calories'],
            protein=data['protein'],
            fat=data['fat'],
            carbs=data['carbs'],
            ingredients=data['ingredients'],
            instructions=instructions
        )
        
        # Save to database
        recipe = await add_recipe(recipe_schema)
        
        # Clear state
        await state.clear()
        
        await message.answer(
            f"✅ Рецепт '{recipe.name}' успешно добавлен!\n\n"
            f"📊 КБЖУ: {recipe.calories}/{recipe.protein}/{recipe.fat}/{recipe.carbs}\n"
            f"🏷 Категория: {recipe.category.value}"
        )
        
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при сохранении рецепта: {str(e)}\n"
            "Попробуйте еще раз."
        )


@add_recipe_router.callback_query(F.data == "cancel_recipe")
async def cancel_recipe_addition(callback: types.CallbackQuery, state: FSMContext):
    """Cancel recipe addition process"""
    await state.clear()
    await callback.message.edit_text("❌ Добавление рецепта отменено.")


def parse_ingredients(text: str) -> List[IngredientModel]:
    """Parse ingredients from text format"""
    ingredients = []
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Parse format: "Name - quantity unit" or "Name - quantity"
        if ' - ' in line:
            name, quantity_unit = line.split(' - ', 1)
            name = name.strip()
            quantity_unit = quantity_unit.strip()
            
            # Extract quantity and unit
            quantity, unit = extract_quantity_unit(quantity_unit)
            
            ingredients.append(IngredientModel(
                name=name,
                quantity=quantity,
                unit=unit
            ))
    
    return ingredients


def extract_quantity_unit(text: str) -> tuple:
    """Extract quantity and unit from text"""
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Pattern for number followed by optional unit
    pattern = r'^(\d+(?:[.,]\d+)?)\s*(.*)$'
    match = re.match(pattern, text)
    
    if match:
        quantity_str = match.group(1).replace(',', '.')
        unit = match.group(2).strip()
        
        try:
            quantity = float(quantity_str)
            return quantity, unit if unit else None
        except ValueError:
            pass
    
    return None, text if text else None
