class PageIsNull(Exception):
    """Страничка с товаром пустая"""

    def __init__(self):
        pass

    def __str__(self):
        return "Карточки товаров закончились"
