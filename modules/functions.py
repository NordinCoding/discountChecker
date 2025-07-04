from modules.models import User, UserProduct, Product, db
from modules.helpers import log_to_file
from flask import jsonify
import requests
import time
import os



def store_product(dict_values, URL, user_id):
    '''
    Function to store the newly scraped product into both the products table 
    and the userProducts table
    
    Args:
        dictValues: Holds the data received from the scraper API
        URL: Holds the URL of the product that was scraped
        user_id: Holds the user_id of the current users session
    
    '''
    try: 
        # Create product object to store it in the products table
        product = Product(
            URL=URL,
            name=dict_values["name"],
            ogPrice=dict_values["ogPrice"],
            currentPrice=dict_values["currentPrice"]
        )
        db.session.add(product)
        db.session.commit()
        
        log_to_file(f"Product added to products table: {dict_values}", "INFO", user_id)
        
        # create a userProduct object using the user_id and the product_id to store it to the userProducts table
        log_to_file("Adding product to userProducts table", "INFO", user_id)
        
        userProduct = UserProduct(userID=user_id, productID=product.id)
        db.session.add(userProduct)
        db.session.commit()
        
        log_to_file(f"Product added to userProducts table: {product.name}", "INFO", user_id)
        
    except Exception as e:
        log_to_file(f"Error storing product in database: {e}", "ERROR", user_id)
        db.session.rollback()
        raise e
    
    
    
    
def validate_URL(URL):
    '''
    This function will validate URLs for the add_product route in app.py.
    
    '''
    
    valid_URLs = ["https://www.bol.com/nl/nl/p",
                  "https://www.bol.com/be/nl/p",
                  "https://www.bol.com/nl/fr/p",
                  "https://www.bol.com/be/fr/p"]
    
    for URL_check in valid_URLs:
        if URL_check in URL:
            return True
    return False




def check_product_existence(URL, product_id, user_id):
    '''
    Function that checks if the requested product that already exists in the products table
    also exists in the users userProducts table.
    
    '''
    userProduct = db.session.query(UserProduct).filter_by(productID=product_id, userID=user_id).first()
    if userProduct:
        # Returns True if product already exists in userProducts table
        log_to_file(f"Product already exists in userProducts table: {URL}", "INFO", user_id)
        return True
            
    # If product does exist in the Products table but not in the userProducts table
    # Add product to userProducts table without requesting the API to avoid duplicates
    else:
        userProduct = UserProduct(userID=user_id, productID=product_id)
        db.session.add(userProduct)
        db.session.commit()
        log_to_file(f"Product already in products table, added to userProducts table: {product_id}", "INFO", user_id)
        return False
    
    
    
'''

SCRAPER MODULES

'''

def rescrape_once(URL, product_id):
    log_to_file(f"Requesting rescrape of product: {product_id}")
    
    try:
        response = requests.get(f"{os.getenv('API_IP')}/scheduled_scrape/scrape?url={URL}")
        response.raise_for_status()
        dict_values = response.json()
        return dict_values
        
    except requests.exceptions.RequestException as e:
        log_to_file(f"Error while rescraping product, trying again: {e}", "ERROR")
        return {'error': e}



def retry_scrape(URL, product_id):
    
    # Request API in loop to retry the scrape twice
    for i in range (0, 2):
        
        if i == 0:
            log_to_file(f"1st retry on product: {product_id}")
        else:
            log_to_file(f"2nd retry on product: {product_id}")
        
        dict_values = rescrape_once(URL, product_id)
        
        # if dict_values contains the key 'currentPrice' it was successful,
        # return dict_values that contains product data
        if dict_values.get('currentPrice'):
            return dict_values
        
        # if loop is on second try and doesnt contain the key 'currentPrice',
        # the scraping failed twice, return dict_values that contains error message
        if i == 1:
            return dict_values
            
        time.sleep(2)