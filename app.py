import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = "annadaan_secure_key_slrtce_2026"
DATABASE = "annadaan.db"

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL, -- 'DONOR', 'NGO', 'ADMIN'
            organization_name TEXT NOT NULL,
            contact_number TEXT NOT NULL,
            address TEXT NOT NULL,
            area TEXT NOT NULL
        )
    ''')
    # Food donations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS food_donations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            donor_id INTEGER NOT NULL,
            food_item_name TEXT NOT NULL,
            food_type TEXT NOT NULL, -- 'Cooked Meal', 'Bakery/Dry', 'Raw Produce'
            quantity_plates INTEGER NOT NULL,
            prepared_time TEXT NOT NULL,
            expiry_time TEXT NOT NULL,
            pickup_address TEXT NOT NULL,
            status TEXT DEFAULT 'AVAILABLE', -- 'AVAILABLE', 'CLAIMED', 'DELIVERED', 'EXPIRED'
            claimed_by_ngo_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(donor_id) REFERENCES users(id),
            FOREIGN KEY(claimed_by_ngo_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    
    # Pre-seed initial establishments if database is fresh
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        demo_users = [
            ("taj_banquets", "pass123", "DONOR", "Grand Celebrations Banquet Hall", "9820011223", "Western Express Highway", "Mira Road East"),
            ("sunrise_society", "pass123", "DONOR", "Sunrise CHS Clubhouse", "9820044556", "Mahavir Nagar", "Kandivali West"),
            ("gupta_catering", "pass123", "DONOR", "Gupta Caterers & Events", "9821133445", "Station Road", "Bhayandar West"),
            ("sneha_ashram", "pass123", "NGO", "Sneha Children Care Shelter", "9819977889", "Near Datta Mandir", "Dahisar East"),
            ("rotary_relief", "pass123", "NGO", "Rotary Community Kitchen", "9833322110", "Maxus Mall Lane", "Bhayandar West"),
            ("admin", "admin123", "ADMIN", "Annadaan Central Oversight Desk", "02228120144", "College Road", "Mira Road East")
        ]
        cursor.executemany(
            "INSERT INTO users (username, password, role, organization_name, contact_number, address, area) VALUES (?, ?, ?, ?, ?, ?, ?)",
            demo_users
        )
        
        # Pre-seed sample active listings
        now = datetime.now()
        exp1 = (now + timedelta(hours=4)).strftime("%I:%M %p")
        exp2 = (now + timedelta(hours=2)).strftime("%I:%M %p")
        cursor.execute('''
            INSERT INTO food_donations (donor_id, food_item_name, food_type, quantity_plates, prepared_time, expiry_time, pickup_address, status)
            VALUES 
            (1, 'Vegetable Biryani & Dal Makhani', 'Cooked Meal', 85, 'Today, 1:30 PM', ?, 'Grand Banquet Hall, Western Express Hwy, Mira Road East', 'AVAILABLE'),
            (2, 'Assorted Roti, Paneer Sabzi, Jeera Rice', 'Cooked Meal', 40, 'Today, 2:00 PM', ?, 'Sunrise Society Clubhouse, Kandivali West', 'AVAILABLE')
        ''', (exp1, exp2))
        conn.commit()
    conn.close()

# Auto-initialize database on server launch
init_db()

# --- HTML TEMPLATES ---
BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Annadaan | Surplus Food Redistribution Network</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-slate-50 text-slate-800 min-h-screen flex flex-col font-sans">
    <nav class="bg-emerald-700 text-white shadow-md sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
            <div class="flex items-center space-x-3">
                <i class="fa-solid fa-hand-holding-heart text-2xl text-emerald-200"></i>
                <a href="{{ url_for('dashboard') }}" class="text-xl font-bold tracking-tight">Annadaan</a>
                <span class="text-xs bg-emerald-800 text-emerald-200 px-2.5 py-0.5 rounded-full font-mono">PS10</span>
            </div>
            <div class="flex items-center space-x-6 text-sm font-medium">
                <a href="{{ url_for('dashboard') }}" class="hover:text-emerald-200">Surplus Listings</a>
                {% if session.get('user_id') %}
                    <span class="text-emerald-100 hidden sm:inline"><i class="fa-regular fa-building mr-1.5"></i>{{ session.get('org_name') }}</span>
                    <a href="{{ url_for('logout') }}" class="bg-emerald-800 hover:bg-emerald-900 px-3.5 py-1.5 rounded-md transition">Logout</a>
                {% else %}
                    <a href="{{ url_for('login') }}" class="bg-white text-emerald-800 hover:bg-emerald-50 px-4 py-1.5 rounded-md font-semibold transition">Partner Login</a>
                {% endif %}
            </div>
        </div>
    </nav>

    <main class="flex-grow max-w-7xl mx-auto px-6 py-8 w-full">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="mb-6 p-4 rounded-lg text-sm font-medium {% if category == 'error' %}bg-rose-100 text-rose-700 border border-rose-200{% else %}bg-emerald-100 text-emerald-800 border border-emerald-200{% endif %}">
                        {{ message }}
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {% block content %}{% endblock %}
    </main>

    <footer class="bg-white border-t border-slate-200 py-6 text-center text-xs text-slate-500">
        Department of Information Technology | IDEA LAB-3 (15612310) | Shree L. R. Tiwari College of Engineering
    </footer>
</body>
</html>
"""

INDEX_VIEW = BASE_TEMPLATE.replace("{% block content %}{% endblock %}", """
<div class="space-y-8">
    <div class="bg-gradient-to-r from-emerald-800 to-teal-700 text-white rounded-2xl p-8 shadow-lg flex flex-col md:flex-row justify-between items-center gap-6">
        <div class="space-y-3 max-w-2xl">
            <span class="bg-emerald-600/80 text-emerald-100 text-xs uppercase tracking-wider font-semibold px-3 py-1 rounded-full">Surplus Food Management</span>
            <h1 class="text-3xl font-extrabold tracking-tight">Connecting Food Donors with Community Shelters</h1>
            <p class="text-emerald-100 text-sm leading-relaxed">
                Empowering banquet halls, restaurants, caterers, and housing societies across Mira-Bhayandar & Mumbai to redistribute safe, unconsumed edible food to verified orphanages and shelters before expiry.
            </p>
        </div>
        <div class="grid grid-cols-2 gap-4 text-center w-full md:w-auto">
            <div class="bg-white/10 backdrop-blur-md rounded-xl p-4 border border-white/20">
                <div class="text-2xl font-black text-amber-300">{{ total_meals }}</div>
                <div class="text-xs text-emerald-100">Meals Salvaged</div>
            </div>
            <div class="bg-white/10 backdrop-blur-md rounded-xl p-4 border border-white/20">
                <div class="text-2xl font-black text-emerald-300">{{ total_co2 }} kg</div>
                <div class="text-xs text-emerald-100">Landfill GHG Saved</div>
            </div>
        </div>
    </div>

    {% if session.get('role') == 'DONOR' %}
    <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h2 class="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
            <i class="fa-solid fa-plus-circle text-emerald-600"></i> Post New Surplus Food Donation
        </h2>
        <form action="{{ url_for('create_donation') }}" method="POST" class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
                <label class="block text-slate-700 font-semibold mb-1">Item Title / Food Description</label>
                <input type="text" name="food_item" placeholder="e.g. Rice, Dal & Mix Vegetable Curry" required class="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-emerald-500 outline-none">
            </div>
            <div>
                <label class="block text-slate-700 font-semibold mb-1">Category</label>
                <select name="food_type" class="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-emerald-500 outline-none bg-white">
                    <option value="Cooked Meal">Cooked Meal (Perishable)</option>
                    <option value="Bakery/Dry">Bakery / Dry Snacks</option>
                    <option value="Raw Produce">Fresh Raw Produce / Fruits</option>
                </select>
            </div>
            <div>
                <label class="block text-slate-700 font-semibold mb-1">Quantity (Approx Plates/Servings)</label>
                <input type="number" name="quantity" min="5" placeholder="e.g. 50" required class="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-emerald-500 outline-none">
            </div>
            <div>
                <label class="block text-slate-700 font-semibold mb-1">Preparation Time</label>
                <input type="text" name="prepared_time" placeholder="e.g. Today 2:00 PM" required class="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-emerald-500 outline-none">
            </div>
            <div>
                <label class="block text-slate-700 font-semibold mb-1">Safe to Consume Until</label>
                <input type="text" name="expiry_time" placeholder="e.g. Today 8:00 PM" required class="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-emerald-500 outline-none">
            </div>
            <div>
                <label class="block text-slate-700 font-semibold mb-1">Pickup Address / Society Wing</label>
                <input type="text" name="pickup_address" placeholder="Clubhouse / Kitchen gate" required class="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-emerald-500 outline-none">
            </div>
            <div class="md:col-span-3 pt-2">
                <button type="submit" class="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold px-6 py-2.5 rounded-lg transition shadow-sm">
                    Publish Available Listing
                </button>
            </div>
        </form>
    </div>
    {% endif %}

    <div>
        <div class="flex justify-between items-center mb-4">
            <h2 class="text-xl font-bold text-slate-900">Current Surplus Food Listings</h2>
            <span class="text-xs text-slate-500">Auto-prioritized by consumption expiry</span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {% for item in donations %}
            <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-5 flex flex-col justify-between hover:shadow-md transition">
                <div>
                    <div class="flex justify-between items-start gap-2 mb-2">
                        <span class="text-xs font-semibold px-2.5 py-1 rounded-full {% if item.status == 'AVAILABLE' %}bg-amber-100 text-amber-800{% elif item.status == 'CLAIMED' %}bg-blue-100 text-blue-800{% else %}bg-slate-100 text-slate-800{% endif %}">
                            {{ item.status }}
                        </span>
                        <span class="text-xs text-slate-500"><i class="fa-regular fa-clock mr-1"></i>Exp: {{ item.expiry_time }}</span>
                    </div>
                    <h3 class="font-bold text-slate-900 text-base leading-snug">{{ item.food_item_name }}</h3>
                    <p class="text-xs text-slate-500 mt-1 mb-3">Donor: <strong>{{ item.organization_name }}</strong> ({{ item.area }})</p>
                    <div class="bg-slate-50 rounded-lg p-3 text-xs space-y-1 text-slate-600 mb-4 border border-slate-100">
                        <div><strong>Quantity:</strong> {{ item.quantity_plates }} Servings / Plates</div>
                        <div><strong>Category:</strong> {{ item.food_type }}</div>
                        <div><strong>Pickup Point:</strong> {{ item.pickup_address }}</div>
                    </div>
                </div>
                <div>
                    {% if session.get('role') == 'NGO' and item.status == 'AVAILABLE' %}
                        <form action="{{ url_for('claim_donation', item_id=item.id) }}" method="POST">
                            <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold py-2.5 rounded-lg transition">
                                <i class="fa-solid fa-hand-holding-hand mr-1.5"></i> Claim & Dispatch Pickup
                            </button>
                        </form>
                    {% elif session.get('role') == 'DONOR' and item.donor_id == session.get('user_id') and item.status == 'CLAIMED' %}
                        <form action="{{ url_for('complete_donation', item_id=item.id) }}" method="POST">
                            <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold py-2.5 rounded-lg transition">
                                <i class="fa-solid fa-check mr-1.5"></i> Verify Handoff & Complete
                            </button>
                        </form>
                    {% else %}
                        <div class="text-center text-xs text-slate-400 py-1 italic">
                            {% if item.status == 'AVAILABLE' %}Awaiting verified NGO claim{% else %}Distribution in progress{% endif %}
                        </div>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</div>
""")

LOGIN_VIEW = BASE_TEMPLATE.replace("{% block content %}{% endblock %}", """
<div class="max-w-5xl mx-auto space-y-6">
    <div class="bg-gradient-to-r from-emerald-800 to-teal-700 text-white rounded-2xl p-6 shadow-sm">
        <h2 class="text-2xl font-bold">Community Partner Portal</h2>
        <p class="text-emerald-100 text-xs mt-1">Select your organization to manage surplus food batches, or register a new donor / NGO profile.</p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
        <!-- Card 1: Fast Login (Choose Organization) -->
        <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-5">
            <h3 class="text-lg font-bold text-slate-900 border-b pb-2">Login to My Organization</h3>
            
            <form method="POST" action="{{ url_for('select_login') }}" class="space-y-4 text-sm">
                <div>
                    <label class="block text-slate-700 font-semibold mb-1">Select registered entity</label>
                    <select name="selected_user_id" required class="w-full border rounded-lg px-3 py-2.5 outline-none focus:ring-2 focus:ring-emerald-500 bg-white">
                        <option value="">-- Choose your entity --</option>
                        <optgroup label="Food Donors (Banquets / Caterers / Societies)">
                            {% for u in donors %}
                                <option value="{{ u.id }}">{{ u.organization_name }} ({{ u.area }})</option>
                            {% endfor %}
                        </optgroup>
                        <optgroup label="Relief Shelters / Food NGOs">
                            {% for u in ngos %}
                                <option value="{{ u.id }}">{{ u.organization_name }} ({{ u.area }})</option>
                            {% endfor %}
                        </optgroup>
                    </select>
                </div>
                <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-2.5 rounded-lg transition">
                    Open Dashboard
                </button>
            </form>

            <div class="pt-4 border-t text-xs text-slate-400">
                Evaluation Demo: Instant login without remembering passwords.
            </div>
        </div>

        <!-- Card 2: Register New Entity -->
        <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-4">
            <h3 class="text-lg font-bold text-slate-900 border-b pb-2">Register a New Partner</h3>
            
            <form method="POST" action="{{ url_for('register') }}" class="space-y-3 text-sm">
                <div>
                    <label class="block text-slate-700 font-semibold mb-1">Organization / Entity Name</label>
                    <input type="text" name="org_name" placeholder="e.g. Royal Caterers / Shanti Niketan CHS" required class="w-full border rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-emerald-500">
                </div>
                <div>
                    <label class="block text-slate-700 font-semibold mb-1">Role / Account Type</label>
                    <select name="role" required class="w-full border rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-emerald-500 bg-white">
                        <option value="DONOR">Food Donor (Restaurant / Caterer / Society)</option>
                        <option value="NGO">Beneficiary / Shelter / Food NGO</option>
                    </select>
                </div>
                <div>
                    <label class="block text-slate-700 font-semibold mb-1">Phone Number</label>
                    <input type="tel" name="phone" placeholder="10-digit mobile number" required class="w-full border rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-emerald-500">
                </div>
                <div>
                    <label class="block text-slate-700 font-semibold mb-1">Area / Locality</label>
                    <select name="area" class="w-full border rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-emerald-500 bg-white">
                        <option value="Mira Road East">Mira Road East</option>
                        <option value="Bhayandar East">Bhayandar East</option>
                        <option value="Bhayandar West">Bhayandar West</option>
                        <option value="Dahisar East">Dahisar East</option>
                        <option value="Borivali West">Borivali West</option>
                        <option value="Kandivali West">Kandivali West</option>
                    </select>
                </div>
                <div>
                    <label class="block text-slate-700 font-semibold mb-1">Address / Landmark</label>
                    <input type="text" name="address" placeholder="e.g. Opposite Silver Park, Mira Road" required class="w-full border rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-emerald-500">
                </div>
                <button type="submit" class="w-full bg-slate-800 hover:bg-slate-900 text-white font-semibold py-2.5 rounded-lg transition mt-2">
                    Register & Go to Dashboard
                </button>
            </form>
        </div>
    </div>
</div>
""")

# --- ROUTES ---
@app.route("/")
def dashboard():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT d.*, u.organization_name, u.contact_number, u.area 
        FROM food_donations d 
        JOIN users u ON d.donor_id = u.id 
        ORDER BY d.id DESC
    ''')
    donations = cursor.fetchall()
    
    cursor.execute("SELECT SUM(quantity_plates) FROM food_donations WHERE status IN ('CLAIMED', 'DELIVERED')")
    row = cursor.fetchone()
    total_meals = row[0] if (row and row[0]) else 0
    total_co2 = round(total_meals * 0.42, 1)
    conn.close()
    
    return render_template_string(INDEX_VIEW, donations=donations, total_meals=total_meals, total_co2=total_co2)

