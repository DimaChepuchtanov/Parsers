import pandas as pd

class FilterData:
    def __init__(self):
        self.title = ["Ссылка на товар", "Артикул", "Название", "Цена",
                      "Описание", "Ссылки на изображения через запятую",
                      "Все характеристики с сохранением их структуры",
                      "Название селлера", "Ссылка на селлера",
                      "Размеры товара через запятую", "Остатки по товару (число)",
                      "Рейтинг", "Количество отзывов"]

    def list_to_pandas(self, data: list) -> dict:
        dict_ = {}

        for title in self.title:
            dict_[title] = [x[title] for x in data]

        return pd.DataFrame(dict_)

    def filter_param(self, data: pd.DataFrame):
        data = data.query("Рейтинг >= 4.5 & Цена < 10000")
        return data
    
    def to_exel(self, data: pd.DataFrame):
        data.to_excel("result.xlsx")
        