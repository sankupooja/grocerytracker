import streamlit as st
import database as db
import llm

# Ensure database is initialized
db.init_db()

st.set_page_config(page_title="Adaptive Meal Planner", layout="wide")

st.title("🥗 Adaptive Meal & Grocery Planner")
st.write("Plan your budget-restricted grocery trip first, then cook meals using only what you bought.")

# Load profile data
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

# Reset button in the sidebar to start over easily
if st.sidebar.button("⚠️ Clear & Reset All"):
    db.reset_all_data()
    st.sidebar.warning("Cleared all meals and groceries!")
    st.rerun()


# --- APP STATE CHECKING ---
grocery_items = db.get_grocery_list()
meals = db.get_all_meals()

# ==========================================
# PHASE 1 & 2: GROCERY PLANNING & CHECKLIST
# ==========================================
st.subheader("🛒 Phase 1: Smart Grocery Planner")

if not grocery_items:
    st.info("Start by generating a grocery budget proposal based on your Profile constraints.")
    if st.button("Generate Grocery Proposal", type="primary"):
        with st.spinner("Calculating optimal groceries matching your budget limit..."):
            latest_profile = db.get_user_profile()
            proposed_groceries = llm.generate_grocery_list_proposal(latest_profile)
            if proposed_groceries:
                db.save_grocery_list(proposed_groceries)
                st.success("Proposed grocery list generated!")
                st.rerun()
            else:
                st.error("Error generating groceries. Check console/API key.")
else:
    # Calculate costs
    total_allowed = current_budget
    total_bought_cost = sum(item["estimated_cost"] for item in grocery_items if item["is_bought"] == 1)
    total_proposed_cost = sum(item["estimated_cost"] for item in grocery_items)
    
    st.markdown(f"**Proposed List Value:** ${total_proposed_cost:.2f} | **Your Checked-Off Cart:** `${total_bought_cost:.2f}` / Limit: `${total_allowed:.2f}`")
    
    if total_bought_cost > total_allowed:
        st.error("🚨 Warning: Your cart exceeds your weekly budget limit! Uncheck some items.")
        
    st.write("Check off items you **actually bought** at the store:")
    
    g_cols = st.columns(2)
    half_index = len(grocery_items) // 2
    
    # Left Column Checklist
    with g_cols[0]:
        for item in grocery_items[:half_index]:
            is_bought = bool(item["is_bought"])
            label = f"~~{item['item_name']}~~ (${item['estimated_cost']:.2f})" if is_bought else f"{item['item_name']} (${item['estimated_cost']:.2f})"
            checked = st.checkbox(label, value=is_bought, key=f"g_{item['id']}")
            if checked != is_bought:
                db.update_grocery_item_status(item["id"], int(checked))
                st.rerun()
                
    # Right Column Checklist
    with g_cols[1]:
        for item in grocery_items[half_index:]:
            is_bought = bool(item["is_bought"])
            label = f"~~{item['item_name']}~~ (${item['estimated_cost']:.2f})" if is_bought else f"{item['item_name']} (${item['estimated_cost']:.2f})"
            checked = st.checkbox(label, value=is_bought, key=f"g_{item['id']}")
            if checked != is_bought:
                db.update_grocery_item_status(item["id"], int(checked))
                st.rerun()

    # ==========================================
    # PHASE 3: MEAL PLANNER (CONSTRAINED TO CART)
    # ==========================================
    st.write("---")
    st.subheader("🍳 Phase 2: Cooking Meal Plan")
    
    bought_items = db.get_bought_groceries()
    
    if not meals:
        st.warning("You must check off items in your cart to buy first before generating meals!")
        st.write(f"Currently selected inventory items: `{len(bought_items)}` items.")
        
        # Disable button if no groceries are checked
        btn_disabled = len(bought_items) == 0
        if st.button("Generate Meal Plan from Cart", type="primary", disabled=btn_disabled):
            with st.spinner("AI is formulating meals using ONLY your bought items..."):
                latest_profile = db.get_user_profile()
                new_meals = llm.generate_meals_from_groceries(latest_profile, bought_items)
                if new_meals:
                    db.save_meal_plan(new_meals)
                    st.success("Meal plan successfully constructed from your inventory!")
                    st.rerun()
                else:
                    st.error("Failed to generate meals. Ensure you checked off a reasonable variety of items.")
    else:
        st.success("Your customized weekly menu is active!")
        
        # Display meals in calendar tab structure
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        tabs = st.tabs(days)
        
        for i, day in enumerate(days):
            with tabs[i]:
                day_meals = [m for m in meals if m["day_of_week"] == day]
                if not day_meals:
                    st.info("No meals planned for today.")
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
                            st.markdown(f"**Used Bought Groceries:**\n_{meal['ingredients']}_")
                            
                            checked = st.checkbox("Mark as Eaten", value=is_eaten, key=f"chk_{meal['id']}")
                            if checked != is_eaten:
                                db.update_meal_status(meal["id"], int(checked))
                                st.rerun()
                        else:
                            st.info(f"No {m_type} planned.")