import pymongo, os
from flask import Flask, flash, redirect, render_template, request, url_for, session, jsonify
from datetime import datetime
import numpy as np
from sklearn.linear_model import LinearRegression

############################################################################

app = Flask(__name__)
app.config["SECRET_KEY"] = "who am i"
database_name = "bustrackerapp"  # make sure another db in same name doesn't exist, change this name to your custom one
############################################################################

# load env variables, "mongo uri" is in env
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception as err:
    print(err)

# fetching mongo connection string
try:
    mongo_uri = os.environ.get("mongo_connection_string")
    print("MongoDB connection string fetched from env = ", mongo_uri)
except:
    # loading default connection string
    mongo_uri = "mongodb://localhost:27017"
    print("MongoDB connection string default, localhost db = ", mongo_uri)

myclient = pymongo.MongoClient(mongo_uri)
dblist = myclient.list_database_names()

if database_name in dblist:
    print(f"The '{database_name}' database exists")
else:
    mydb = myclient[database_name]

    logincol = mydb["logininfo"]
    logindata = {
        "bus_number": 1,
        "student_id": 1234567,
        "name": "vasanth",
        "college_mail_id": "vasa@vec",
        "password": "vasa",
        "role": "Passenger",
    }
    logincol.insert_one(logindata)

    routecol = mydb["routes"]
    routesdata = [
        {
            "route": 1,
            "stops": [[13.150691, 80.191386,"Main Street", "10:30 AM", "5 mins"], [13.086973, 80.198556, "2nd Avenue", "10:40 AM", "7 mins"], [13.070050 , 80.204622],[13.064789,80.211225],[13.0499770, 80.2119263],[13.034884 , 80.212141],[13.0294610, 80.2087680],[13.019450954211383, 80.20632620850493],[13.007810350875493, 80.20360120850467],[12.996983,80.190630],[12.978001,80.181632],[12.987453,80.175985],[12.968753,80.149757],[12.951582,80.140173],[12.936907,80.127587 ]],
        },
        {
            "route": 2,
            "stops": [[13.15032506953065, 80.19147914344043], [13.09585903472055, 80.22202094048951], [13.085928892300894, 80.22404919501291],[13.08485664414506, 80.21859361165367],[13.075493606110536, 80.21840817911998],[13.070393183392007, 80.22719697272477],[13.066691265503707, 80.23206884418678],[13.04212491032381, 80.23474128281728],[13.030117239107405, 80.23131724843451],[13.02144863856292, 80.2212003655121],[12.994539329872936, 80.21726541220235],[12.97632499772321, 80.2215077926113],[12.964976318333006, 80.20587360400336],[12.945686185811388, 80.15506982613861],[12.943727712259752, 80.1837119306911]],
        },
        {
            "route": 3,
            "stops": [
                [13.150630, 80.191372],
                [13.103062, 80.198937],
                [13.103428, 80.201695],
                [13.103203, 80.207560],
                [13.100191, 80.215610],
                [13.099750, 80.229786],
                [13.097660, 80.240446],
                [13.094202, 80.241161],
                [13.085790, 80.248089],
                [13.085747, 80.250342],
                [13.073257, 80.260745],
                [13.066129, 80.267898],
                [13.065797, 80.273791],
                [13.058738, 80.274166],
                [13.052879, 80.273537],
            ],
        },
        {
            "route": 4,
            "stops": [
                [13.15061238447854, 80.19138723228298],
                [13.085345537958435, 80.19847651410682],
                [13.057563430233515, 80.19424843357973],
                [13.052772292524377, 80.19207184836598],
                [13.04400463769775, 80.19769042561637],
                [13.04180020965743, 80.19390350561187],
                [13.037277941124094, 80.1960218138087],
                [13.04567283844882, 80.18695395860433],
                [13.042329374498916, 80.18055817497364],
                [13.04098732959311, 80.17281978053377],
                [13.034680571705527, 80.15639926949234],
                [13.037650826065008, 80.13683161714332],
                [13.040731310500066, 80.12859898605494],
                [13.045032144902105, 80.11573468323134],
                [13.046743421507971, 80.11106646423087],
            ],
        },
    ]
    routecol.insert_many(routesdata)

    issuecol = mydb["issues"]
    issuedata = {"frombus": 2, "issue": "hi i am facing breakdown at kk nagar","name":"vasanth"}
    issuecol.insert_one(issuedata)

    annoucementscol = mydb["announcements"]
    anndata = {"Message": "Bus 4 will leave in 5 mins"}
    annoucementscol.insert_one(anndata)

    locationcol = mydb["buslocation"]
    locdata = [
        {
            "route": 1,
            "location": [13.150500910874094, 80.19221141449697],
        },
        {
            "route": 3,
            "location": [13.150500910874094, 80.19221141449697],
        },
        {
            "route": 4,
            "location": [13.150500910874094, 80.19221141449697],
        },
        {
            "route": 2,
            "location": [13.150500910874094, 80.19221141449697],
        },
    ]
    locationcol.insert_many(locdata)

    print(f"Database named {database_name} has been created in localhost")


