from flask import Flask, render_template, request, redirect, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection
app = Flask(__name__)
app.secret_key = "change_this_secret_key"


@app.route("/")
def home():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total_gardeners FROM gardeners")
    total_gardeners = cursor.fetchone()["total_gardeners"]

    cursor.execute("SELECT COUNT(*) AS total_plants FROM plants")
    total_plants = cursor.fetchone()["total_plants"]

    cursor.execute("SELECT COUNT(*) AS public_plants FROM plants WHERE is_public = 1")
    public_plants = cursor.fetchone()["public_plants"]

    cursor.close()
    connection.close()

    return render_template(
        "home.html",
        total_gardeners=total_gardeners,
        total_plants=total_plants,
        public_plants=public_plants,
        username=session.get("username"),
        role=session.get("role")
    )


@app.route("/test-db")
def test_db():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT DATABASE();")
    result = cursor.fetchone()
    cursor.close()
    connection.close()

    return f"Database connected successfully: {result[0]}"

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        password2 = request.form.get("password2")

        if not all([username, email, password, password2]):
            flash("Please fill in all fields.")
            return redirect("/register")

        if password != password2:
            flash("Passwords do not match.")
            return redirect("/register")

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT gardener_id FROM gardeners WHERE username = %s OR email = %s",
            (username, email)
        )
        existing_user = cursor.fetchone()

        if existing_user:
            cursor.close()
            connection.close()
            flash("Username or email already exists.")
            return redirect("/register")

        password_hash = generate_password_hash(password)

        cursor.execute(
            """
            INSERT INTO gardeners (username, email, password_hash)
            VALUES (%s, %s, %s)
            """,
            (username, email, password_hash)
        )

        connection.commit()
        cursor.close()
        connection.close()

        flash("Registration successful. Please log in.")
        return redirect("/login")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form.get("role")
        username = request.form.get("username")
        password = request.form.get("password")

        if not all([role, username, password]):
            flash("Please fill in all fields.")
            return redirect("/login")

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        if role == "gardener":
            cursor.execute(
                "SELECT * FROM gardeners WHERE username = %s",
                (username,)
            )
            user = cursor.fetchone()

            if user and user["status"] == "enabled" and check_password_hash(user["password_hash"], password):
                session["user_id"] = user["gardener_id"]
                session["username"] = user["username"]
                session["role"] = "gardener"

                cursor.close()
                connection.close()

                flash("Login successful.")
                return redirect("/gardener/dashboard")

        elif role == "admin":
            cursor.execute(
                "SELECT * FROM admins WHERE username = %s",
                (username,)
            )
            user = cursor.fetchone()

            if user and user["status"] == "enabled" and check_password_hash(user["password_hash"], password):
                session["user_id"] = user["admin_id"]
                session["username"] = user["username"]
                session["role"] = "admin"

                cursor.close()
                connection.close()

                flash("Admin login successful.")
                return redirect("/admin/dashboard")

        cursor.close()
        connection.close()

        flash("Wrong username, password, role, or account disabled.")
        return redirect("/login")

    return render_template("login.html")

@app.route("/gardener/dashboard")
def gardener_dashboard():
    if session.get("role") != "gardener":
        flash("Please log in as a gardener.")
        return redirect("/login")

    return render_template(
        "gardener_dashboard.html",
        username=session.get("username")
    )


