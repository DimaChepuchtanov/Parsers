from typing import Dict, List, Any
from json import dumps

from bs4 import BeautifulSoup


class ParsePage:
    def __init__(self):
        pass

    def get_card_prace(self, page: Dict[str, Any]) -> int:
        result = []
        for data in page:
            if 'price' in data:
                result.append(data['price']['product'] // 100)
        price = max(result)
        return price

    def get_card_description(self, page: Dict[str, Any]) -> str:
        try:
            description = page['description']
        except Exception as e:
            print("Ошибка получения описания.", e),
            return None
        else:
            return description

    def get_card_img(self, page: int, id: int) -> str:

        img_url = "basket-27.wbbasket.ru/vol{vol}/part{part}/{id}/images/big/{num}.webp"

        imgs = []
        for i in range(1, page):
            imgs.append(img_url.format(vol=str(id)[:4], part=str(id)[:6], num= str(i), id=id))
        return '\n'.join(imgs)

    def get_card_additional(self, page: Dict[str, Any]) -> str:
        try:
            additional = {}
            for item in page['options']:
                additional[item['name']] = item['value']
            return dumps(additional)
        except Exception:
            return None

    def get_card_count_items(self, page: Dict[str, Any]) -> int:
        count = 0
        for item in page:
            if "stocks" not in item:
                continue
            for j in item['stocks']:
                count += j['qty']
        return count
