import time
import json
import csv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth
from bs4 import BeautifulSoup
from curl_cffi import requests
from datetime import datetime


def init_webdriver():
    # hrome_options = Options()
    # chrome_options.add_argument("--headless")
    driver = webdriver.Chrome()
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True)
    driver.maximize_window()
    return driver


def scrolldown(driver, deep):
    for _ in range(deep):
        driver.execute_script('window.scrollBy(0, 500)')
        time.sleep(0.1)


def get_product_info(product_url):
    session = requests.Session()

    raw_data = session.get("https://www.ozon.ru/api/composer-api.bx/page/json/v2?url=" + product_url)
    json_data = json.loads(raw_data.content.decode())

    full_name = json_data["seo"]["title"]

    if json_data["layout"][0]["component"] == "userAdultModal":
        product_id = str(full_name.split()[-1])[1:-1]
        return (product_id, full_name, "Товары для взрослых", None)
    else:
        # description = json.loads(json_data["seo"]["script"][0]["innerHTML"])["description"]
        image_url = json.loads(json_data["seo"]["script"][0]["innerHTML"])["image"]
        price = json.loads(json_data["seo"]["script"][0]["innerHTML"])["offers"]["price"] + " " + \
                json.loads(json_data["seo"]["script"][0]["innerHTML"])["offers"]["priceCurrency"]
        product_id = json.loads(json_data["seo"]["script"][0]["innerHTML"])["sku"]

        return product_id, full_name, price, image_url


def get_mainpage_cards(driver, url):
    driver.get(url)
    scrolldown(driver, 50)
    main_page_html = BeautifulSoup(driver.page_source, "html.parser")

    content = main_page_html.find("div", {"class": "container"})
    content = content.findChildren(recursive=False)[-1].find("div")
    content = content.findChildren(recursive=False)
    content = [item for item in content if "freshIsland" in str(item)][-1]
    content = content.find("div").find("div").find("div")
    content = content.findChildren(recursive=False)

    all_cards = list()
    for layer in content:
        layer = layer.find("div")
        cards = layer.findChildren(recursive=False)

        cards_in_layer = list()
        for card in cards:
            card = card.findChildren(recursive=False)

            card_name = card[2].find("span", {"class": "tsBody500Medium"}).contents[0]
            card_url = card[2].find("a", href=True)["href"]
            product_url = "https://ozon.ru/" + card_url

            product_id, full_name, price, image_url = get_product_info(card_url)
            card_info = {product_id: {"short_name": card_name,
                                      "full_name": full_name,
                                      "url": product_url,
                                      "price": price,
                                      "image_url": image_url
                                      }
                         }
            cards_in_layer.append(card_info)

        all_cards.extend(cards_in_layer)
    return all_cards


def get_searchpage_cards(driver, url, all_cards=[]):
    driver.get(url)
    scrolldown(driver, 20)
    search_page_html = BeautifulSoup(driver.page_source, "html.parser")

    content = search_page_html.find("div", {"id": "layoutPage"})
    content = content.find("div")

    content_with_cards = content.find("div", {"class": "widget-search-result-container"})
    content_with_cards = content_with_cards.find("div").findChildren(recursive=False)

    cards_in_page = list()
    for card in content_with_cards:
        card_url = card.find("a", href=True)["href"]

        card_name = card.find("span", {"class": "tsBody500Medium"}).contents[0]

        product_url = "https://ozon.ru/" + card_url

        product_id, full_name, price, image_url = get_product_info(card_url)
        card_info = {product_id: {"short_name": card_name,
                                  "full_name": full_name,
                                  "url": product_url,
                                  "price": price,
                                  "image_url": image_url
                                  }
                     }
        cards_in_page.append(card_info)

    content_with_next = [div for div in content.find_all("a", href=True) if "Дальше" in str(div)]
    if not content_with_next:
        return cards_in_page
    else:
        next_page_url = "https://www.ozon.ru" + content_with_next[0]["href"]
        all_cards.extend(get_searchpage_cards(driver, next_page_url, cards_in_page))
        return all_cards


if __name__ == "__main__":
    print("Укажите позицию для парсинга:", '1) Балтика №0 Нефильтрованное Пшеничное Банка 0,45', '2) Flash Up Energy банка 0,45', sep='\n')
    if int(input()) == 1:
        url_search = "https://www.ozon.ru/search/?from_global=true&text=%D0%91%D0%B0%D0%BB%D1%82%D0%B8%D0%BA%D0%B0+%E2%84%960+%D0%9D%D0%B5%D1%84%D0%B8%D0%BB%D1%8C%D1%82%D1%80%D0%BE%D0%B2%D0%B0%D0%BD%D0%BD%D0%BE%D0%B5+%D0%9F%D1%88%D0%B5%D0%BD%D0%B8%D1%87%D0%BD%D0%BE%D0%B5+%D0%91%D0%B0%D0%BD%D0%BA%D0%B0+0%2C45"
    else:
        url_search = 'https://www.ozon.ru/search/?text=Flash+Up+Energy+%D0%B1%D0%B0%D0%BD%D0%BA%D0%B0+0%2C45&from_global=true'

    filename_prefix = input("Укажите название файла: ")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.csv"

    driver = init_webdriver()
    end_list = list()

    search_cards = get_searchpage_cards(driver, url_search)

    driver.quit()

    # Write the data to CSV
    with open(filename, mode='w') as file:
        writer = csv.writer(file, delimiter=',')
        writer.writerow(["Product ID", "Full Name", "Price", "Image URL"])
        for card in search_cards:
            for product_id, details in card.items():
                writer.writerow(
                    [product_id, details["full_name"], details["price"], details["image_url"]])

    print(f"Data has been saved to {filename}")
