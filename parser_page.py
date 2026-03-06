from typing import Dict, List


class ParsePage:
    def __init__(self):
        self.base_url = "https://www.wildberries.ru/catalog/{id}/detail.aspx?targetUrl=EX"

    def parse_urls(self, page: Dict = {}) -> List[str]:
        catalogs = []

        for item in page['products']:
            catalogs.append(self.base_url.format(id=item['id']))

        return catalogs
