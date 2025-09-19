from aiogram.fsm.state import State, StatesGroup


class AddRecipeStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_category = State()
    waiting_for_calories = State()
    waiting_for_protein = State()
    waiting_for_fat = State()
    waiting_for_carbs = State()
    waiting_for_ingredients = State()
    waiting_for_instructions = State()
