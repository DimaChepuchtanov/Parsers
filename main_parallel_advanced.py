"""
Продвинутая версия с асинхронной обработкой
Использует asyncio + aiohttp для максимальной производительности

Для 4300 карточек: потенциально ~30-60 минут (в 40-80 раз быстрее!)
Требует: pip install aiohttp aiofiles

ВНИМАНИЕ: Это альтернативная реализация без browser automation,
использует прямые HTTP запросы вместо Selenium
"""
import asyncio
import aiohttp
from time import time
from typing import Dict, Any, List, Optional
from json import loads


# Конфигурация
MAX_CONCURRENT_REQUESTS = 20  # Максимум одновременных запросов
REQUEST_TIMEOUT = 30          # Таймаут запроса в секундах

# URL-шаблоны
URL_CATALOG = 'https://www.wildberries.ru/__internal/u-search/exastmatch/ru/common/v18/search?ab_testing=false&appType=1&curr=rub&dest=-1586361&hide_dtype=9&hide_vflags=4294967296&lang=ru&page={page}&query=пальто+из+натуральной+шерсти&resultset=catalog&sort=popular&spp=30&suppressSpellcheck=fals'
URL_CARD_PAGE = "https://www.wildberries.ru/catalog/{id}/detail.aspx"
URL_CARD_JSON = 'https://www.wildberries.ru/__internal/u-card/cards/v4/detail?appType=1&curr=rub&dest=-1586361&lang=ru&nm={id}'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
}


