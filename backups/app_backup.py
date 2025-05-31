from flask import Flask, flash, redirect, render_template, request, session, jsonify, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from modules.models import User, UserProduct, Product, db
from flask_sqlalchemy import SQLAlchemy
from modules.helpers import login_required, log_to_file
from waitress import serve
from modules import create_app
from modules.functions import store_product, validate_URL, check_product_existence
from modules.tasks import add, request_bol_data
from modules.celery_utils import celery_init_app

'''

Flask back end application for the DiscountChecker web app.

This application is responsible for handling user authentication, database management, product data processing and scheduling API requests.
It uses Flask for the web framework, SQLAlchemy for database management, and APScheduler for scheduling tasks.
This application communicates with my scraper API running on a VPS to fetch product data from the desired webshops through URLs.
The application is designed to be run in a production environment using Waitress as the WSGI server, however
it is not meant for mass use, since I am not financially capable to support a large amount of users.
This program is purely a portfolio piece to show off what I have learned and what I am capable of.
Any feedback is very welcome since I am always looking to learn more and improve myself.

'''

# Create app using __init__.py
app = create_app()

# Initialize celery object
celery = celery_init_app(app)


log_to_file("App started", "INFO")


def process_product_data(URL):
    
    '''
    This function fetches the product data from the scraper API, 
    adds it to the products table and then to the userProducts table for current user.
    This function does not get called if the product is already in the dB since that is
    handeled in /add_product before this function gets called.
    
    I did this so that the database would not get bloated with the same data, but also to speed up the process
    of adding products to the userProducts table and to prevent unnecessary requests to the scraper API incase of an already existing product.
    This function is called from the /add_product route.
    
    '''
    
    try:
                  
        # Fetch the product data from the scraper API and store it in a dictionary, raise for HTTP errors
        log_to_file("Fetching product data with scraper API", "INFO", session["user_id"])
        
        # request_bol_data uses Celery to create a task queue to not overload the API
        task_result = request_bol_data.delay(URL)
        dictValues = task_result.get(timeout=15)
        if dictValues.get("error"):
            log_to_file(f"API request error: {dictValues["error"]}", "ERROR", session["user_id"])
            return False, None
            
        log_to_file(f"Product data fetched: {dictValues}", "INFO", session["user_id"])

        # Add the product to the Products table in the database
        log_to_file("Adding product to products table", "INFO", session["user_id"])

        store_product(dictValues, URL, session["user_id"])
            
        return True, dictValues
    
    except TypeError as e:
        log_to_file(f"error processing data: {e}", "ERROR", session["user_id"])
        return False, None
    except KeyError as e:
        log_to_file(f"KeyError while running function: {e}", "ERROR", session["user_id"])
        return False, None
    except Exception as e:
        log_to_file(f"error while running function: {e}", "ERROR", session["user_id"])
        return False, None


# Scheduler for refreshing prices every 24 hours. Check refresh.py for the function
'''
    def scheduled_job():
    with app.app_context():
        refresh_prices()


scheduler = BackgroundScheduler()
scheduler.add_job(
    refresh_prices,
    'interval',
    hours=24,
    id='refresh_prices',
    name='Refresh prices every 24 hours',
)


try:
    scheduler.start()
    log_to_file("Starting scheduler", "INFO")
except Exception as e:
    log_to_file(f"Error starting scheduler: {e}", "ERROR")
    scheduler.shutdown()
    log_to_file("Scheduler stopped", "ERROR")
'''  


@app.route('/', methods=["GET", "POST"])
@login_required
def index():

    log_to_file(f"Loading index", "INFO", session["user_id"])
    # Uncomment to test Celery worker
    #task = add.delay(5, 5)
    #print(task)
    
    # Get all the product IDs of the products from the users userProducts table to get the product data from the products table
    userProductsRaw = db.session.query(UserProduct).filter_by(userID=session["user_id"]).all()
    products = []
    
    # using userProductsRaw, Get the users product objects from the products table to push it to the front end
    for userProductRaw in userProductsRaw:
        product = db.session.query(Product).filter_by(id=userProductRaw.productID).first()
        products.append(product)
        
    return render_template("index.html", products=products)


@app.route('/register', methods=["GET", "POST"])
def register():
    
    session.clear()
    log_to_file("Loading register page", "INFO")
    
    # Registers the user in the database and encrypt password,
    # checking if user already exists is done with JS in "register.html" and the check_username() function
    # authentication is done with JS in "register.html"
    if request.method == "POST":
        name = request.form.get("username")
        passwordHash = generate_password_hash(request.form.get("password"), method='pbkdf2', salt_length=16)
        user = User(username=name, passwordHash=passwordHash)
        
        db.session.add(user)
        db.session.commit()
        
        log_to_file(f"User registered succesfully: {name}", "INFO")
        return redirect(url_for("login"))
    return render_template("register.html")


