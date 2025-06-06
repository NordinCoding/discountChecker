from celery import shared_task
from modules.models import User, UserProduct, Product, db
from flask import jsonify, session
from modules.helpers import log_to_file
from modules.functions import rescrape_once, retry_scrape
import requests
import time

# Task to test out concurrency
@shared_task
def add(x, y):
    
    for i in range (0, 10):
        print(i)
        time.sleep(1)
    return x + y  


@shared_task
def request_bol_data(URL):
    '''
    
    This task is purely reserved for requesting the API, it has a concurrency of 1
    So no matter the amount of requests, my API will only handle 1 at a time.
    If i increase the resources on my VPS i will increase the concurrency.
    
    '''
    try:
        print("requesting data")
        response = requests.get(f"http://136.144.172.186/scrape?url={URL}")
        response.raise_for_status()
        dictValues = response.json()
        return dictValues
    
    except requests.exceptions.RequestException as e:
        return None
    
    

@shared_task(name="scheduler_test")
def scheduler_test():
    for i in range(0, 5):
        time.sleep(1)
        


@shared_task(name="scheduled_rescrape")
def scheduled_rescrape():
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