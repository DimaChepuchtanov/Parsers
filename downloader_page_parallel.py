"""
Параллельный загрузчик страниц
Использует пул браузеров для одновременной загрузки нескольких карточек
"""
from typing import Optional, Dict, List
from json import loads, JSONDecodeError
from random import randint
from time import sleep
import threading

from botasaurus.browser import Driver

from exceptions import PageIsNull


class BrowserPool:
    """
    Пул браузеров для параллельной работы
    Создаёт N браузеров и分配 их между потоками
    """
    def __init__(self, pool_size: int = 5):
        self.pool_size = pool_size
        self.drivers: List[Driver] = []
        self._lock = threading.Lock()
        
        print(f"Инициализирую пул браузеров размером {pool_size}...")
        for i in range(pool_size):
            driver = Driver(headless=False)
            self.drivers.append(driver)
            print(f"Браузер {i+1}/{pool_size} готов")
    
    def get_driver(self) -> Driver:
        """Получить свободный браузер из пула"""
        with self._lock:
            for driver in self.drivers:
                if not hasattr(driver, '_in_use') or not driver._in_use:
                    driver._in_use = True
                    return driver
            # Если все заняты, ждём
            sleep(0.5)
            return self.get_driver()
    
    def release_driver(self, driver: Driver):
        """Освободить браузер"""
        driver._in_use = False
    
    def close_all(self):
        """Закрыть все браузеры"""
        for driver in self.drivers:
            try:
                driver.close()
            except:
                pass


class DownloaderPageParallel:
    def __init__(self, pool_size: int = 5):
        self.url_catalog = 'https://www.wildberries.ru/__internal/u-search/exactmatch/ru/common/v18/search?ab_testing=false&appType=1&curr=rub&dest=-1586361&hide_dtype=9&hide_vflags=4294967296&lang=ru&page={page}&query=пальто+из+натуральной+шерсти&resultset=catalog&sort=popular&spp=30&suppressSpellcheck=fals'
        self.url_card_page = "https://ekt-basket-cdn-06bl.geobasket.ru/vol{val}/part{part}/{id}/info/ru/card.json"
        self.url_card_js = 'https://www.wildberries.ru/__internal/u-card/cards/v4/detail?appType=1&curr=rub&dest=-1586361&lang=ru&nm={id}'

        # Используем пул браузеров
        self.browser_pool = BrowserPool(pool_size=pool_size)

    def get_catalog(self, page: int = 0) -> Optional[List]:
        """Получить каталог (синхронно, один браузер)"""
        driver = self.browser_pool.get_driver()
        try:
            driver.get(
                link=self.url_catalog.format(page=page),
                wait=2
            )
            page_data: dict = loads(driver.page_text)

            if "products" not in page_data:
                raise PageIsNull()
            else:
                return page_data['products']
        except PageIsNull as e:
            print(str(e))
            return "END"
        except JSONDecodeError:
            print("retur")
            return "RETRY"
        except Exception as e:
            print("Ошибка ", e)
            return "Skip"
        finally:
            self.browser_pool.release_driver(driver)

    def get_card_js(self, page: int = 0) -> Optional[Dict]:
        """Получить JS данные карточки"""
        driver = self.browser_pool.get_driver()
        try:
            driver.get(
                link=self.url_card_js.format(id=page),
                wait=2
            )
            page_data: dict = loads(driver.page_text)

            if "products" not in page_data:
                raise Exception("Ошибка данных")
            else:
                return page_data['products'][0]
        except Exception as e:
            print("Ошибка ", e)
            return "Skip"
        finally:
            self.browser_pool.release_driver(driver)

    def get_card_page(self, page: int = 0) -> Optional[str]:
        """Получить HTML страницу карточки (ОПТИМИЗИРОВАНО - убран лишний sleep)"""
        driver = self.browser_pool.get_driver()
        try:
            driver.get(
                link=self.url_card_page.format(val=str(page)[:4], part=str(page)[:6], id=page),
                wait=2
            )
            page_data: dict = loads(driver.page_text)
            return page_data

        except PageIsNull as e:
            print(str(e))
            return "END"
        except JSONDecodeError:
            print("retur")
            return "RETRY"
        except Exception as e:
            print("Ошибка ", e)
            return "Skip"
        finally:
            self.browser_pool.release_driver(driver)

    def close(self):
        self.browser_pool.close_all()

