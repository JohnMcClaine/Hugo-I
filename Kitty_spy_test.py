"""
Шпионский тест
"""

import os
import random
import time
import setuptools.dist
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium_stealth import stealth

# ========== НАСТРОЙКИ ========== #
SCREEN_DIR = "spy_screens"
os.makedirs(SCREEN_DIR, exist_ok=True)

SEARCH_QUERIES = [
    "милые котята", "смешные коты", "котята фото",
    "kкоты приколы", "смешные видео с котами"
]
# =============================== #


def human_delay(a=0.4, b=1.2):
    """Случайная задержка человека."""
    time.sleep(random.uniform(a, b))


def human_typing(element, text):
    """Ввод текста по буквам с паузой."""
    for ch in text:
        element.send_keys(ch)
        human_delay(0.05, 0.2)
    element.send_keys(Keys.ENTER)


def take_shot(driver, name):
    """Сохранить скриншот в папку."""
    path = os.path.join(SCREEN_DIR, f"{name}.png")
    driver.save_screenshot(path)
    print(f"📸 Скриншот сохранён: {path}")


def run_spy_test():
    # --- Инициализация UC в стелс режиме ---
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = uc.Chrome(options=options, headless=True)  # headless — «невидимый» режим

    # Прячем следы автоматизации
    stealth(driver,
            languages=["ru-RU", "ru", "en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL",
            fix_hairline=True,
            )

    try:
        # 1. Открываем Google
        driver.get("https://www.google.com/")
        human_delay(1, 2)

        # 2. Принимаем куки, если будет поп-ап
        try:
            cookies_btn = driver.find_element(By.ID, "L2AGLb")
            cookies_btn.click()
        except Exception:
            pass

        # 3. Находим поле поиска
        box = driver.find_element(By.NAME, "q")
        query = random.choice(SEARCH_QUERIES)
        print(f"🔍 Ищем: {query}")
        box.click()
        human_typing(box, query)

        # 4. Ждём результаты, переходим во вкладку «Картинки»
        human_delay(2, 3)
        images_link = driver.find_element(By.CSS_SELECTOR, "a[href*='tbm=isch']")
        images_link.click()
        human_delay(2, 3)

        # 5. Финальный скриншот страницы с картинками
        take_shot(driver, "kittens_images")

        print("✅ Шпионский тест завершён")
    finally:
        driver.quit()


if __name__ == "__main__":
    run_spy_test()