class AsyncDownloader:
    """Асинхронный загрузчик страниц"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(
            limit=MAX_CONCURRENT_REQUESTS,
            limit_per_host=MAX_CONCURRENT_REQUESTS
        )
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=HEADERS
        )
        return self
    
    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()
    
    async def fetch_json(self, url: str) -> Optional[Dict]:
        """Асинхронно получить JSON данные"""
        async with self.semaphore:
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
            except Exception as e:
                print(f"Ошибка запроса {url}: {e}")
                return None
    
    async def fetch_html(self, url: str) -> Optional[str]:
        """Асинхронно получить HTML страницу"""
        async with self.semaphore:
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        return await response.text()
                    return None
            except Exception as e:
                print(f"Ошибка запроса {url}: {e}")
                return None
    
    async def get_catalog(self, page: int) -> Optional[List]:
        """Получить каталог товаров"""
        url = URL_CATALOG.format(page=page)
        data = await self.fetch_json(url)
        if data and "products" in data:
            return data['products']
        return None
    
    async def get_card_json(self, card_id: int) -> Optional[Dict]:
        """Получить JSON данные карточки"""
        url = URL_CARD_JSON.format(id=card_id)
        data = await self.fetch_json(url)
        if data and "products" in data and len(data['products']) > 0:
            return data['products'][0]
        return None
    
    async def get_card_html(self, card_id: int) -> Optional[str]:
        """Получить HTML страницу карточки"""
        url = URL_CARD_PAGE.format(id=card_id)
        return await self.fetch_html(url)


class AsyncParser:
    """Асинхронный парсер (для совместимости, логика та же)"""
    
    @staticmethod
    def parse_urls(page: Dict = {}) -> List[int]:
        return [item['id'] for item in page]
    
    @staticmethod
    def get_card_title(page: Dict) -> str:
        return page.get('name')
    
    @staticmethod
    def get_card_link(page: Dict) -> str:
        return f"https://www.wildberries.ru/catalog/{page.get('id')}/detail.aspx"
    
    @staticmethod
    def get_card_id(page: Dict) -> str:
        return str(page.get('id'))
    
    @staticmethod
    def get_card_price(page: str) -> str:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(page, 'html.parser')
        try:
            price = soup.find('div', {"class": "priceBlock--ZADKT"})
            if price:
                return price.get_text().replace('\xa0', '').replace("₽", "₽ | ")
        except:
            pass
        return None
    
    @staticmethod
    def get_card_seller(page: Dict) -> str:
        return page.get('brand')
    
    @staticmethod
    def get_card_seller_link(page: Dict) -> str:
        brand_id = page.get('brandId')
        if brand_id:
            return f"https://www.wildberries.ru/brands/{brand_id}"
        return None
    
    @staticmethod
    def get_card_sizes(page: Dict) -> str:
        sizes = page.get('sizes', [])
        return ', '.join([s['name'] for s in sizes])
    
    @staticmethod
    def get_card_count_items(page: Dict) -> str:
        count = 0
        for item in page.get('sizes', []):
            for stock in item.get('stocks', []):
                count += stock.get('qty', 0)
        return str(count)
    
    @staticmethod
    def get_card_review_rating(page: Dict) -> str:
        return str(page.get('reviewRating', 0))
    
    @staticmethod
    def get_card_feedbacks(page: Dict) -> str:
        return str(page.get('feedbacks', 0))


async def process_card_async(card_id: int, downloader: AsyncDownloader) -> Dict[str, Any]:
    """
    Асинхронно обработать одну карточку
    """
    # Параллельно загружаем JSON и HTML
    card_json, card_html = await asyncio.gather(
        downloader.get_card_json(card_id),
        downloader.get_card_html(card_id)
    )
    
    parser = AsyncParser()
    
    result = {
        "Ссылка на товар": parser.get_card_link(card_json) if card_json else None,
        "Артикул": parser.get_card_id(card_json) if card_json else None,
        "Название": parser.get_card_title(card_json) if card_json else None,
        "Цена": parser.get_card_price(card_html) if card_html else None,
        "Название селлера": parser.get_card_seller(card_json) if card_json else None,
        "Ссылка на селлера": parser.get_card_seller_link(card_json) if card_json else None,
        "Размеры товара через запятую": parser.get_card_sizes(card_json) if card_json else None,
        "Остатки по товару (число)": parser.get_card_count_items(card_json) if card_json else None,
        "Рейтинг": parser.get_card_review_rating(card_json) if card_json else None,
        "Количество отзывов": parser.get_card_feedbacks(card_json) if card_json else None,
    }
    
    return result


async def collect_catalog(downloader: AsyncDownloader) -> List[int]:
    """Собрать все ID карточек из каталога"""
    all_ids = []
    for page_num in range(1, 100):
        products = await downloader.get_catalog(page_num)
        if products:
            all_ids.extend(AsyncParser.parse_urls(products))
            print(f"Страница {page_num}: собрано {len(products)} товаров")
        else:
            break
    return all_ids


async def main_async():
    """
    Основная асинхронная функция
    """
    print("=" * 60)
    print("АСИНХРОННАЯ ВЕРСИЯ ПАРСЕРА")
    print(f"Максимум одновременных запросов: {MAX_CONCURRENT_REQUESTS}")
    print("=" * 60)
    
    start_total = time()
    
    async with AsyncDownloader() as downloader:
        # Шаг 1: Сбор каталога
        print("\n[1/2] Сбор ID карточек из каталога...")
        start = time()
        all_catalogs = await collect_catalog(downloader)
        catalog_time = time() - start
        print(f"Найдено {len(all_catalogs)} карточек за {catalog_time:.1f} сек")
        
        # Шаг 2: Параллельная загрузка всех карточек
        print(f"\n[2/2] Загрузка данных с {len(all_catalogs)} карточек...")
        start = time()
        
        cards = []
        completed = 0
        
        # Создаём задачи для всех карточек
        tasks = [
            process_card_async(card_id, downloader) 
            for card_id in all_catalogs
        ]
        
        # Выполняем с отслеживанием прогресса
        for coro in asyncio.as_completed(tasks):
            card = await coro
            cards.append(card)
            completed += 1
            
            if completed % 100 == 0:
                elapsed = time() - start
                rate = completed / elapsed
                remaining = (len(all_catalogs) - completed) / rate
                print(f"Прогресс: {completed}/{len(all_catalogs)} | "
                      f"{rate:.1f} карт/сек | Осталось: {remaining/60:.1f} мин")
        
        card_time = time() - start
        
        # Итоги
        total_time = time() - start_total
        
        print("\n" + "=" * 60)
        print("РЕЗУЛЬТАТЫ:")
        print(f"  Каталог: {catalog_time:.1f} сек")
        print(f"  Карточки: {card_time:.1f} сек ({len(cards)} шт)")
        print(f"  Общее время: {total_time:.1f} сек ({total_time/60:.1f} мин)")
        print(f"  Скорость: {len(cards)/total_time:.1f} карт/сек")
        print("=" * 60)
        
        return cards


def main():
    """Точка входа"""
    cards = asyncio.run(main_async())
    print(f"\nИтого обработано: {len(cards)} карточек")


if __name__ == "__main__":
    main()

