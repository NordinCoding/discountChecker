from celery import shared_task
from sqlalchemy import select, ScalarResult
from modules.models import User, UserProduct, Product, db
from flask import jsonify, session
from modules.helpers import log_to_file
from modules.functions import rescrape_once, retry_scrape
import re
import requests
import time
import os

# Task to test out concurrency
@shared_task
def add(x, y):
    
    for i in range (0, 10):
        print(i)
        time.sleep(1)
    return x + y  


@shared_task
def request_API(URL):
    '''
    
    This task is purely reserved for requesting the API, it has a concurrency of 1
    So no matter the amount of requests, my API will only handle 1 at a time.
    If i increase the resources on my VPS i will increase the concurrency.
    
    '''
    try:
        response = requests.get(f"{os.getenv('API_IP')}/user_scrape/scrape?url={URL}")
        response.raise_for_status()
        dictValues = response.json()
        return dictValues
    
    except requests.exceptions.RequestException as e:
        return None


@shared_task(name="scheduled_rescrape")
def scheduled_rescrape():
    
    log_to_file("Starting Weekly Products rescrape")
    
    products = db.session.query(Product).all()
    for product in products:
        # Request API per product and catch errors
        dict_values = rescrape_once(product.URL, product.id)
        
        if dict_values.get('error'):
            log_to_file(f"Requested rescrape failed, retrying: {dict_values}", "ERROR")
            
            # Store retry response in variable, check if variable contains an error message
            # If so, skip product. If not, store response in dict_values and continue the task
            retry_response = retry_scrape(product.URL, product.id)
            
            if retry_response.get('currentPrice'):
                dict_values = retry_response
            else:
                log_to_file(f"Product cant be scraped successfully, skipping product: {product.id}", "ERROR")
                continue
        
        log_to_file(f"Requested product succesfully rescraped: {dict_values}")
        
        #Convert dictValues from string to float to allow comparison
        new_current_price = float(dict_values["currentPrice"])
        new_og_price = float(dict_values["ogPrice"])
        
        # if either currentPrice or ogPrice has changed, update the product in the dB with the new data
        if product.currentPrice != new_current_price or product.ogPrice != new_og_price:
            log_to_file("Updating product data")
            
            product.currentPrice = new_current_price
            product.ogPrice = new_og_price
            db.session.commit()
            
            log_to_file("Successfully updated product data")
            
        # Sleep for 2 seconds to not overload the API
        time.sleep(2)
        

@shared_task(name="scheduled_user_rescrape")
def scheduled_user_rescrape():
    
    log_to_file("Starting Daily UserProducts rescrape")
    
    userProducts_id = db.session.query(UserProduct.productID).all()
    
    for id in userProducts_id:
        # Extract and clean up the product IDs from the UserProducts table
        id = re.sub("[^0-9]", "", str(id[0]))
        product = db.session.query(Product).filter_by(id=id).first()
        
        #Request rescrape with cleaned up product ID
        dict_values = rescrape_once(product.URL, product.id)
        if dict_values.get('error'):
            log_to_file(f"Requested rescrape failed, retrying: {dict_values}", "ERROR")
            
            # Store retry response in variable, check if variable contains an error message
            # If so, skip product. If not, store response in dict_values and continue the task
            retry_response = retry_scrape(product.URL, product.id)
            
            if retry_response.get('currentPrice'):
                dict_values = retry_response
            else:
                log_to_file(f"Product cant be scraped successfully, skipping product: {product.id}", "ERROR")
                continue
            
        log_to_file(f"Requested product succesfully rescraped: {dict_values}")
        
        #Convert dictValues from string to float to allow comparison
        new_current_price = float(dict_values["currentPrice"])
        new_og_price = float(dict_values["ogPrice"])
        
        # if either currentPrice or ogPrice has changed, update the product in the dB with the new data
        if product.currentPrice != new_current_price or product.ogPrice != new_og_price:
            log_to_file("Updating product data")
            
            product.currentPrice = new_current_price
            product.ogPrice = new_og_price
            db.session.commit()
            
            log_to_file("Successfully updated product data")
            
        # Sleep for 2 seconds to not overload the API
        time.sleep(2)