from typing import Optional, Dict, Union, List
from json import loads, JSONDecodeError
from random import randint
from time import sleep

from botasaurus.browser import Driver

from exceptions import PageIsNull


class DownloaderPage:
    def __init__(self):
        self.driver = Driver(headless=False)
        self.url_catalog = 'https://www.wildberries.ru/__internal/u-search/exactmatch/ru/common/v18/search?ab_testing=false&appType=1&curr=rub&dest=-1586361&hide_dtype=9&hide_vflags=4294967296&lang=ru&page={page}&query=пальто+из+натуральной+шерсти&resultset=catalog&sort=popular&spp=30&suppressSpellcheck=fals'
        self.url_card = "https://ekt-basket-cdn-06bl.geobasket.ru/vol{val}/part{part}/{id}/info/ru/card.json"

    def get_catalog(self, page: int = 0) -> Optional[List]:
        try:
            self.driver.get(
                    link=self.url_catalog.format(page=page),
                    wait=1
            )
            page: dict = loads(self.driver.page_text)

            if "products" not in page:
                raise PageIsNull()
            else:
                return page['products']
        except PageIsNull as e:
            print(str(e))
            return "END"
        except JSONDecodeError:
            print("retur")
            return "RETRY"
        except Exception as e:
            print("Ошибка ", e)
            return "Skip"

    def get_card(self, page: int = 0) -> Optional[Dict]:
        try:
            self.driver.get(
                link=self.url_card.format(val=str(page)[:4], part=str(page)[:6], id=page),
                wait=2
            )
            page: dict = loads(self.driver.page_text)

            return page
        except Exception as e:
            print("Ошибка ", e)
            return "Skip"

    def close(self):
        self.driver.close()
