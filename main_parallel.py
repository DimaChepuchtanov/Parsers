"""
Главный файл с ПАРАЛЛЕЛЬНОЙ обработкой карточек
Использует ThreadPoolExecutor для одновременной загрузки карточек

Для 4300 карточек время сократится с 38 часов до ~2-4 часов
(в зависимости от количества потоков и браузеров)
"""
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List

from downloader_page_parallel import DownloaderPageParallel
from parser_page import ParsePage
from filter import FilterData


def process_single_card(card_id: int, downloader: DownloaderPageParallel, 
                        parser: ParsePage) -> Dict[str, Any]:
    """
    Обработать одну карточку (выполняется в отдельном потоке)
    """
    page_js = downloader.get_card_js(page=card_id)
    page_html = downloader.get_card_page(page=card_id)

    base_card = {
        "Ссылка на товар": parser.get_card_link(page_js) if page_js != "Skip" else None,
        "Артикул": parser.get_card_id(page_js) if page_js != "Skip" else None,
        "Название": parser.get_card_title(page_js) if page_js != "Skip" else None,
        "Цена": parser.get_card_prace(page_js) if page_js != "Skip" else None,
        "Описание": parser.get_card_description(page_html) if page_html != "Skip" else "-",
        "Ссылки на изображения через запятую": parser.get_card_img(page_js) if page_html != "Skip" else None,
        "Все характеристики с сохранением их структуры": parser.get_card_additional(page_html) if page_html != "Skip" else None,
        "Название селлера": parser.get_card_seller(page_js) if page_js != "Skip" else None,
        "Ссылка на селлера": parser.get_card_seller_link(page_js) if page_js != "Skip" else None,
        "Размеры товара через запятую": parser.get_card_sizes(page_js) if page_js != "Skip" else None,
        "Остатки по товару (число)": parser.get_card_count_items(page_js) if page_js != "Skip" else None,
        "Рейтинг": parser.get_card_reviewRating(page_js) if page_js != "Skip" else None,
        "Количество отзывов": parser.get_card_feedbacks(page_js) if page_js != "Skip" else None,
    }

    return base_card


def main():
    """
    Основная функция с параллельной обработкой
    """
    # Настройки параллелизации
    MAX_WORKERS = 5        # Количество одновременных потоков
    BROWSER_POOL_SIZE = 5   # Количество браузеров в пуле

    print(f"Запускаю параллельную работу с {MAX_WORKERS} потоками")
    print(f"Размер пула браузеров: {BROWSER_POOL_SIZE}")

    downloader = DownloaderPageParallel(pool_size=BROWSER_POOL_SIZE)
    parser = ParsePage()
    filt = FilterData()

    all_catalogs: List[int] = []

    print("Запускаю сбор всех карточек из каталога")
    start = datetime.datetime.now()

    # Сбор каталога (синхронно, тут небольшое количество страниц)
    for i in range(1, 10000):
        page: dict = downloader.get_catalog(page=i)
        if page != "END" and page != "Skip" and page != "RETRY":
            all_catalogs = all_catalogs + parser.parse_urls(page)
        elif page == "Skip":
            continue
        elif page == "RETRY":
            for t in range(3):
                print(f"Ошибка парса странички: {i}. Делаю попытку {t+1}")
                page: dict = downloader.get_catalog(page=i)
                if page != "END" and page != "Skip" and page != "RETRY":
                    all_catalogs += parser.parse_urls(page)
                    break
                elif page == "Skip":
                    break
                elif page == "END":
                    break
        else:
            break

    catalog_time = datetime.datetime.now() - start
    print(f"Завершил сбор карточек с каталога")
    print(f"Время выполнения: {catalog_time.total_seconds() //3600}ч : {(catalog_time.total_seconds() % 3600) // 60}м : {catalog_time.total_seconds() % 3600 % 60}с")
    print(f"Собрано: {len(all_catalogs)} карточек")

    # ПАРАЛЛЕЛЬНАЯ ОБРАБОТКА КАРТОЧЕК
    print(f"\nЗапускаю параллельный сбор данных с карточек ({MAX_WORKERS} потоков)")
    cards = []
    start_card = datetime.datetime.now()

    # Используем ThreadPoolExecutor для параллельной обработки
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Создаём future для каждой карточки
        future_to_card = {
            executor.submit(process_single_card, card_id, downloader, parser): card_id 
            for card_id in all_catalogs
        }

        # Собираем результаты по мере завершения
        completed = 0
        for future in as_completed(future_to_card):
            card_id = future_to_card[future]
            try:
                card = future.result()
                cards.append(card)
                completed += 1

                # Логируем прогресс каждые 100 карточек
                if completed % 100 == 0:
                    elapsed = datetime.datetime.now() - start_card
                    rate = completed / elapsed if elapsed > 0 else 0
                    remaining = (len(all_catalogs) - completed) / rate if rate > 0 else 0
                    print(f"Обработано {completed}/{len(all_catalogs)} | "
                          f"Скорость: {rate:.1f} карт/сек | "
                          f"Осталось: {remaining/60:.1f} мин")
            except Exception as e:
                print(f"Ошибка при обработке карточки {card_id}: {e}")

    card_time = datetime.datetime.now() - start_card
    print(f"\nЗавершил параллельную работу")
    print(f"Время выполнения: {card_time.total_seconds() //3600}ч : {(card_time.total_seconds() % 3600) // 60}м : {card_time.total_seconds() % 3600 % 60}с")
    print(f"Собрано: {len(cards)} карточек")

    data = filt.list_to_pandas(cards)
    data = filt.filter_param(data)
    filt.to_exel(data)

    # Общее время
    total_time = catalog_time + card_time
    print(f"\n{'='*50}")
    print(f"Время выполнения: {total_time.total_seconds() //3600}ч : {(total_time.total_seconds() % 3600) // 60}м : {total_time.total_seconds() % 3600 % 60}с")
    print(f"{'='*50}")

    # Очистка
    downloader.close()


if __name__ == "__main__":
    main()