@app.route("/admin/dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        flash("Please log in as an admin.")
        return redirect("/login")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total_gardeners FROM gardeners")
    total_gardeners = cursor.fetchone()["total_gardeners"]

    cursor.execute("SELECT COUNT(*) AS total_plants FROM plants")
    total_plants = cursor.fetchone()["total_plants"]

    cursor.close()
    connection.close()

    return render_template(
        "admin_dashboard.html",
        username=session.get("username"),
        total_gardeners=total_gardeners,
        total_plants=total_plants
    )
@app.route("/admin/users")
def admin_users():
    if session.get("role") != "admin":
        flash("Please log in as an admin.")
        return redirect("/login")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT gardener_id, username, email, join_date, status
        FROM gardeners
        ORDER BY join_date DESC
        """
    )
    gardeners = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("admin_users.html", gardeners=gardeners)

@app.route("/admin/users/<int:gardener_id>/enable", methods=["POST"])
def enable_gardener(gardener_id):
    if session.get("role") != "admin":
        flash("Please log in as an admin.")
        return redirect("/login")

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        "UPDATE gardeners SET status = 'enabled' WHERE gardener_id = %s",
        (gardener_id,)
    )

    connection.commit()
    cursor.close()
    connection.close()

    flash("Gardener account enabled.")
    return redirect("/admin/users")


@app.route("/admin/users/<int:gardener_id>/disable", methods=["POST"])
def disable_gardener(gardener_id):
    if session.get("role") != "admin":
        flash("Please log in as an admin.")
        return redirect("/login")

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        "UPDATE gardeners SET status = 'disabled' WHERE gardener_id = %s",
        (gardener_id,)
    )

    connection.commit()
    cursor.close()
    connection.close()

    flash("Gardener account disabled.")
    return redirect("/admin/users")

@app.route("/plants/add", methods=["GET", "POST"])
def add_plant():
    if session.get("role") != "gardener":
        flash("Please log in as a gardener.")
        return redirect("/login")

    if request.method == "POST":
        name = request.form.get("name")
        species = request.form.get("species")
        plant_type = request.form.get("plant_type")
        water_frequency_days = request.form.get("water_frequency_days")
        sunlight = request.form.get("sunlight")
        difficulty = request.form.get("difficulty")
        is_public = request.form.get("is_public")
        health_status = request.form.get("health_status")

        if not all([name, species, plant_type, water_frequency_days, sunlight, difficulty, is_public, health_status]):
            flash("Please fill in all required fields.")
            return redirect("/plants/add")

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO plants
            (gardener_id, name, species, plant_type, water_frequency_days, sunlight, difficulty, is_public, health_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                session.get("user_id"),
                name,
                species,
                plant_type,
                int(water_frequency_days),
                sunlight,
                difficulty,
                int(is_public),
                health_status
            )
        )

        connection.commit()
        cursor.close()
        connection.close()

        flash("Plant added successfully.")
        return redirect("/my-plants")

    return render_template("plant_form.html", title="Add New Plant", plant=None)

@app.route("/admin/users/<int:gardener_id>/delete", methods=["POST"])
def delete_gardener(gardener_id):
    if session.get("role") != "admin":
        flash("Please log in as an admin.")
        return redirect("/login")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        "SELECT plant_id FROM plants WHERE gardener_id = %s",
        (gardener_id,)
    )
    plants = cursor.fetchall()

    for plant in plants:
        plant_id = plant["plant_id"]

        cursor.execute(
            "DELETE FROM plant_photos WHERE plant_id = %s",
            (plant_id,)
        )

        cursor.execute(
            "DELETE FROM care_activities WHERE plant_id = %s",
            (plant_id,)
        )

    cursor.execute(
        "DELETE FROM plants WHERE gardener_id = %s",
        (gardener_id,)
    )

    cursor.execute(
        "DELETE FROM gardeners WHERE gardener_id = %s",
        (gardener_id,)
    )

    connection.commit()
    cursor.close()
    connection.close()

    flash("Gardener account deleted.")
    return redirect("/admin/users")

@app.route("/plants/<int:plant_id>/edit", methods=["GET", "POST"])
def edit_plant(plant_id):
    if session.get("role") != "gardener":
        flash("Please log in as a gardener.")
        return redirect("/login")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM plants
        WHERE plant_id = %s AND gardener_id = %s
        """,
        (plant_id, session.get("user_id"))
    )
    plant = cursor.fetchone()

    if not plant:
        cursor.close()
        connection.close()
        flash("Plant not found or access denied.")
        return redirect("/my-plants")

    if request.method == "POST":
        name = request.form.get("name")
        species = request.form.get("species")
        plant_type = request.form.get("plant_type")
        water_frequency_days = request.form.get("water_frequency_days")
        sunlight = request.form.get("sunlight")
        difficulty = request.form.get("difficulty")
        is_public = request.form.get("is_public")
        health_status = request.form.get("health_status")

        if not all([name, species, plant_type, water_frequency_days, sunlight, difficulty, is_public, health_status]):
            cursor.close()
            connection.close()
            flash("Please fill in all required fields.")
            return redirect(f"/plants/{plant_id}/edit")

        cursor.execute(
            """
            UPDATE plants
            SET name = %s,
                species = %s,
                plant_type = %s,
                water_frequency_days = %s,
                sunlight = %s,
                difficulty = %s,
                is_public = %s,
                health_status = %s
            WHERE plant_id = %s AND gardener_id = %s
            """,
            (
                name,
                species,
                plant_type,
                int(water_frequency_days),
                sunlight,
                difficulty,
                int(is_public),
                health_status,
                plant_id,
                session.get("user_id")
            )
        )

        connection.commit()
        cursor.close()
        connection.close()

        flash("Plant updated successfully.")
        return redirect(f"/plants/{plant_id}")

    cursor.close()
    connection.close()

    return render_template(
        "plant_form.html",
        title="Edit Plant",
        plant=plant
    )
