from flask import Flask, flash, redirect, render_template, request, session, jsonify, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from modules.models import User, UserProduct, Product, db
from flask_sqlalchemy import SQLAlchemy
from modules.helpers import login_required, log_to_file
from waitress import serve
from modules import create_app
from modules.functions import store_product, validate_URL, check_product_existence, remove_trailing_data
from modules.tasks import add, request_bol_data, scheduled_rescrape
from modules.celery_utils import celery_init_app
import os

'''

Flask back end application for the DiscountChecker web app.

This application is responsible for handling user authentication, database management, product data processing and scheduling API requests.
It uses Flask for the web framework, SQLAlchemy for database management and redis + Celery beat for scheduling tasks and rate limiting API requests.
This application communicates with my scraper APIs running on a VPS to fetch product data from the desired webshops through URLs.
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

# Set base URL for redirects, the URL is different in production.
BASE_URL = os.getenv("BASE_URL", "")

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
        task_result = request_bol_data.apply_async(args=[URL], queue='user_requests')
        dict_values = task_result.get(timeout=30)
        if dict_values.get("error"):
            log_to_file(f"API request error: {dict_values}", "ERROR", session["user_id"])
            return False, None
            
        log_to_file(f"Product data fetched: {dict_values}", "INFO", session["user_id"])

        # Add the product to the Products table in the database
        log_to_file("Adding product to products table", "INFO", session["user_id"])

        store_product(dict_values, URL, session["user_id"])
            
        return True, dict_values
    
    except TypeError as e:
        log_to_file(f"error processing data: {e}", "ERROR", session["user_id"])
        return False, None
    except KeyError as e:
        log_to_file(f"KeyError while running function: {e}", "ERROR", session["user_id"])
        return False, None
    except Exception as e:
        log_to_file(f"error while running function: {e}", "ERROR", session["user_id"])
        return False, None



@app.route('/', methods=["GET", "POST"])
@login_required
def index():

    log_to_file(f"Loading index", "INFO", session["user_id"])
    # Uncomment to test Celery worker
    #task = add.delay(5, 5)
    #print(task)
    
    # Get all the product IDs of the products from the users userProducts table to get the product data from the products table
    userProducts = db.session.query(UserProduct).filter_by(userID=session["user_id"]).all()
    products = []
    
    # using userProducts, Get the users product objects from the products table to push it to the front end
    for userProduct in userProducts:
        product = db.session.query(Product).filter_by(id=userProduct.productID).first()
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
        return redirect(f"{BASE_URL}/login")
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
            return jsonify({"success":False, "message":"Invalid username and/or password"})
        else:
            session["user_id"] = user.id
            log_to_file(f"User logged in: {username}", "INFO", session["user_id"])
            return jsonify({"success":True, "redirect": f"{BASE_URL}/"})
    
    return render_template("login.html")


@app.route('/logout', methods=["GET", "POST"])
def logout():
    # Clear all session data and redirect to login page
    log_to_file("Logging out user", "INFO", session["user_id"])
    
    session.clear()
    return redirect(f"{BASE_URL}/login")



@app.route('/add_product', methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        URL = request.form.get("URL")
        
        # Check count of amount of / in URL, if count exceeds 7, this means the URL has trailing data that changes often, not needed to look up the product
        # In this case remove the trailing data. Otherwise do nothing with the URL since its already formatted correctly
        log_to_file(f"Removing trailing data if it exists from: {URL}")
        new_URL = remove_trailing_data(URL)
        log_to_file(f"New URL: {new_URL}")
        
        if not validate_URL(new_URL):
            log_to_file(f"Invalid URL: {new_URL}", "ERROR", session["user_id"])
            return jsonify({"success": False, "message": "Invalid URL, please enter a valid Product URL."})
        
        # Check of user has 5 products in table, if so alert user that the maximum amount is 5
        query_result = db.session.query(UserProduct).filter_by(userID=session["user_id"]).all()
        if len(query_result) >= 5:
            return jsonify({"success": False, "message": "The maximum amount of items allowed at a time is 5. Please remove an item before adding a new one"})
        
        # Check if the requested product is already in the Products table
        # If it is, alert the user and dont add it again
        product = db.session.query(Product).filter_by(URL=new_URL).first()
        if product:
            if check_product_existence(new_URL, product.id, session["user_id"]):
                return jsonify({"success": False, "message": "Product is already in your list."})
            
            # Otherwise, add product to userProducts table without requesting the API to avoid duplicates
            else:
                return jsonify({"success": True, "message": "Product added successfully.", "product_data": {"URL": new_URL,
                                                                                                            "id": product.id,
                                                                                                            "name": product.name,
                                                                                                            "currentPrice": product.currentPrice,
                                                                                                            "ogPrice": product.ogPrice}})
        
        # if the product does not exist in either tables, call process_propduct_data()
        result, product_data = process_product_data(new_URL)
        
        # if it fails, pass the user a failure message
        if result == False:
            log_to_file(f"Error processing product data: {URL}", "ERROR", session["user_id"])
            return jsonify({"success": False, 
                            "message": "Error processing product data, please check if the URL you entered is an available product"})
        
        # if it succeeds, pass the user success message and send the product data to the script in "index.html"
        product_data["URL"] = new_URL
        log_to_file(f"Product added succesfully", "INFO", session["user_id"])
        return jsonify({"success": True, "message": "Product added successfully.", "product_data": product_data})
            
    return redirect(f"{BASE_URL}/")


# Remove row from the database when user clicks 'remove' button
@app.route('/remove_row', methods=["GET", "POST"])
def remove_row():
    if request.method == "POST":
        
        # get Product data from the JSON object sent from "index.html"
        row_data = request.get_json()
        log_to_file(f"Removing requested product: {row_data} from userProducts table", "INFO", session["user_id"])
        
        # Look for the product in the database and remove it from the userProducts table using the data from the JSON object
        try:
            product_data = db.session.query(Product).filter_by(name=row_data["name"]).first()
            print(product_data.id)
            db.session.query(UserProduct).filter_by(productID=product_data.id, userID=session['user_id']).delete()
            db.session.commit()
            
        except Exception as e:
            log_to_file(f"Error removing product: {row_data["name"]} from userProducts table: {e}", "ERROR", session["user_id"])
            return redirect(f"{BASE_URL}/")
        
        log_to_file(f"Product removed from userProducts table: {product_data}", "INFO", session["user_id"])
        
        return redirect(f"{BASE_URL}/")
    return redirect(f"{BASE_URL}/")


# Route used to test the 24H based scheduled rescrape of the Products table
@app.route('/test_scheduler', methods=["GET", "POST"])
def test_scheduler():
    scheduled_rescrape()
    return redirect(f"{BASE_URL}/")


mode = "dev"


if __name__ == '__main__':
    if mode == "dev":
        app.run(host='0.0.0.0', port=80, debug=True, use_reloader=True)
    else:
        serve(app, host='0.0.0.0', port=80, threads=2,
              url_prefix="/DiscountChecker")