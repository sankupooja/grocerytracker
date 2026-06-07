import sqlite3

DB_FILE = "meal_planner.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. User Profile Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dietary_type TEXT DEFAULT 'None',
            allergies TEXT DEFAULT 'None',
            daily_calories_target INTEGER DEFAULT 2000,
            weekly_budget REAL DEFAULT 100.0
        )
    """)
    
    # 2. Meals Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day_of_week TEXT NOT NULL,
            meal_type TEXT NOT NULL,
            meal_name TEXT NOT NULL,
            calories INTEGER DEFAULT 0,
            ingredients TEXT NOT NULL,
            is_eaten INTEGER DEFAULT 0
        )
    """)
    
    # 3. Smart Grocery List Table (NEW)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grocery_list (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            is_bought INTEGER DEFAULT 0
        )
    """)
    
    # 4. Deviations Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS deviations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            food_item TEXT NOT NULL,
            calories_consumed INTEGER DEFAULT 0,
            action_taken TEXT DEFAULT 'Pending'
        )
    """)
    
    cursor.execute("SELECT COUNT(*) FROM user_profile")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO user_profile (dietary_type, allergies, daily_calories_target, weekly_budget)
            VALUES ('None', 'None', 2000, 100.0)
        """)
        
    conn.commit()
    conn.close()

# --- PROFILE HELPERS ---
def get_user_profile():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_profile WHERE id = 1")
    profile = cursor.fetchone()
    conn.close()
    return dict(profile) if profile else None

def update_user_profile(dietary_type, allergies, daily_calories_target, weekly_budget):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE user_profile
        SET dietary_type = ?,
            allergies = ?,
            daily_calories_target = ?,
            weekly_budget = ?
        WHERE id = 1
    """, (dietary_type, allergies, daily_calories_target, weekly_budget))
    conn.commit()
    conn.close()

# --- MEALS HELPERS ---
def clear_meal_plan():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM meals")
    conn.commit()
    conn.close()

def save_meal_plan(meals_list):
    conn = get_connection()
    cursor = conn.cursor()
    for m in meals_list:
        cursor.execute("""
            INSERT INTO meals (day_of_week, meal_type, meal_name, calories, ingredients, is_eaten)
            VALUES (?, ?, ?, ?, ?, 0)
        """, (m['day_of_week'], m['meal_type'], m['meal_name'], m['calories'], m['ingredients']))
    conn.commit()
    conn.close()

def get_all_meals():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM meals")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_meal_status(meal_id, is_eaten):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE meals SET is_eaten = ? WHERE id = ?", (is_eaten, meal_id))
    conn.commit()
    conn.close()

# --- GROCERY LIST HELPERS (NEW) ---
def clear_grocery_list():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM grocery_list")
    conn.commit()
    conn.close()

def save_grocery_list(items_list):
    conn = get_connection()
    cursor = conn.cursor()
    for item in items_list:
        cursor.execute("""
            INSERT INTO grocery_list (item_name, is_bought)
            VALUES (?, 0)
        """, (item,))
    conn.commit()
    conn.close()

def get_grocery_list():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM grocery_list")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_grocery_item_status(item_id, is_bought):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE grocery_list SET is_bought = ? WHERE id = ?", (is_bought, item_id))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()