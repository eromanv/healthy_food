import asyncio
import json

from database import RecipeDB, async_session, init_db
from utils import parse_recipes_from_file


async def load_recipes():
    await init_db()

    # Parse recipes from file
    recipes = parse_recipes_from_file("/app/recipies.txt")

    async with async_session() as session:
        for recipe in recipes:
            db_recipe = RecipeDB(
                name=recipe.name,
                servings=recipe.servings,
                ingredients=json.dumps([ing.dict() for ing in recipe.ingredients]),
                nutrition=json.dumps(recipe.nutrition_per_serving.dict())
                if recipe.nutrition_per_serving
                else None,
                instructions=recipe.instructions,
                image_url=recipe.image_url,
            )
            session.add(db_recipe)
        await session.commit()


if __name__ == "__main__":
    asyncio.run(load_recipes())
