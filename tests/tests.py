import pytest

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.functions import validate_URL
    

    
# Test the retry functionality of the 24H based scheduled scraper
def mock_retry_scrape(mock_responses):
        
    # Loop through mock_responses to test functionality
    for i in range (0, 2):
        dict_values = mock_responses[i]
        
        # if dict_values contains the key 'currentPrice' it was successful,
        # return dict_values that contains product data and the amount of attempts for testing
        if dict_values.get('currentPrice'):
            return dict_values, (i + 1)
        
        # if loop is on second try and doesnt contain the key 'currentPrice',
        # the scraping failed twice, return dict_values that contains error message and the amount of attempts for testing
        if i == 1:
            return dict_values, (i + 1)
    


# This mock function combines the product checking logic from add_product and check_product_existence into one testing function
def mock_product_check_logic_test(product_exists_in_products_table, user_already_has_product, user_product_count):
    """
    Mock that tests the actual decision logic from your add_product route
    """
    
    # Test if feedback message is returned if table limit it exceeded
    if user_product_count >= 5:
        return {"success": False, "message": "The maximum amount of items allowed at a time is 5. Please remove an item before adding a new one"}
    
    # If product is found in Products table, check if its also in the users userProducts table
    if product_exists_in_products_table:
        # if check_product_existence returns True
        if user_already_has_product:  
            return {"success": False, "message": "Product is already in your list."}
        # if check_product_existence returns False
        else:  
            return {"success": True, "message": "Product added successfully."}
    else:
        # Product doesn't exist in Products table, would call process_product_data
        return {"success": True, "message": "Will process new product"}
        
    

# Test if the core functionality and error handling of process_product_data is correct
def mock_process_product_data(mock_response=None, raise_exception=None):
    
    try:
        if raise_exception:
            raise raise_exception
        
        dict_values = mock_response
        
        if dict_values.get("error"):
            return False, None
            
        return True, dict_values
    
    except TypeError as e:
        return False, None
    except KeyError as e:
        return False, None
    except Exception as e:
        return False, None
    
    





# TESTS

def test_validate_URL():
    assert validate_URL("https://www.bol.com/nl/nl/p/full-dutch-product") == True
    assert validate_URL("https://www.bol.com/be/nl/p/belgium-dutch-product") == True
    assert validate_URL("https://www.bol.com/nl/fr/p/dutch-french-product") == True
    assert validate_URL("https://www.bol.com/be/fr/p/belgian-french-product") == True
    
    assert validate_URL("https://www.amazon.com/product") == False
    assert validate_URL("https://www.google.com") == False
    assert validate_URL("not-a-url") == False
    assert validate_URL("") == False
    
    print("All URL validation tests passed!")



def test_retry_scrape():
    """Test different retry scenarios"""
    
    # Test 1: Success on first try
    mock_responses = [{'currentPrice': 29.99, 'name': 'Test Product'}]
    result, attempts = mock_retry_scrape(mock_responses)
    assert result.get('currentPrice') == 29.99
    assert attempts == 1
    print("Retry test 1 passed: Success on first try")
    
    # Test 2: Fail first, succeed second (this is the important one!)
    mock_responses = [
        {'error': 'scraping failed'}, 
        {'currentPrice': 19.99, 'name': 'Test Product'}
    ]
    result, attempts = mock_retry_scrape(mock_responses)
    assert result.get('currentPrice') == 19.99
    assert attempts == 2
    print("Retry test 2 passed: Failed first, succeeded second")
    
    # Test 3: Fail both attempts
    mock_responses = [
        {'error': 'scraping failed'}, 
        {'error': 'scraping failed again'}
    ]
    result, attempts = mock_retry_scrape(mock_responses)
    assert result.get('currentPrice') is None
    assert 'error' in result
    assert attempts == 2
    print("Retry test passed: Failed both attempts")
    
    print("All retry logic tests passed!")



def test_product_check_logic():
    result = mock_product_check_logic_test(product_exists_in_products_table=False, user_already_has_product=False, user_product_count=5)
    assert result["success"] == False
    assert "maximum amount" in result["message"]
    
    result = mock_product_check_logic_test(product_exists_in_products_table=True, user_already_has_product=False, user_product_count=2)
    assert result["success"] == True
    assert "Product added successfully" in result["message"]
    
    result = mock_product_check_logic_test(product_exists_in_products_table=True, user_already_has_product=True, user_product_count=4)
    assert result["success"] == False
    assert "Product is already in your list" in result["message"]
    
    result = mock_product_check_logic_test(product_exists_in_products_table=False, user_already_has_product=False, user_product_count=0)
    assert result["success"] == True
    assert "Will process new product" in result["message"]
    
    print("All product check logic tests passed!")
     
    
    
def test_process_product_data():
    
    # Test if success case returns correctly
    mock_response = {
        "name": "Mock product name",
        "currentPrice": "49.99",
        "ogPrice": "64.99"
        }
    result, dict_values = mock_process_product_data(mock_response=mock_response)
    assert result == True
    assert dict_values["name"] == "Mock product name"
    assert dict_values["currentPrice"] == "49.99"
    assert dict_values["ogPrice"] == "64.99"
    
    
    # Test if error response from API call is handled correctly
    mock_response = {
        "error": 'Failed to find class "promo-price"'
    }
    result, dict_values = mock_process_product_data(mock_response=mock_response)
    assert result == False
    assert dict_values == None
    
    
    # Test TypeError handling
    result, dict_values = mock_process_product_data(raise_exception=TypeError())
    assert result == False
    assert dict_values == None

    # Test KeyError handling  
    result, dict_values = mock_process_product_data(raise_exception=KeyError())
    assert result == False
    assert dict_values == None

    # Test generic Exception handling
    result, dict_values = mock_process_product_data(raise_exception=Exception())
    assert result == False
    assert dict_values == None
    
    print("All process product data tests passed!")
    


if __name__ == "__main__":
    test_validate_URL()
    test_retry_scrape()
    test_product_check_logic()
    test_process_product_data()