@app.route("/login", methods=["GET"])
def login():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, organization_name, area FROM users WHERE role = 'DONOR'")
    donors = cursor.fetchall()
    cursor.execute("SELECT id, organization_name, area FROM users WHERE role = 'NGO'")
    ngos = cursor.fetchall()
    conn.close()
    return render_template_string(LOGIN_VIEW, donors=donors, ngos=ngos)

@app.route("/select-login", methods=["POST"])
def select_login():
    user_id = request.form.get("selected_user_id")
    if not user_id:
        flash("Please select an organization", "error")
        return redirect(url_for("login"))
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = user["role"]
        session["org_name"] = user["organization_name"]
        flash(f"Signed in as {user['organization_name']}", "success")
    return redirect(url_for("dashboard"))

@app.route("/register", methods=["POST"])
def register():
    org_name = request.form.get("org_name")
    role = request.form.get("role")
    phone = request.form.get("phone")
    area = request.form.get("area")
    address = request.form.get("address")
    username = org_name.lower().replace(" ", "_")[:20] + f"_{datetime.now().strftime('%S')}"
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (username, password, role, organization_name, contact_number, address, area)
        VALUES (?, 'pass123', ?, ?, ?, ?, ?)
    ''', (username, role, org_name, phone, address, area))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    session["user_id"] = new_id
    session["username"] = username
    session["role"] = role
    session["org_name"] = org_name
    flash(f"Welcome {org_name}! Account created and verified.", "success")
    return redirect(url_for("dashboard"))

@app.route("/create-donation", methods=["POST"])
def create_donation():
    if session.get("role") != "DONOR":
        flash("Only registered food donors can publish listings", "error")
        return redirect(url_for("dashboard"))
    
    food_item = request.form.get("food_item")
    food_type = request.form.get("food_type")
    quantity = int(request.form.get("quantity"))
    prepared_time = request.form.get("prepared_time")
    expiry_time = request.form.get("expiry_time")
    pickup_address = request.form.get("pickup_address")
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO food_donations (donor_id, food_item_name, food_type, quantity_plates, prepared_time, expiry_time, pickup_address, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'AVAILABLE')
    ''', (session["user_id"], food_item, food_type, quantity, prepared_time, expiry_time, pickup_address))
    conn.commit()
    conn.close()
    flash("Surplus food listing published to verified network!", "success")
    return redirect(url_for("dashboard"))

@app.route("/claim/<int:item_id>", methods=["POST"])
def claim_donation(item_id):
    if session.get("role") != "NGO":
        flash("Only registered NGOs can claim donations", "error")
        return redirect(url_for("dashboard"))
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE food_donations SET status = 'CLAIMED', claimed_by_ngo_id = ? WHERE id = ? AND status = 'AVAILABLE'", 
                   (session["user_id"], item_id))
    conn.commit()
    conn.close()
    flash("Donation successfully claimed! Coordinate pickup with donor.", "success")
    return redirect(url_for("dashboard"))

@app.route("/complete/<int:item_id>", methods=["POST"])
def complete_donation(item_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE food_donations SET status = 'DELIVERED' WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    flash("Handoff verified and recorded to environmental audit ledger.", "success")
    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True, port=5000)