import json
from typing import List

from sqlalchemy import select

from database import RecipeDB, async_session
from models import AddRecipeSchema, IngredientModel, RecipeModel


async def add_recipe(recipe_data: AddRecipeSchema) -> RecipeModel:
    """Add new recipe to database"""
    async with async_session() as session:
        # Convert ingredients to JSON string
        ingredients_json = json.dumps([ing.dict() for ing in recipe_data.ingredients])

        # Create database record
        db_recipe = RecipeDB(
            name=recipe_data.name,
            calories=recipe_data.calories,
            protein=recipe_data.protein,
            fat=recipe_data.fat,
            carbs=recipe_data.carbs,
            ingredients=ingredients_json,
            category=recipe_data.category,
            instructions=recipe_data.instructions,
        )

        session.add(db_recipe)
        await session.commit()
        await session.refresh(db_recipe)

        # Return RecipeModel
        return _convert_db_to_model(db_recipe)


async def get_all_recipes() -> List[RecipeModel]:
    """Get all recipes from database"""
    async with async_session() as session:
        result = await session.execute(select(RecipeDB))
        db_recipes = result.scalars().all()

        recipes = []
        for db_recipe in db_recipes:
            recipes.append(_convert_db_to_model(db_recipe))

        return recipes


async def get_recipe_by_id(recipe_id: int) -> RecipeModel:
    """Get recipe by ID from database"""
    async with async_session() as session:
        result = await session.execute(select(RecipeDB).where(RecipeDB.id == recipe_id))
        db_recipe = result.scalar_one_or_none()

        if db_recipe:
            return _convert_db_to_model(db_recipe)
        return None


def _convert_db_to_model(db_recipe: RecipeDB) -> RecipeModel:
    """Convert database record to Pydantic model"""
    ingredients_data = json.loads(db_recipe.ingredients)
    if isinstance(ingredients_data, dict):
        # Convert dict to list of IngredientModel dicts
        ingredients = [
            IngredientModel(name=name, quantity=qty, unit=None).dict()
            for name, qty in ingredients_data.items()
        ]
    else:
        # Assume it's already a list of dicts
        ingredients = ingredients_data

    ingredients_models = [IngredientModel(**ing) for ing in ingredients]

    return RecipeModel(
        id=db_recipe.id,
        name=db_recipe.name,
        calories=db_recipe.calories,
        protein=db_recipe.protein,
        fat=db_recipe.fat,
        carbs=db_recipe.carbs,
        servings=db_recipe.servings,
        ingredients=ingredients_models,
        category=db_recipe.category,
        instructions=db_recipe.instructions,
    )