@app.route("/my-plants")
def my_plants():
    if session.get("role") != "gardener":
        flash("Please log in as a gardener.")
        return redirect("/login")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT plant_id, name, species, plant_type, water_frequency_days,
               is_public, health_status
        FROM plants
        WHERE gardener_id = %s
        ORDER BY created_at DESC
        """,
        (session.get("user_id"),)
    )

    plants = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "my_plants.html",
        plants=plants,
        username=session.get("username")
    )

@app.route("/plants/<int:plant_id>")
def plant_detail(plant_id):
    if session.get("role") != "gardener":
        flash("Please log in as a gardener.")
        return redirect("/login")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM plants
        WHERE plant_id = %s AND gardener_id = %s
        """,
        (plant_id, session.get("user_id"))
    )
    plant = cursor.fetchone()

    if not plant:
        cursor.close()
        connection.close()
        flash("Plant not found or access denied.")
        return redirect("/my-plants")

    cursor.execute(
        """
        SELECT activity_id, activity_type, notes, activity_date, created_at
        FROM care_activities
        WHERE plant_id = %s
        ORDER BY activity_date DESC
        """,
        (plant_id,)
    )
    activities = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "plant_detail.html",
        plant=plant,
        activities=activities
    )

@app.route("/plants/<int:plant_id>/water", methods=["POST"])
def mark_as_watered(plant_id):
    if session.get("role") != "gardener":
        flash("Please log in as a gardener.")
        return redirect("/login")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT plant_id
        FROM plants
        WHERE plant_id = %s AND gardener_id = %s
        """,
        (plant_id, session.get("user_id"))
    )
    plant = cursor.fetchone()

    if not plant:
        cursor.close()
        connection.close()
        flash("Plant not found or access denied.")
        return redirect("/my-plants")

    cursor.execute(
        """
        INSERT INTO care_activities (plant_id, activity_type, notes, activity_date)
        VALUES (%s, %s, %s, NOW())
        """,
        (plant_id, "Watering", "Marked as watered")
    )

    connection.commit()
    cursor.close()
    connection.close()

    flash("Plant marked as watered.")
    return redirect(f"/plants/{plant_id}")

@app.route("/plants/<int:plant_id>/activities/add", methods=["POST"])
def add_care_activity(plant_id):
    if session.get("role") != "gardener":
        flash("Please log in as a gardener.")
        return redirect("/login")

    activity_type = request.form.get("activity_type")
    notes = request.form.get("notes")
    activity_date = request.form.get("activity_date")

    if not all([activity_type, activity_date]):
        flash("Please fill in the required activity fields.")
        return redirect(f"/plants/{plant_id}")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT plant_id
        FROM plants
        WHERE plant_id = %s AND gardener_id = %s
        """,
        (plant_id, session.get("user_id"))
    )
    plant = cursor.fetchone()

    if not plant:
        cursor.close()
        connection.close()
        flash("Plant not found or access denied.")
        return redirect("/my-plants")

    cursor.execute(
        """
        INSERT INTO care_activities (plant_id, activity_type, notes, activity_date)
        VALUES (%s, %s, %s, %s)
        """,
        (plant_id, activity_type, notes, activity_date)
    )

    connection.commit()
    cursor.close()
    connection.close()

    flash("Care activity added successfully.")
    return redirect(f"/plants/{plant_id}")
@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect("/login")
@app.route("/gallery")
def gallery():
    search = request.args.get("search", "").strip()
    plant_type = request.args.get("plant_type", "").strip()
    sunlight = request.args.get("sunlight", "").strip()
    difficulty = request.args.get("difficulty", "").strip()

    query = """
        SELECT plant_id, name, species, plant_type, sunlight, difficulty, health_status
        FROM plants
        WHERE is_public = 1
    """
    params = []

    if search:
        query += " AND name LIKE %s"
        params.append(f"%{search}%")

    if plant_type:
        query += " AND plant_type = %s"
        params.append(plant_type)

    if sunlight:
        query += " AND sunlight = %s"
        params.append(sunlight)

    if difficulty:
        query += " AND difficulty = %s"
        params.append(difficulty)

    query += " ORDER BY created_at DESC"

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(query, tuple(params))
    plants = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "gallery.html",
        plants=plants,
        search=search,
        plant_type=plant_type,
        sunlight=sunlight,
        difficulty=difficulty
    )

@app.route("/public/plants/<int:plant_id>")
def public_plant_detail(plant_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT plant_id, name, species, plant_type, water_frequency_days,
               sunlight, difficulty, health_status
        FROM plants
        WHERE plant_id = %s AND is_public = 1
        """,
        (plant_id,)
    )

    plant = cursor.fetchone()

    cursor.close()
    connection.close()

    if not plant:
        flash("Public plant not found.")
        return redirect("/gallery")

    return render_template("public_plant_detail.html", plant=plant)
@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404



if __name__ == "__main__":
    app.run(debug=True)