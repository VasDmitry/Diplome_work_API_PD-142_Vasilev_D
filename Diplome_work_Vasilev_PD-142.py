import json
import requests
import sys
from tqdm import tqdm

# from yandex_token import yandex_token


class CatText:
    def __init__(self):
        self.base_url = "https://cataas.com/cat/says/"

    def _get_cat_with_text(self, text):
        self.text = text
        url = f"{self.base_url}{text}"
        try:
            image_response = requests.get(url, timeout=5)
            image_response.raise_for_status()
            return image_response.content
        except requests.exceptions.RequestException as error:
            print(f"Ошибка при загрузке изображения: {error}")
            sys.exit(1)

    def save_on_yandex_disk(self, yandex_token):
        text = input("""Введите текст, не используя спецсимволы (/\\?#%&=""''<>): """)
        if set(text) & set("""<>:"'/\\|?*#%"""):
            print("Ошибка. В тексте используются спецсимволы.")
            sys.exit(1)
        name = f"{text}.jpg"

        # Прогресс-бар
        pbar = tqdm(total=3, desc="Прогресс", unit="этап")

        # Этап 1 Получение изображения
        pbar.set_description("Получение изображения")
        cat_image = self._get_cat_with_text(text)
        pbar.update(1)

        yandex_url = "https://cloud-api.yandex.net/v1/disk/resources"

        # Создаем папку на Яндекс-диске
        headers = {"Authorization": yandex_token}
        params = {"path": "PD-142"}
        response = requests.get(yandex_url, headers=headers, params=params)

        if response.status_code == 404:
            requests.put(yandex_url, headers=headers, params=params)
        elif response.status_code != 200:
            pbar.close()
            print(f"Ошибка: {response.status_code} — {response.json()}")

        # Этап 2: Загрузка картинки в папку PD-142 на Яндекс-диске
        pbar.set_description("Загрузка картинки")
        params = {"path": f"PD-142/{name}", "overwrite": "true"}
        response_upload_link = requests.get(
            "https://cloud-api.yandex.net/v1/disk/resources/upload",
            headers=headers,
            params=params,
        )
        if response_upload_link.status_code != 200:
            pbar.close()
            print("Ошибка получения ссылки:", response_upload_link.json())
            return
        upload_link = response_upload_link.json()["href"]
        upload_result = requests.put(upload_link, data=cat_image)
        pbar.update(1)

        # Этап 3: Сохраняем json файл
        if upload_result.status_code == 201:
            pbar.set_description("Создание JSON")
            image_size = len(cat_image)
            json_file = json.dumps(
                {"name": name, "size": image_size}, ensure_ascii=False
            ).encode("utf-8")
            params = {"path": f"PD-142/{text}.json", "overwrite": "true"}
            response_upload_link = requests.get(
                "https://cloud-api.yandex.net/v1/disk/resources/upload",
                headers=headers,
                params=params,
            )
            upload_link = response_upload_link.json()["href"]
            requests.put(upload_link, data=json_file)
            pbar.update(1)
            pbar.close()
            print(
                f"Файл {name} успешно загружен на Яндекс диск в папку PD-142. Файл json успешно создан и сохранен туда же."
            )
            return
        else:
            pbar.close()
            print("Ошибка загрузки")
            return


yandex_token = input("Для успешной работы программы скопируйте сюда Яндекс токен: ")
cat_image = CatText()
cat_image.save_on_yandex_disk(yandex_token)
