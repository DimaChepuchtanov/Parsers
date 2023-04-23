"""
    Парсер использует ТЛС адаптер.

"""

import ssl
import requests

from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from urllib3.util import ssl_

from bs4 import BeautifulSoup


CIPHERS = (
    'ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-SHA256:AES256-SHA'
)


class TlsAdapter(HTTPAdapter):

    def __init__(self, ssl_options=0, **kwargs):
        self.ssl_options = ssl_options
        super(TlsAdapter, self).__init__(**kwargs)

    def init_poolmanager(self, *pool_args, **pool_kwargs):
        ctx = ssl_.create_urllib3_context(ciphers=CIPHERS, cert_reqs=ssl.CERT_REQUIRED, options=self.ssl_options)
        self.poolmanager = PoolManager(*pool_args,
                                       ssl_context=ctx,
                                       **pool_kwargs)


class AvitoParser():
    
    def __init__(self):
        self.site = {}

    def __get_session(self):
        """
        Создание сессии для реквеста.
        """
        session = requests.session()
        adapter = TlsAdapter(ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1)
        session.mount("https://", adapter)
        
        return session

    def pars(self, url = None):
        """
        Функция предназначена для парса страницы через GET запрос
        Входные данные:
        :: url - Ссылка, которую будем парсить. По умолчанию, это пустая ссылка

        Выходные данные:
        :: FindText - Полный список объявлений
        """
        FindText = ""
        count = 0
        session = self.__get_session()
        try:
            r = session.request('GET', url = url)
            soup = BeautifulSoup(r.text,'lxml')

            flag = False
            for key,values in self.site.items():
                if key == url:
                    flag = True

            if flag:
                tes = soup.find_all('a',{'class':'iva-item-sliderLink-uLz1v'})
                for i in tes:    
                    if i['href'] not in self.site[url]:
                        FindText += " -- > https://www.avito.ru"+i['href'] + "\n"
                        count+=1
                        self.site[url].append(i['href'])
                    else:
                        pass
            else:
                self.site[url] = []
                tes = soup.find_all('a',{'class':'iva-item-sliderLink-uLz1v'})
                for i in tes:     
                    if i['href'] not in self.site[url]:
                        FindText += " -- > https://www.avito.ru"+i['href'] + "\n"
                        count+=1
                        self.site[url].append(i['href'])
                    else:
                        pass

        except Exception as exception:
            print(exception)

        if FindText != "":
            return FindText,count
        else:
            return "Новых объявлений"