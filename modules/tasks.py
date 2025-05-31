from celery import shared_task
from modules.models import User, UserProduct, Product, db
from flask import jsonify, session
from modules.helpers import log_to_file
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
    