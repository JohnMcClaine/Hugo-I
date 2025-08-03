import os
import random
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# РЕШЕНИЕ 1: Отключить SSL-проверку для WebDriverManager
os.environ['WDM_SSL_VERIFY'] = '0'

# Создание папки для скриншотов
SCREENSHOTS_DIR = "screenshots"
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


def human_delay(min_s=0.8, max_s=2.5):
    """Задержка как у человека"""
    time.sleep(random.uniform(min_s, max_s))


def human_typing(element, text):
    """Печать по буквам с задержками"""
    for letter in text:
        element.send_keys(letter)
        time.sleep(random.uniform(0.07, 0.22))
        if letter == " ":
            time.sleep(random.uniform(0.15, 0.35))


def take_screenshot(driver, step):
    filename = os.path.join(SCREENSHOTS_DIR, f"{step}.png")
    driver.save_screenshot(filename)
    print(f"Скриншот сохранен: {filename}")


def test_google_kitten_search():
    # Запуск браузера с дополнительными опциями для SSL
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")

    # Добавляем опции для работы с SSL сертификатами
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--ignore-ssl-errors")
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.4896.127 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    ]
    options.add_argument(f"user-agent={random.choice(user_agents)}")

    try:
        # РЕШЕНИЕ 2: Создаем драйвер с отключением SSL-проверки
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        print("✅ Браузер успешно запущен!")

    except Exception as e:
        print(f"❌ Ошибка при создании WebDriver: {e}")
        print("\n🔧 Попробуйте альтернативные решения:")
        print("1. Скачайте ChromeDriver вручную: https://chromedriver.chromium.org/")
        print("2. Или используйте метод без WebDriverManager (см. ниже)")
        return

    try:
        # Остальной код теста остается тем же
        driver.get("https://www.google.com/")
        human_delay(1, 2)
        take_screenshot(driver, "01_google_home")

        # Принять куки (если нужно)
        try:
            consent_selectors = [
                '//button[contains(text(),"Принять")]',
                '//button[contains(text(),"Accept")]',
                '#L2AGLb',
                '[aria-label*="Accept"]'
            ]

            for selector in consent_selectors:
                try:
                    if selector.startswith('//'):
                        consent = driver.find_element(By.XPATH, selector)
                    else:
                        consent = driver.find_element(By.CSS_SELECTOR, selector)
                    consent.click()
                    human_delay()
                    take_screenshot(driver, "02_consent_accepted")
                    break
                except:
                    continue
        except:
            pass

        # Найти поисковую строку
        search_selectors = [
            "input[name='q']",
            "textarea[name='q']",
            "[title*='Поиск']",
            "[title*='Search']"
        ]

        search_box = None
        for selector in search_selectors:
            try:
                search_box = driver.find_element(By.CSS_SELECTOR, selector)
                break
            except:
                continue

        if not search_box:
            print("❌ Поисковая строка не найдена")
            return

        search_box.click()
        human_delay()
        take_screenshot(driver, "03_search_box_clicked")

        # Ввести запрос "котята"
        query = random.choice([
            "милые котята", "cute kittens", "котята фото", "kitten pictures"
        ])
        print(f"🔍 Ищем: {query}")
        human_typing(search_box, query)
        human_delay(1, 1.7)
        take_screenshot(driver, "04_query_typed")

        # Нажать Enter или выбрать автодополнение
        if random.random() < 0.5:
            search_box.send_keys(Keys.RETURN)
        else:
            human_delay(0.3, 0.7)
            search_box.send_keys(Keys.ARROW_DOWN)
            time.sleep(0.4)
            search_box.send_keys(Keys.RETURN)

        human_delay(2, 3)
        take_screenshot(driver, "05_search_results")

        # Открыть вкладку "Картинки"
        images_selectors = [
            '//a[contains(text(),"Картинки")]',
            '//a[contains(text(),"Images")]',
            'a[href*="tbm=isch"]'
        ]

        images_tab = None
        for selector in images_selectors:
            try:
                if selector.startswith('//'):
                    images_tab = driver.find_element(By.XPATH, selector)
                else:
                    images_tab = driver.find_element(By.CSS_SELECTOR, selector)
                break
            except:
                continue

        if images_tab:
            images_tab.click()
            human_delay(2, 3)
            take_screenshot(driver, "06_images_tab")
            print("🖼️ Перешли во вкладку 'Картинки'")
        else:
            print("⚠️ Вкладка 'Картинки' не найдена")

        # Прокручивать страницу
        for i in range(3):
            driver.execute_script(f"window.scrollBy(0, {random.randint(250, 550)});")
            human_delay(0.7, 1.6)
            take_screenshot(driver, f"07_scrolled_{i + 1}")
            print(f"📜 Прокрутка {i + 1}/3")

        # Кликнуть на случайное изображение
        try:
            images = driver.find_elements(By.CSS_SELECTOR, "img[src*='http']")
            visible_images = [img for img in images if img.is_displayed()]

            if visible_images:
                img = random.choice(visible_images[:min(10, len(visible_images))])
                driver.execute_script("arguments[0].scrollIntoView(true);", img)
                human_delay(0.4, 0.9)
                img.click()
                human_delay(1, 2)
                take_screenshot(driver, "08_kitten_image_opened")
                print("🐱 Кликнули на изображение котенка!")
            else:
                print("⚠️ Изображения не найдены")

        except Exception as e:
            print(f"⚠️ Ошибка при клике на изображение: {e}")

        print("✅ Тест успешно завершен!")

    except Exception as e:
        print(f"❌ Ошибка в тесте: {e}")
        take_screenshot(driver, "error_screenshot")

    finally:
        driver.quit()


# АЛЬТЕРНАТИВНОЕ РЕШЕНИЕ: Без WebDriverManager
def test_google_kitten_search_manual():
    """Альтернативный метод без WebDriverManager"""

    # Укажите путь к chromedriver.exe вручную
    CHROMEDRIVER_PATH = r"C:\path\to\chromedriver.exe"  # Замените на свой путь

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")

    try:
        # Используем локальный chromedriver
        service = Service(CHROMEDRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=options)
        print("✅ Браузер запущен с локальным ChromeDriver!")

        # Далее тот же код теста...
        driver.get("https://www.google.com/")
        human_delay(2, 3)
        print("🌐 Google загружен")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("💡 Скачайте ChromeDriver с https://chromedriver.chromium.org/")

    finally:
        if 'driver' in locals():
            driver.quit()


if __name__ == "__main__":
    print("🚀 Запуск теста поиска котят...")
    test_google_kitten_search()

    # Если первый метод не работает, попробуйте второй:
    # test_google_kitten_search_manual()
