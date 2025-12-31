from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)

# Database setup
DATABASE = 'travel_mvp.db'

def init_db():
    """Initialize the database and create the FamilyProfiles table if it doesn't exist."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Check if table exists and what columns it has
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='FamilyProfiles'")
    table_exists = cursor.fetchone() is not None
    
    if table_exists:
        # Check if old column exists (migration from kids_ages to kids_birthdates)
        cursor.execute("PRAGMA table_info(FamilyProfiles)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'kids_ages' in columns and 'kids_birthdates' not in columns:
            # Migrate: create new table, copy data, drop old table, rename new table
            cursor.execute('''
                CREATE TABLE FamilyProfiles_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    num_adults INTEGER NOT NULL,
                    num_kids INTEGER NOT NULL,
                    kids_birthdates TEXT,
                    destinations TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    budget REAL NOT NULL,
                    travel_style TEXT NOT NULL,
                    interests TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Copy data (kids_ages will be NULL in new table since we can't convert ages to birthdates)
            cursor.execute('''
                INSERT INTO FamilyProfiles_new 
                (id, num_adults, num_kids, kids_birthdates, destinations, start_date, end_date, budget, travel_style, interests, timestamp)
                SELECT id, num_adults, num_kids, NULL, destinations, start_date, end_date, budget, travel_style, interests, timestamp
                FROM FamilyProfiles
            ''')
            
            cursor.execute('DROP TABLE FamilyProfiles')
            cursor.execute('ALTER TABLE FamilyProfiles_new RENAME TO FamilyProfiles')
            conn.commit()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS FamilyProfiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            num_adults INTEGER NOT NULL,
            num_kids INTEGER NOT NULL,
            kids_birthdates TEXT,
            destinations TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            budget REAL NOT NULL,
            travel_style TEXT NOT NULL,
            interests TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    """Homepage with family profile form."""
    return render_template('index.html')

@app.route('/submit_profile', methods=['POST'])
def submit_profile():
    """Handle form submission, save to database, and redirect to thank you page."""
    # Get form data
    num_adults = request.form.get('num_adults', type=int)
    num_kids = request.form.get('num_kids', type=int)
    
    # Get kids birthdates from month/day/year dropdowns
    kids_birthdates_list = []
    for i in range(1, num_kids + 1):
        month = request.form.get(f'kid_{i}_month', '')
        day = request.form.get(f'kid_{i}_day', '')
        year = request.form.get(f'kid_{i}_year', '')
        if month and day and year:
            # Format as YYYY-MM-DD
            birthdate = f"{year}-{month}-{day}"
            kids_birthdates_list.append(birthdate)
    kids_birthdates = ','.join(kids_birthdates_list) if kids_birthdates_list else ''
    
    destinations = request.form.get('destinations', '')
    start_date = request.form.get('start_date', '')
    end_date = request.form.get('end_date', '')
    budget = request.form.get('budget', type=float)
    travel_style = request.form.get('travel_style', '')
    
    # Get interests (checkboxes - can be multiple)
    interests_list = request.form.getlist('interests')
    interests = ','.join(interests_list) if interests_list else ''
    
    # Print to console
    print("\n" + "="*50)
    print("FAMILY PROFILE SUBMISSION")
    print("="*50)
    print(f"Number of Adults: {num_adults}")
    print(f"Number of Kids: {num_kids}")
    print(f"Kids Birthdates: {kids_birthdates}")
    print(f"Destinations: {destinations}")
    print(f"Start Date: {start_date}")
    print(f"End Date: {end_date}")
    print(f"Budget: ${budget:,.2f}")
    print(f"Travel Style: {travel_style}")
    print(f"Interests: {interests}")
    print("="*50 + "\n")
    
    # Save to database
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO FamilyProfiles 
        (num_adults, num_kids, kids_birthdates, destinations, start_date, end_date, budget, travel_style, interests)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (num_adults, num_kids, kids_birthdates, destinations, start_date, end_date, budget, travel_style, interests))
    
    conn.commit()
    conn.close()
    
    return redirect(url_for('thank_you'))

@app.route('/thank_you')
def thank_you():
    """Thank you page after profile submission."""
    return render_template('thank_you.html')

if __name__ == '__main__':
    # Initialize database on startup
    init_db()
    app.run(debug=True, host='127.0.0.1', port=5000)

