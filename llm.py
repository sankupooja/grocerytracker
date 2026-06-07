import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_grocery_list_proposal(profile):
    """
    Step 1: Generates a list of suggested groceries with estimated costs
    that strictly stay within the specified budget ceiling.
    """
    diet = profile.get("dietary_type", "None")
    allergies = profile.get("allergies", "None")
    calories = profile.get("daily_calories_target", 2000)
    budget = profile.get("weekly_budget", 100.0)

    system_prompt = (
        "You are an expert budget-focused meal planner and financial assistant. "
        "Your goal is to suggest a list of grocery items with estimated costs that "
        "allows the user to meet their calorie and dietary needs for 1 week. "
        "Your response MUST be a single, valid JSON object matching the requested schema."
    )

    user_prompt = f"""
    Please generate a proposed list of real-world groceries to buy for the week:
    - Diet Type: {diet}
    - Allergies/Restrictions: {allergies}
    - Target Daily Calories: {calories} kcal
    - MAXIMUM Weekly Budget Limit: ${budget}
    
    IMPORTANT RULES:
    1. The sum of all 'estimated_cost' values MUST be strictly less than or equal to ${budget}. Do not exceed it.
    2. Convert recipe fractions into real-world purchasing quantities (e.g., '1 bunch of Bananas', '1 carton of eggs (12)', '1 bag of Rice (1kg)').
    3. Include a realistic estimated price (in USD) for each item based on average grocery store pricing.
    
    Output format:
    {{
      "grocery_list": [
        {{"item_name": "1 carton Almond Milk (1L)", "estimated_cost": 3.49}},
        {{"item_name": "1 bunch of Bananas", "estimated_cost": 1.99}},
        {{"item_name": "1 carton of Eggs (12)", "estimated_cost": 4.29}}
      ]
    }}
    Do not output any markdown formatting other than the raw JSON.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.5
        )
        result = json.loads(response.choices[0].message.content)
        return result.get("grocery_list", [])
    except Exception as e:
        print(f"Error suggesting groceries: {e}")
        return []


def generate_meals_from_groceries(profile, bought_groceries):
    """
    Step 2: Generates a weekly meal plan constrained strictly to
    the list of bought groceries, plus simple pantry staples.
    """
    diet = profile.get("dietary_type", "None")
    allergies = profile.get("allergies", "None")
    calories = profile.get("daily_calories_target", 2000)

    system_prompt = (
        "You are a master creative chef and resource-constrained nutritionist. "
        "Your task is to build a complete 7-day meal plan (Monday through Sunday, 3 meals/day) "
        "using ONLY the specific groceries the user bought, plus basic pantry staples."
    )

    user_prompt = f"""
    Please construct a 7-day meal plan based on these constraints:
    - Diet Style: {diet}
    - Allergies/Restrictions: {allergies}
    - Target Daily Calories: {calories} kcal
    - List of groceries I actually bought: {bought_groceries}
    
    STRICT MEAL COMPOSITION RULE:
    You must construct the recipes using ONLY the items in the bought groceries list. 
    You may assume the user has basic pantry staples on hand: water, salt, black pepper, and basic cooking oil (olive/vegetable).
    No other unpurchased ingredients are allowed.
    
    Output format:
    {{
      "meals": [
        {{
          "day_of_week": "Monday",
          "meal_type": "Breakfast",
          "meal_name": "Title of Meal",
          "calories": 450,
          "ingredients": "List of specifically used items from the bought list"
        }}
      ]
    }}
    Do not output any introductory or closing text. Output ONLY raw JSON.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        result = json.loads(response.choices[0].message.content)
        return result.get("meals", [])
    except Exception as e:
        print(f"Error generating constrained meals: {e}")
        return []