#############################################################################
@app.route("/")
def splash():
    return render_template("splash.html")

@app.route("/login", methods=["POST", "GET"])
def home():
    if request.method == "GET":
        return render_template("index.html")
    else:
        # post request i.e. login form was submitted
        college_mail_id = request.form.get("signin-email")
        password = request.form.get("signin-pswd")

        # checking if admin
        if college_mail_id == "vasa@vec" and password == "vasa":
            session["admin"] = True
            return redirect(url_for("admin"))
        else:
            client = pymongo.MongoClient(mongo_uri)[database_name]["logininfo"]

            # auth contains the collection that matches the mail id submitted in form
            auth = client.find_one({"college_mail_id": college_mail_id})

            # checking if password matches the db
            if auth != None:  # making sure collection is not None
                pbool = auth["password"] == password

            if auth == None:
                flash("imail", category="error")  # invalid mail
            elif pbool == False:
                flash("ipass", category="error")  # invalid password
            else:
                # login success
                session["userbusno"] = auth["bus_number"]
                session["username"] = auth["name"]
                print("Session Cookie = ", session)

                return redirect(url_for("homepage"))

        # rendering the same page (login page) if auth fails
        return render_template("index.html")


@app.route("/admin")
def admin():
    if "admin" in session:
        return render_template("adminhome.html")
    else:
        return redirect(url_for("home"))


@app.route("/adminann", methods=["POST", "GET"])
def adminann():
    if "admin" in session:
        if request.method == "GET":
            client = pymongo.MongoClient(mongo_uri)[database_name]["announcements"]
            str = []

            for i in client.find({}, {"_id": 0, "Message": 1}):
                str.append(i["Message"])

            return render_template("adminannounce.html", message=str)
        else:
            # posting issues
            issue = request.form.get("message")

            if len(issue) < 5:
                flash(
                    "Message too short to be posted. Please be more elaborate!",
                    category="error",
                )
            else:
                # success
                flash(
                    "Your announcement has been made successfully. All the users can see your announcement",
                    category="success",
                )

                # inserting announcements to mongoDB
                client = pymongo.MongoClient(mongo_uri)[database_name]["announcements"]
                data = {"Message": issue}
                client.insert_one(data)

            client = pymongo.MongoClient(mongo_uri)[database_name]["announcements"]
            str = []

            for i in client.find({}, {"_id": 0, "Message": 1}):
                str.append(i["Message"])

            return render_template("adminannounce.html", message=str)
    else:
        return redirect(url_for("home"))


@app.route("/adminissues")
def adminissues():
    if "admin" in session:
        client = pymongo.MongoClient(mongo_uri)[database_name]["issues"]
        data = []

        for i in client.find({}, {"_id": 0}):
            # Update the message format to include name
            iss = f"{i['name']} from Bus {i['frombus']} reported: \"{i['issue']}\""
            data.append(iss)

        return render_template("adminissues.html", message=data)
    else:
        return redirect(url_for("home"))

# make this accessible from admin login alone
@app.route("/signup", methods=["POST", "GET"])
def signup():
    if "admin" in session:
        if request.method == "GET":
            return render_template("create_acc.html")
        else:
            # getting posted form data
            name = request.form.get("name")
            email = request.form.get("email")
            password = request.form.get("pswd")
            re_password = request.form.get("confpswd")
            account_type = request.form.get("account")
            routeno = request.form.get("busroute")

            data = {
                "bus_number": int(routeno),
                "name": name,
                "college_mail_id": email,
                "password": password,
                "role": account_type,
            }

            client = pymongo.MongoClient(mongo_uri)[database_name]["logininfo"]

            # checking if mail id exists already
            auth = client.find_one({"college_mail_id": email})
            if auth != None:
                flash("The email id is already registered", category="error")
            elif len(name) < 2:
                flash("Name too short", category="error")
            elif "@vec" not in email:
                flash(
                    "Invalid mail id, mail id must belong to vec domain",
                    category="error",
                )
            elif len(password) < 4:
                flash("Password too short", category="error")
            elif password != re_password:
                flash("Passwords don't match", category="error")
            else:
                client.insert_one(data)
                flash("Registered Successfully", category="success")

            return render_template("create_acc.html")
    else:
        return redirect(url_for("home"))


