import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, json
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required, get_coord, get_add

google_api = 'AIzaSyB8tBulyh-SduPrWVmryVfx4uuLC1_wrgA'

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response



# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///stairs.db")

# Make sure API key is set
#if not os.environ.get("API_KEY"):
    #raise RuntimeError("API_KEY not set")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            alert = "Must provide username"
            return render_template("login.html", alert=alert)

        # Ensure password was submitted
        elif not request.form.get("password"):
            alert = "Must provide password"
            return render_template("login.html", alert=alert)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            alert = "Invalid username and/or password"
            return render_template("login.html", alert=alert)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "GET":
        return render_template("register.html")

    else:
        # Ensure username was submitted
        if not request.form.get("username"):
            alert = "Username required"
            return render_template("register.html", alert=alert)

        # Ensure password was submitted
        elif not request.form.get("password"):
            alert = "Must provide password"
            return render_template("register.html", alert=alert)

        # Ensure password was submitted
        elif not request.form.get("confirmation"):
            alert = "Must confirm password"
            return render_template("register.html", alert=alert)


        # Query database for username
        accounts = db.execute("SELECT username FROM users WHERE username = ?", request.form.get("username"))

        if len(accounts) != 0:
            alert = "Username taken"
            return render_template("register.html", alert=alert)

         # Ensure confirmation and password are the same
        elif not request.form.get("confirmation") == request.form.get("password"):
            alert = "Password and confirmation so not match"
            return render_template("register.html", alert=alert)

        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", request.form.get("username"), generate_password_hash(request.form.get("password")))
        return render_template("login.html")


@app.route("/")
@login_required
def index():
    return render_template("search.html")


@app.route("/addstairs", methods=["GET", "POST"])
@login_required
def add_stairs():

    if request.method == "GET":
        return render_template("add.html")
    else:
        # make sure location entered
        if not request.form.get("location"):
            alert = "location required"
            return render_template("add.html", alert=alert)
        #elif not request.form.get("photo"):
            #alert = "photo of stairs required"
            #return render_template("add.html")
        else:

            coordinates = get_coord(request.form.get("location"))

            # if no coordinates are returned stay on page & tell user
            if coordinates == 'no results':
                alert = "Could not find location of stairs"
                return render_template("add.html", alert=alert)

            # if search returned multiple places stay on page & tell user
            elif coordinates == 'multiple results':
                alert = "Enter a more specific address"
                return render_template("add.html", alert=alert)
            else:
                # query for those coordinates as to not add repeats
                spots = db.execute("SELECT id FROM locations WHERE latitude = ? AND longitude = ?", coordinates['lat'], coordinates['lng'])

                # check if repeat
                if len(spots) == 0:
                    db.execute("INSERT INTO locations (latitude, longitude, user_id) VALUES (?, ?, ?)", coordinates['lat'], coordinates['lng'], session.get("user_id"))

                # query for coordinates so when pictures are implemented information can be used when photos are added w/ location
                spots = db.execute("SELECT id FROM locations WHERE latitude = ? AND longitude = ?", coordinates['lat'], coordinates['lng'])

                # for future photo purposes
                #db.execute("INSERT INTO photos (photo, location_id, user_id) VALUES (?, ?, ?)", request.files['photo'], spots[0]['id'], session.get("user_id"))
                #pic = db.execute("SELECT photo FROM photos WHERE location_id = ?", spots[0]['id'])

            return render_template("added.html", api_key=os.environ.get("API_KEY"), lat=coordinates['lat'], lng=coordinates['lng'])


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():

    if request.method == "GET":
        return render_template("search.html")
    else:
        # if nno address entered
        if not request.form.get("location"):
            alert = "Forgot location"
            return render_template("search.html", alert=alert)
        else:
            location = request.form.get("location")

        coordinates = get_coord(location)

        # if no coordinates are returned stay on page & tell user
        if coordinates == 'no results':
            alert = 'could not find location'
            return render_template("search.html", alert=alert)

        # if search returned multiple places stay on page & tell user
        elif coordinates == 'multiple results':
            alert = 'Enter a more specific location'
            return render_template("search.html", alert=alert)
        else:
            origin = f"{coordinates['lat']},{coordinates['lng']}"

            # query for closest 10 stairs as the crow flies
            stairs = db.execute("SELECT CAST(longitude AS real), CAST(latitude AS real), (((longitude - ?)*(longitude - ?)) + ((latitude - ?)*(latitude - ?))) AS proximity FROM locations ORDER BY proximity ASC LIMIT 10;", coordinates['lng'], coordinates['lng'], coordinates['lat'], coordinates['lat'])

        api_key = os.environ.get("API_KEY")

        # get coordinates and address lists to for rendered template
        staircases = []
        staircases_add = []
        p = 0
        for i in stairs:
            staircases.append([i['CAST(latitude AS real)'], i['CAST(longitude AS real)']])
            staircases_add.append(get_add(staircases[p]))
            p = p + 1

        return render_template("searched.html", api_key=api_key, lat=json.dumps(coordinates['lat']), lng=json.dumps(coordinates['lng']), stairs=json.dumps(staircases), address=staircases_add)
