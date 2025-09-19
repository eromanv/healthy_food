from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class CategoryENUM(str, Enum):
    BREAKFAST = "завтрак"
    MAIN_DISH = "основное блюдо"
    DESSERT = "десерт"


class IngredientModel(BaseModel):
    name: str
    quantity: Optional[float] = None  # in grams or pieces
    unit: Optional[str] = None  # g, ml, шт, etc.


class NutritionModel(BaseModel):
    calories: float  # kcal
    protein: float  # g
    fat: float  # g
    carbs: float  # g


class RecipeModel(BaseModel):
    id: Optional[int] = None
    name: str
    ingredients: List[IngredientModel]
    calories: float
    protein: float
    fat: float
    carbs: float
    servings: int
    category: CategoryENUM
    instructions: str
    image_url: Optional[str] = None
    serving_weight: Optional[float] = None  # вес одной порции в граммах


class PortionModel(BaseModel):
    """Модель для расчета порций на день"""

    recipe: RecipeModel
    portion_weight: float  # вес порции в граммах
    portions_count: int  # количество порций
    total_weight: float  # общий вес для приготовления
    nutrition_per_portion: NutritionModel


class DailyPortionsModel(BaseModel):
    """Модель для дневных порций"""

    breakfast: Optional[PortionModel] = None
    main_dish: Optional[PortionModel] = None
    dessert: Optional[PortionModel] = None
    total_nutrition: NutritionModel


class AddRecipeSchema(BaseModel):
    name: str
    calories: float
    protein: float
    fat: float
    carbs: float
    category: CategoryENUM
    ingredients: List[IngredientModel]
    instructions: str


class MealPlanModel(BaseModel):
    day: str  # e.g., "Monday"
    recipe: RecipeModel
    servings_to_prepare: int


class WeeklyPlanModel(BaseModel):
    week_start: str  # date
    meals: List[MealPlanModel]
