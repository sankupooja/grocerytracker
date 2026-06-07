import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_weekly_plan(profile):
    diet = profile.get("dietary_type", "None")
    allergies = profile.get("allergies", "None")
    calories = profile.get("daily_calories_target", 2000)
    budget = profile.get("weekly_budget", 100.0)

    system_prompt = (
        "You are an expert chef, certified nutritionist, and professional grocery planner. "
        "Your task is to generate a personalized weekly meal plan (Monday through Sunday, 3 meals/day) "
        "and a corresponding CONSOLIDATED grocery shopping list. "
        "Your response MUST be a single, valid JSON object matching the requested schema exactly."
    )

    user_prompt = f"""
    Please generate a 7-day meal plan and consolidated grocery list based on:
    - Diet Type: {diet}
    - Allergies/Restrictions: {allergies}
    - Target Daily Calories: {calories} kcal
    - Total Weekly Budget: ${budget}
    
    CRITICAL RULE FOR THE GROCERY LIST:
    When consolidating ingredients for the 'grocery_list', convert recipe measurements into standard grocery store purchasing units. 
    - Do NOT output recipe units like '1/2 banana', '1/2 avocado', or '1 cup almond milk'. 
    - Instead, consolidate them into real-world purchasing packages and units (e.g., '3 Bananas', '2 Avocados', '1 bottle of Almond Milk (1L)', '1 pack of Whole Wheat Pasta (500g)').
    
    You must output your response in this exact JSON format:
    {{
      "meals": [
        {{
          "day_of_week": "Monday",
          "meal_type": "Breakfast",
          "meal_name": "Egg and Avocado Toast",
          "calories": 450,
          "ingredients": "1 slice whole wheat bread, 1 egg, 1/4 avocado"
        }}
      ],
      "grocery_list": [
        "1 carton Almond Milk (1L)",
        "3 Bananas",
        "2 Avocados",
        "1 pack of Firm Tofu"
      ]
    }}
    Do not include any other markdown formatting outside the raw JSON.
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
        return {
            "meals": result.get("meals", []),
            "grocery_list": result.get("grocery_list", [])
        }
        
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return {"meals": [], "grocery_list": []}