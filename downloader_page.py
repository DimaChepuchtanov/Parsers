from typing import Optional, Dict, Union
from json import loads, JSONDecodeError

from botasaurus.browser import Driver

from exceptions import PageIsNull, InvalidJson


class DownloaderPage:
    def __init__(self):
        self.driver = Driver(headless=True)
        self.base_url = 'https://www.wildberries.ru/__internal/u-search/exactmatch/ru/common/v18/search?ab_testing=false&appType=1&curr=rub&dest=-1586361&hide_dtype=9&hide_vflags=4294967296&lang=ru&page={page}&query=пальто+из+натуральной+шерсти&resultset=catalog&sort=popular&spp=30&suppressSpellcheck=fals'

    def get_page(self, page: int = 0) -> Optional[Union[Dict, str]]:
        try:
            self.driver.get(
                link=self.base_url.format(page=page),
                wait=1
            )
            page: dict = loads(self.driver.page_text)

            if "products" not in page:
                raise PageIsNull()
            else:
                return page
        except PageIsNull as e:
            print(str(e))
            return "END"
        except JSONDecodeError:
            print("retur")
            return "RETRY"
        except Exception as e:
            print("Ошибка ", e)
            return "Skip"
    
    def close(self):
        self.driver.close()
