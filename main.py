from time import time

from downloader_page import DownloaderPage
from parser_page import ParsePage


downloader = DownloaderPage()
parser = ParsePage()

all_catalogs = []

print("Запускаю работу ")
start = time()


for i in range(1, 100):
    page: dict = downloader.get_page(page=i)
    if page != "END" and page != "Skip" and page != "RETRY":
        all_catalogs = all_catalogs + parser.parse_urls(page)
    elif page == "Skip":
        continue
    elif page == "RETRY":
        for t in range(3):
            print(f"Ошибка парса странички: {i}. Делаю попытку {t+1}")

            page: dict = downloader.get_page(page=i)
            if page != "END" and page != "Skip" and page != "RETRY":
                all_catalogs += parser.parse_urls(page)
                break
            elif page == "Skip":
                break
            elif page == "END":
                break
    else:
        break


print("Количество записей: ", len(all_catalogs))
print("Общее время выполнения парса% ", (time()-start) // 60)
