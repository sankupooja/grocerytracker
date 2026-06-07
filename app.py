import streamlit as st
import database as db
import llm

db.init_db()

st.set_page_config(page_title="Adaptive Meal Planner", layout="wide")

st.title("🥗 Adaptive Meal & Grocery Planner")
st.write("An LLM-powered dynamic meal planner that adapts when your plans change.")

profile = db.get_user_profile()

# --- SIDEBAR: USER PROFILE SETTINGS ---
st.sidebar.header("👤 User Profile")
current_diet = profile.get("dietary_type", "None") if profile else "None"
current_allergies = profile.get("allergies", "None") if profile else "None"
current_calories = profile.get("daily_calories_target", 2000) if profile else 2000
current_budget = profile.get("weekly_budget", 100.0) if profile else 100.0

diet_options = ["None", "Keto", "Vegan", "Vegetarian", "Paleo", "Mediterranean"]
diet_index = diet_options.index(current_diet) if current_diet in diet_options else 0

diet = st.sidebar.selectbox("Dietary Preference", diet_options, index=diet_index)
allergies = st.sidebar.text_input("Allergies / Restrictions (comma-separated)", value=current_allergies)
calories = st.sidebar.number_input("Daily Calorie Target", min_value=500, max_value=10000, value=current_calories, step=100)
budget = st.sidebar.number_input("Weekly Grocery Budget ($)", min_value=10.0, max_value=1000.0, value=float(current_budget), step=5.0)

if st.sidebar.button("Save Profile Settings"):
    db.update_user_profile(diet, allergies, calories, budget)
    st.sidebar.success("Settings saved successfully!")
    st.rerun()

# --- MAIN SECTION ---
st.subheader("🗓️ Your Weekly Plan")

meals = db.get_all_meals()
grocery_items = db.get_grocery_list()

# Generate Plan Button
if st.button("Generate / Reset Weekly Plan", type="primary"):
    with st.spinner("AI is crafting your meal plan and consolidated grocery list..."):
        latest_profile = db.get_user_profile()
        new_plan_data = llm.generate_weekly_plan(latest_profile)
        
        new_meals = new_plan_data.get("meals", [])
        new_groceries = new_plan_data.get("grocery_list", [])
        
        if new_meals:
            # Save Meals
            db.clear_meal_plan()
            db.save_meal_plan(new_meals)
            
            # Save Groceries
            db.clear_grocery_list()
            db.save_grocery_list(new_groceries)
            
            st.success("Successfully generated your new meal plan & smart grocery list!")
            st.rerun()
        else:
            st.error("Failed to generate meal plan. Please check your API key.")

# Display meals if they exist
if meals:
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    tabs = st.tabs(days)
    
    for i, day in enumerate(days):
        with tabs[i]:
            day_meals = [m for m in meals if m["day_of_week"] == day]
            if not day_meals:
                st.write("No meals planned.")
                continue
            
            cols = st.columns(3)
            meal_types = ["Breakfast", "Lunch", "Dinner"]
            for col_idx, m_type in enumerate(meal_types):
                meal = next((m for m in day_meals if m["meal_type"] == m_type), None)
                with cols[col_idx]:
                    if meal:
                        st.markdown(f"### {m_type}")
                        is_eaten = bool(meal["is_eaten"])
                        card_header = f"✅ **{meal['meal_name']}**" if is_eaten else f"🍽️ **{meal['meal_name']}**"
                        st.markdown(card_header)
                        st.caption(f"🔥 Calories: {meal['calories']} kcal")
                        st.markdown(f"**Ingredients:**\n_{meal['ingredients']}_")
                        
                        checked = st.checkbox("Mark as Eaten", value=is_eaten, key=f"chk_{meal['id']}")
                        if checked != is_eaten:
                            db.update_meal_status(meal["id"], int(checked))
                            st.rerun()

    # --- UPDATED: SMART GROCERY SHOPPING LIST ---
    st.write("---")
    st.subheader("🛒 Smart Weekly Grocery List (Consolidated)")
    
    if grocery_items:
        st.write("Cross off items as you buy them at the store:")
        g_cols = st.columns(2)
        half_index = len(grocery_items) // 2
        
        # Column 1
        with g_cols[0]:
            for item in grocery_items[:half_index]:
                is_bought = bool(item["is_bought"])
                label = f"~~{item['item_name']}~~" if is_bought else item["item_name"]
                
                checked = st.checkbox(label, value=is_bought, key=f"g_{item['id']}")
                if checked != is_bought:
                    db.update_grocery_item_status(item["id"], int(checked))
                    st.rerun()
                    
        # Column 2
        with g_cols[1]:
            for item in grocery_items[half_index:]:
                is_bought = bool(item["is_bought"])
                label = f"~~{item['item_name']}~~" if is_bought else item["item_name"]
                
                checked = st.checkbox(label, value=is_bought, key=f"g_{item['id']}")
                if checked != is_bought:
                    db.update_grocery_item_status(item["id"], int(checked))
                    st.rerun()
    else:
        st.write("No groceries logged.")
else:
    st.info("You don't have a plan set up yet. Adjust your settings in the sidebar and click 'Generate / Reset Weekly Plan' to start!")