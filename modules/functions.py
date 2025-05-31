from modules.models import User, UserProduct, Product, db
from modules.helpers import log_to_file
from flask import jsonify


def store_product(dictValues, URL, user_id):
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
            name=dictValues["name"],
            ogPrice=dictValues["ogPrice"],
            currentPrice=dictValues["currentPrice"]
        )
        db.session.add(product)
        db.session.commit()
        
        log_to_file(f"Product added to products table: {dictValues}", "INFO", user_id)
        
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
            
    # If product does exist in the products table but not in userProducts
    # Add product to userProducts table without requesting the API to avoid duplicates
    else:
        userProduct = UserProduct(userID=user_id, productID=product_id)
        db.session.add(userProduct)
        db.session.commit()
        log_to_file(f"Product already in products table, added to userProducts table: {product_id}", "INFO", user_id)
        return False