from bs4 import BeautifulSoup
import requests
import time

def bol_scraper():
    print("start test")
    URL = "https://www.bol.com/nl/nl/p/sony-wh-1000xm4-draadloze-over-ear-koptelefoon-met-noise-cancelling-zwart/9300000006173040/?bltgh=48453174-5a44-4173-ae61-ff0bb64f61a8.topDealsForYou.product-tile-9300000006173040.ProductImage&promo=main_860_deals_for_you___product_4_9300000006173040"
    
    page = requests.get(URL)

    soup = BeautifulSoup(page.content, 'html.parser')
    print(soup)

    spans = soup.find('span', class_="promo-price")
    # If no price is found
    if spans == None:
        print("no price found")
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
            print("test1")
            print(dictValues)

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
        print("test2")
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
    print(dictValues)
    
bol_scraper()