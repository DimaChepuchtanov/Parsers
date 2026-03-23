from time import time
from datetime import datetime

from downloader_page import DownloaderPage
from parser_page import ParsePage


downloader = DownloaderPage()
parser = ParsePage()

all_catalogs = []

print("Запускаю работу ")
start = time()

print("Запускаю сбор всех карточек из каталога")
start_catalog = time()
for i in range(1, 100):
    pages: dict = downloader.get_catalog(page=i)
    if pages != "END" and pages != "Skip" and pages != "RETRY":
        for page in pages:
            base_card = {
                "Ссылка на товар": f"https://www.wildberries.ru/catalog/{page['id']}/detail.aspx",
                "Артикул": page['id'],
                "Название": page['name'],
                "Цена": parser.get_card_prace(page['sizes']),
                "Описание": None, # parser.get_card_description(downloader.get_card(page=page['id'])),
                "Ссылки на изображения через запятую": parser.get_card_img(page['pics'], id=page['id']),
                "Все характеристики с сохранением их структуры": None, # parser.get_card_description(downloader.get_card(page=page['id'])),
                "Название селлера": page['brand'],
                "Ссылка на селлера": f"https://www.wildberries.ru/brands/{page['brandId']}",
                "Размеры товара через запятую": ', '.join([size['name'] for size in page['sizes']]),
                "Остатки по товару (число)": parser.get_card_count_items(page['sizes']),
                "Рейтинг": page['reviewRating'],
                "Количество отзывов": page['feedbacks']
            }
            all_catalogs.append(base_card)
    elif pages == "Skip":
        continue
    elif pages == "RETRY":
        for t in range(3):
            print(f"Ошибка парса странички: {i}. Делаю попытку {t+1}")

            pages: dict = downloader.get_catalog(page=i)
            if pages != "END" and pages != "Skip" and pages != "RETRY":
                for page in pages:
                    base_card = {
                        "Ссылка на товар": f"https://www.wildberries.ru/catalog/{page['id']}/detail.aspx",
                        "Артикул": page['id'],
                        "Название": page['name'],
                        "Цена": parser.get_card_prace(page['sizes']),
                        "Описание": None, # parser.get_card_description(downloader.get_card(page=page['id'])),
                        "Ссылки на изображения через запятую": parser.get_card_img(page['pics'], id=page['id']),
                        "Все характеристики с сохранением их структуры": None, # parser.get_card_description(downloader.get_card(page=page['id'])),
                        "Название селлера": page['brand'],
                        "Ссылка на селлера": f"https://www.wildberries.ru/brands/{page['brandId']}",
                        "Размеры товара через запятую": ', '.join([size['name'] for size in page['sizes']]),
                        "Остатки по товару (число)": parser.get_card_count_items(page['sizes']),
                        "Рейтинг": page['reviewRating'],
                        "Количество отзывов": page['feedbacks']
                    }
                    all_catalogs.append(base_card)
                break
            elif pages == "Skip":
                break
            elif pages == "END":
                break
    else:
        break

catalog_time = datetime.now() - start
print(f"Завершил сбор карточек с каталога")
print(f"Время выполнения: {catalog_time.total_seconds() //3600}ч : {(catalog_time.total_seconds() % 3600) // 60}м : {catalog_time.total_seconds() % 3600 % 60}с")
print(f"Собрано: {len(all_catalogs)} карточек")

