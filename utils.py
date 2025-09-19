import json
import re
from typing import List

from database import RecipeDB
from models import IngredientModel, NutritionModel, RecipeModel


def parse_recipes_from_file(file_path: str) -> List[RecipeModel]:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    recipes = []
    sections = re.split(r"\n\n+", content.strip())
    current_recipe = {}

    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Parse recipe name
        if "✅" in section and not current_recipe.get("name"):
            lines = section.split("\n")
            for line in lines:
                if "✅" in line:
                    current_recipe["name"] = line.split("✅")[0].strip()
                    break

        # Parse KBZU
        elif "КБЖУ" in section:
            match = re.search(r"КБЖУ\s*-\s*([\d,./]+)", section)
            if match:
                kbju_str = match.group(1).replace(",", ".")
                parts = kbju_str.split("/")
                if len(parts) == 4:
                    try:
                        cal, prot, fat, carb = map(float, parts)
                        current_recipe["nutrition"] = NutritionModel(
                            calories=cal, protein=prot, fat=fat, carbs=carb
                        )
                    except ValueError:
                        pass

        # Parse ingredients
        elif "Ингредиенты" in section:
            lines = section.split("\n")
            servings_match = re.search(r"Ингредиенты\s+(\d+)\s+порции", section)
            if servings_match:
                current_recipe["servings"] = int(servings_match.group(1))

            ingredients = []
            for line in lines:
                line = line.strip()
                if line and (
                    line[0].isdigit()
                    or line.startswith("Соус:")
                    or line.startswith("Для маринада:")
                    or line.startswith("Намазка:")
                ):
                    if ":" in line:
                        # Subcategory, skip
                        continue
                    # Parse ingredient
                    match = re.match(r"\d+\.\s*(.+?)\s*-\s*(.+)", line)
                    if match:
                        name = match.group(1).strip()
                        qty_unit = match.group(2).strip()
                        qty, unit = parse_quantity_unit(qty_unit)
                        ingredients.append(
                            IngredientModel(name=name, quantity=qty, unit=unit)
                        )
                    else:
                        # Ingredient without quantity
                        name = line.split(".", 1)[1].strip() if "." in line else line
                        ingredients.append(
                            IngredientModel(name=name, quantity=None, unit=None)
                        )
            current_recipe["ingredients"] = ingredients

        # Parse instructions
        elif "Рецепт" in section:
            instructions = (
                section.replace("Рецепт :", "").replace("Рецепт:", "").strip()
            )
            current_recipe["instructions"] = instructions
            current_recipe["image_url"] = None

            # If we have all parts, create recipe
            if all(
                key in current_recipe
                for key in [
                    "name",
                    "servings",
                    "ingredients",
                    "nutrition",
                    "instructions",
                ]
            ):
                recipes.append(RecipeModel(**current_recipe))
                current_recipe = {}

    return recipes


def parse_quantity_unit(qty_unit: str) -> tuple:
    qty_unit = qty_unit.lower()
    match = re.match(r"(\d+(?:[.,]\d+)?)\s*(гр|мл|шт|таб|ч\.л|ст\.л|кг|л)?", qty_unit)
    if match:
        qty = float(match.group(1).replace(",", "."))
        unit = match.group(2) if match.group(2) else None
        return qty, unit
    return None, None


def save_recipes_to_db(recipes: List[RecipeModel], session):
    for recipe in recipes:
        db_recipe = RecipeDB(
            name=recipe.name,
            servings=recipe.servings,
            ingredients=json.dumps([ing.dict() for ing in recipe.ingredients]),
            nutrition=json.dumps(recipe.nutrition.dict()) if recipe.nutrition else None,
            instructions=recipe.instructions,
            image_url=recipe.image_url,
        )
        session.add(db_recipe)
    session.commit()