@app.route("/homepage")
def homepage():
    if "userbusno" in session:
        # Load the API key from the .env
        google_maps_api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
        # Pass the API key to the HTML template
        return render_template("homepage.html", google_maps_api_key=google_maps_api_key)
    else:
        # Redirect to login page if not logged in
        return redirect(url_for("home"))


@app.route("/updates")
def updates():
    # if userbusno != 0:
    if "userbusno" in session:
        client = pymongo.MongoClient(mongo_uri)[database_name]["announcements"]
        str = []

        for i in client.find({}, {"_id": 0, "Message": 1}):
            str.append(i["Message"])

        return render_template("recentUpdate.html", message=str)
    else:
        # re directing to login page (function name of login page is home, not to be confused)
        return redirect(url_for("home"))


@app.route("/report", methods=["POST", "GET"])
def report():
    if request.method == "GET":
        # if userbusno != 0:
        if "userbusno" in session:
            return render_template("report.html")
        else:
            return redirect(url_for("home"))
    else:
        # posting issues
        issue = request.form.get("issue")

        if len(issue) < 5:
            flash(
                "Issue too short to be posted. Please be more elaborate!",
                category="error",
            )
        else:
            # success
            flash(
                "Your issue has been successfully submitted to admin",
                category="success",
            )

            # inserting issue to mongoDB
            client = pymongo.MongoClient(mongo_uri)[database_name]["issues"]
            data = {"frombus": session["userbusno"], "issue": issue,"name": session["username"]  }
            client.insert_one(data)

        return render_template("report.html")


@app.route("/logout")
def logout():
    if "userbusno" in session:
        session.pop("userbusno", None)
    if "admin" in session:
        session.pop("admin", None)

    return redirect(url_for("splash"))


# route to get live locations for all buses



# route to get stoppings data of all buses
@app.route("/stoppings")
def stoppings():
    client = pymongo.MongoClient(mongo_uri)[database_name]["routes"]

    data = {}

    for document in client.find({}, {"_id": 0}):
        data[document["route"]] = document["stops"]

    return data


# route to get bus number of current logged in user
from flask import jsonify

@app.route("/busno")
def busno():
    if "userbusno" in session:
        return str(session["userbusno"])  # Convert session data to string
    else:
        return jsonify({"error": "Bus number not found"}), 404  # Return a valid JSON response


# post requrest will be sent here to update the location to DB



@app.route("/emergency", methods=["POST"])
def emergency():
    if "userbusno" in session:
        client = pymongo.MongoClient(mongo_uri)[database_name]["issues"]
        emergency_data = {
            "frombus": session["userbusno"],
            "issue": "Emergency Alert!",
            "name": session.get("username", "Anonymous")  # Added name field
        }
        client.insert_one(emergency_data)
        return jsonify({"status": "success", "message": "Emergency alert sent!"})
    else:
        return jsonify({"status": "error", "message": "User not authenticated!"}), 403


  

@app.route('/sharelocation', methods=['POST'])
def share_location():
    data = request.json
    bus_id = data.get("bus_id")
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    timestamp = datetime.datetime.utcnow()
    
    if not bus_id or latitude is None or longitude is None:
        return jsonify({"error": "Missing data"}), 400
    
    pymongo.MongoClient(mongo_uri)[database_name]["locations"].insert_one({
        "bus_id": bus_id,
        "latitude": latitude,
        "longitude": longitude,
        "timestamp": timestamp
    })
    return jsonify({"message": "Location updated"})



@app.route('/update-location', methods=['POST'])
def update_location():
    if request.method == 'POST':
        try:
            data = request.get_json()
            bus_no = int(data['busNo'])
            lat = float(data['lat'])
            lng = float(data['lng'])
            
            # Update location in MongoDB
            location_col = myclient[database_name]["buslocation"]
            location_col.update_one(
                {"route": bus_no},
                {"$set": {"location": [lat, lng]}},
                upsert=True
            )
            
            return jsonify({"status": "success"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 400

@app.route('/get-location/<int:bus_no>')
def get_location(bus_no):
    try:
        location_col = myclient[database_name]["buslocation"]
        location_data = location_col.find_one(
            {"route": bus_no},
            {"_id": 0, "location": 1}
        )
        
        if location_data:
            return jsonify({
                "lat": location_data["location"][0],
                "lng": location_data["location"][1]
            })
        return jsonify({"error": "Location not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Modify your existing location route to use the new structure
@app.route("/location")
def location():
    client = myclient[database_name]["buslocation"]
    data = {}
    
    for document in client.find({}, {"_id": 0}):
        data[document["route"]] = document["location"]
    
    return jsonify(data)



if __name__ == "__main__":
    app.run(debug=True)