# This route is used by register.html
@app.route('/check_username', methods=["GET", "POST"])
def check_username():
    
    # Check if the username that the user is trying to register with already exists in the users table
    data = request.get_json()
    username = data.get("username")
    user = db.session.query(User).filter_by(username=username).first()
    if user:
        log_to_file(f"Username already exists: {username}", "DEBUG")
        return jsonify({"exists": True})
    else:
        log_to_file(f"Username does not exist: {username}", "DEBUG")
        return jsonify({"exists": False})


@app.route('/login', methods=["GET", "POST"])
def login():
    
    session.clear()
    
    log_to_file("Loading login page", "INFO")
    
    if request.method == "POST":
        data = request.get_json()
        username = data.get("username")
        user = db.session.query(User).filter_by(username=username).first()
        
        # Check if user exists and if the password is correct
        # Password comes directly from the form, as to never store it in a variable
        if user is None or not check_password_hash(user.passwordHash, data.get("password")):
            return jsonify({"success":False, "message":"Invalid username or password"})
        else:
            session["user_id"] = user.id
            log_to_file(f"User logged in: {username}", "INFO", session["user_id"])
            return jsonify({"success":True, "redirect": "/"})
    
    return render_template("login.html")


@app.route('/logout', methods=["GET", "POST"])
def logout():
    # Clear all session data and redirect to login page
    log_to_file("Logging out user", "INFO", session["user_id"])
    
    session.clear()
    return redirect(url_for("login"))



# Im pretty sure you can remove all of this, double check first tho
# Make this happen every 24 or 12 hours for production mode, also remove refresh button
'''
@app.route('/api/refresh_prices', methods=["GET", "POST"])
@login_required
def refresh_prices():
    products = db.session.query(Product).all()
    productDicts = []
    
    # Loop through all the products in the database and update the prices
    for product in products:
        dictValues = bol_scraper(product.URL)
        product.currentPrice = dictValues["currentPrice"]
        product.ogPrice = dictValues["ogPrice"]
        db.session.commit()
    
    # Get all the updated products and return them as a JSON object for the script
    updated_products = db.session.query(Product).all()
    for updated_product in updated_products:
        productDict = {"id": updated_product.id, 
                       "name": "updated_product.name", 
                       "ogPrice": updated_product.ogPrice, 
                       "currentPrice": updated_product.currentPrice}
        productDicts += [productDict]
        
    return jsonify(productDicts)

'''


@app.route('/add_product', methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        URL = request.form.get("URL")
        
        if not validate_URL(URL):
            log_to_file(f"Invalid URL: {URL}", "ERROR", session["user_id"])
            return jsonify({"success": False, "message": "Invalid URL, please enter a valid bol.com Product URL."})
        
        # Check if the requested product is already in the users table
        # If it is, alert the user and dont add it again
        product = db.session.query(Product).filter_by(URL=URL).first()
        if product:
            if check_product_existence(URL, product.id, session["user_id"]):
                return jsonify({"success": False, "message": "Product is already in your list."})
            
            # Otherwise, add product to userProducts table without requesting the API to avoid duplicates
            else:
                return jsonify({"success": True, "message": "Product added successfully.", "product_data": {"URL": URL,
                                                                                                            "id": product.id,
                                                                                                            "name": product.name,
                                                                                                            "currentPrice": product.currentPrice,
                                                                                                            "ogPrice": product.ogPrice}})
        
        # if the product does not exist in either tables, call process_propduct_data()
        result, product_data = process_product_data(URL)
        
        # if it fails, pass the user a failure message
        if result == False:
            log_to_file(f"Error processing product data: {URL}", "ERROR", session["user_id"])
            return jsonify({"success": False, "message": "Error processing product data."})
        
        # if it succeeds, pass the user success message and send the product data to the script in "index.html"
        product_data["URL"] = URL
        log_to_file(f"Product added succesfully", "INFO", session["user_id"])
        return jsonify({"success": True, "message": "Product added successfully.", "product_data": product_data})
            
    return redirect(url_for("index"))


# Remove row from the database when user clicks 'remove' button
@app.route('/remove_row', methods=["GET", "POST"])
def remove_row():
    if request.method == "POST":
        
        # get Product data from the JSON object sent from "index.html"
        rowData = request.get_json()
        log_to_file(f"Removing requested product: {rowData} from userProducts table", "INFO", session["user_id"])
        
        # Look for the product in the database and remove it from the userProducts table using the data from the JSON object
        try:
            print(rowData["name"])
            productData = db.session.query(Product).filter_by(name=rowData["name"]).first()
            print(productData.id)
            db.session.query(UserProduct).filter_by(productID=productData.id, userID=session['user_id']).delete()
            db.session.commit()
            
        except Exception as e:
            log_to_file(f"Error removing product: {rowData["name"]} from userProducts table: {e}", "ERROR", session["user_id"])
            return redirect(url_for("index"))
        
        log_to_file(f"Product removed from userProducts table: {productData}", "INFO", session["user_id"])
        
        return redirect(url_for("index"))
    return redirect(url_for("index"))


mode = "dev"


if __name__ == '__main__':
    if mode == "dev":
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=True)
    else:
        serve(app, host='0.0.0.0', port=5000, threads=2,
              url_prefix="/DiscountChecker")