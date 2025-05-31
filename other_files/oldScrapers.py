from bs4 import BeautifulSoup
import requests
import time

def bol_scraper(URL):
    page = requests.get(URL)

    soup = BeautifulSoup(page.content, 'html.parser')

    spans = soup.find('span', class_="promo-price")
    # If no price is found
    if spans == None:
        # Look for div containing Text
        div = soup.find('div', class_="buy-block__title")
        # If no div is found return 1
        if div == None:
            return 1
        # Else return dictionary containing only the text. This most likely says "Niet Leverbaar".
        else:
            dictValues = {
                "name": div.text,
                "ogPrice": 0,
                "currentPrice": 0
            }
            return dictValues

    currentPrice = spans.text.replace("\n", '')
    # error maybe possibly in future
    currentPrice = currentPrice.replace('-','00').replace("\u2013","").replace("  ", '.')

    ogPrice = soup.find('del', class_="h-nowrap buy-block__list-price")
    if ogPrice != None:
        ogPrice = ogPrice.text
        ogPrice = ogPrice.replace(",", ".")
        ogPrice = ogPrice.replace('-','00').replace("\u2013","")
    else:
        ogPrice = currentPrice

    # Make sure theres no weird symbol in the price, if there is print the price
    try:
        savings = float(ogPrice) - float(currentPrice)
    except ValueError:
        print(ogPrice)
        print(currentPrice)
        return 0
    savings = round(savings, 2)
    savings = str(savings)

    dictValues = {
        "name": soup.title.text,
        "ogPrice": ogPrice,
        "currentPrice": currentPrice
    }
    return dictValues


# Works but amazon blocks scrapers so i need a PROXY which costs money
def amazon_scraper(URL):
    page = requests.get(URL)

    soup = BeautifulSoup(page.content, 'lxml')

    # Look for the current price
    spans = soup.find('span', class_="a-price-whole")
    if spans == None:
        # CHECK THIS
        print("Too many requests, try again later OR something is wrong")
        return 1

    currentPrice = spans.text.replace("\n", '')
    # error maybe possibly in future
    currentPrice = currentPrice.replace('-','00').replace("\u2013","").replace("  ", '.')

    # Look for original price
    ogPrice = soup.find('del', class_="a-offscreen")
    if ogPrice != None:
        ogPrice = ogPrice.text
        ogPrice = ogPrice.replace(",", ".")
        ogPrice = ogPrice.replace('-','00').replace("\u2013","")
    else:
        ogPrice = currentPrice

    # Make sure theres no weird symbol in the price, if there is print the price
    try:
        savings = float(ogPrice) - float(currentPrice)
    except ValueError:
        print(ogPrice)
        print(currentPrice)
        return 0
    savings = round(savings, 2)
    savings = str(savings)

    dictValues = {
        "name": soup.title.text,
        "ogPrice": 50,
        "currentPrice": currentPrice
    }
    return dictValues

