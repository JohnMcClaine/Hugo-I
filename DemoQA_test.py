"""
Автотест проверки ключевых элементов интерфейса на сайте DemoQA.com
Проверяет наличие основных компонентов: навигация, кнопки, формы и т.д.
"""

import os
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Отключаем SSL проверку для WebDriverManager
os.environ['WDM_SSL_VERIFY'] = '0'

# Создание папки для скриншотов
SCREENSHOTS_DIR = "ui_test_screenshots"
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


class DemoQAUITest:
    """Класс для тестирования UI элементов на DemoQA"""

    def __init__(self):
        self.driver = None
        self.wait = None
        self.base_url = "https://demoqa.com"
        self.test_results = []

    def setup_driver(self):
        """Настройка и запуск браузера"""
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # Случайный User-Agent
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        options.add_argument(f"--user-agent={random.choice(user_agents)}")

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.wait = WebDriverWait(self.driver, 10)

            # Скрываем признаки автоматизации
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            print("✅ Браузер успешно запущен")
            return True

        except Exception as e:
            print(f"❌ Ошибка запуска браузера: {e}")
            return False

    def take_screenshot(self, name):
        """Сделать скриншот"""
        if self.driver:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}.png"
            filepath = os.path.join(SCREENSHOTS_DIR, filename)
            self.driver.save_screenshot(filepath)
            print(f"📸 Скриншот сохранен: {filepath}")
            return filepath
        return None

    def check_element_exists(self, locator, element_name, timeout=5):
        """Проверить существование элемента"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
            print(f"✅ {element_name}: найден")
            self.test_results.append(f"✅ {element_name}: PASS")
            return element
        except TimeoutException:
            print(f"❌ {element_name}: НЕ найден")
            self.test_results.append(f"❌ {element_name}: FAIL")
            return None

    def check_element_clickable(self, locator, element_name, timeout=5):
        """Проверить, что элемент кликабельный"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable(locator)
            )
            print(f"✅ {element_name}: кликабельный")
            self.test_results.append(f"✅ {element_name} (кликабельный): PASS")
            return element
        except TimeoutException:
            print(f"❌ {element_name}: НЕ кликабельный")
            self.test_results.append(f"❌ {element_name} (кликабельный): FAIL")
            return None

    def check_text_content(self, locator, element_name, expected_text=None):
        """Проверить текстовое содержимое элемента"""
        try:
            element = self.wait.until(EC.presence_of_element_located(locator))
            actual_text = element.text.strip()

            if expected_text:
                if expected_text.lower() in actual_text.lower():
                    print(f"✅ {element_name}: текст корректный ('{actual_text}')")
                    self.test_results.append(f"✅ {element_name} текст: PASS")
                else:
                    print(f"❌ {element_name}: неверный текст. Ожидали: '{expected_text}', получили: '{actual_text}'")
                    self.test_results.append(f"❌ {element_name} текст: FAIL")
            else:
                print(f"✅ {element_name}: содержит текст ('{actual_text}')")
                self.test_results.append(f"✅ {element_name} текст: PASS")

            return actual_text

        except Exception as e:
            print(f"❌ {element_name}: ошибка проверки текста - {e}")
            self.test_results.append(f"❌ {element_name} текст: FAIL")
            return None

    def test_homepage_elements(self):
        """Тест основных элементов главной страницы"""
        print("\n🏠 === ТЕСТИРОВАНИЕ ГЛАВНОЙ СТРАНИЦЫ ===")

        # Переходим на главную страницу
        self.driver.get(self.base_url)
        time.sleep(2)
        self.take_screenshot("01_homepage_loaded")

        # Проверяем заголовок страницы
        page_title = self.driver.title
        if "DEMOQA" in page_title.upper():
            print(f"✅ Заголовок страницы: корректный ('{page_title}')")
            self.test_results.append("✅ Заголовок страницы: PASS")
        else:
            print(f"❌ Заголовок страницы: некорректный ('{page_title}')")
            self.test_results.append("❌ Заголовок страницы: FAIL")

        # Проверяем логотип/главный заголовок
        logo_selectors = [
            (By.XPATH, "//img[contains(@src, 'Toolsqa')]"),
            (By.CSS_SELECTOR, "header img"),
            (By.XPATH, "//a[contains(@href, 'demoqa')]//img")
        ]

        logo_found = False
        for selector in logo_selectors:
            if self.check_element_exists(selector, "Логотип сайта", timeout=3):
                logo_found = True
                break

        if not logo_found:
            print("⚠️ Логотип не найден по стандартным селекторам")

        # Проверяем основные категории на главной странице
        categories = [
            (By.XPATH, "//h5[text()='Elements']", "Категория 'Elements'"),
            (By.XPATH, "//h5[text()='Forms']", "Категория 'Forms'"),
            (By.XPATH, "//h5[text()='Alerts, Frame & Windows']", "Категория 'Alerts, Frame & Windows'"),
            (By.XPATH, "//h5[text()='Widgets']", "Категория 'Widgets'"),
            (By.XPATH, "//h5[text()='Interactions']", "Категория 'Interactions'"),
            (By.XPATH, "//h5[text()='Book Store Application']", "Категория 'Book Store Application'")
        ]

        for locator, name in categories:
            self.check_element_exists(locator, name)
            self.check_element_clickable(locator, name)

        self.take_screenshot("02_homepage_elements_checked")

    def test_elements_page(self):
        """Тест страницы Elements"""
        print("\n📝 === ТЕСТИРОВАНИЕ СТРАНИЦЫ ELEMENTS ===")

        # Кликаем на Elements
        try:
            elements_card = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//h5[text()='Elements']"))
            )
            elements_card.click()
            time.sleep(2)
            self.take_screenshot("03_elements_page_loaded")

            # Проверяем боковое меню
            menu_items = [
                (By.XPATH, "//span[text()='Text Box']", "Text Box"),
                (By.XPATH, "//span[text()='Check Box']", "Check Box"),
                (By.XPATH, "//span[text()='Radio Button']", "Radio Button"),
                (By.XPATH, "//span[text()='Web Tables']", "Web Tables"),
                (By.XPATH, "//span[text()='Buttons']", "Buttons"),
                (By.XPATH, "//span[text()='Links']", "Links"),
                (By.XPATH, "//span[text()='Upload and Download']", "Upload and Download")
            ]

            for locator, name in menu_items:
                self.check_element_exists(locator, f"Пункт меню '{name}'")
                self.check_element_clickable(locator, f"Пункт меню '{name}'")

        except Exception as e:
            print(f"❌ Ошибка перехода на страницу Elements: {e}")
            self.test_results.append("❌ Переход на страницу Elements: FAIL")

    def test_text_box_functionality(self):
        """Тест функциональности Text Box"""
        print("\n📄 === ТЕСТИРОВАНИЕ TEXT BOX ===")

        try:
            # Кликаем на Text Box
            text_box_menu = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Text Box']"))
            )
            text_box_menu.click()
            time.sleep(2)
            self.take_screenshot("04_text_box_page")

            # Проверяем элементы формы
            form_elements = [
                (By.ID, "userName", "Поле 'Full Name'"),
                (By.ID, "userEmail", "Поле 'Email'"),
                (By.ID, "currentAddress", "Поле 'Current Address'"),
                (By.ID, "permanentAddress", "Поле 'Permanent Address'"),
                (By.ID, "submit", "Кнопка 'Submit'")
            ]

            for locator, name in form_elements:
                self.check_element_exists(locator, name)

            # Проверяем, что кнопку Submit можно нажать
            self.check_element_clickable((By.ID, "submit"), "Кнопка 'Submit'")

            # Заполняем форму тестовыми данными
            test_data = {
                "userName": "Тестовый Пользователь",
                "userEmail": "test@example.com",
                "currentAddress": "Текущий адрес, ул. Тестовая, д. 1",
                "permanentAddress": "Постоянный адрес, ул. Постоянная, д. 2"
            }

            for field_id, value in test_data.items():
                try:
                    field = self.driver.find_element(By.ID, field_id)
                    field.clear()
                    field.send_keys(value)
                    print(f"✅ Поле '{field_id}': заполнено значением '{value}'")
                except Exception as e:
                    print(f"❌ Ошибка заполнения поля '{field_id}': {e}")

            time.sleep(1)
            self.take_screenshot("05_text_box_filled")

            # Нажимаем Submit
            submit_btn = self.driver.find_element(By.ID, "submit")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_btn)
            time.sleep(1)
            submit_btn.click()
            time.sleep(2)

            # Проверяем результат
            try:
                output = self.wait.until(
                    EC.presence_of_element_located((By.ID, "output"))
                )
                if output.is_displayed():
                    print("✅ Результат формы: отображается")
                    self.test_results.append("✅ Отправка формы Text Box: PASS")
                    self.take_screenshot("06_text_box_result")
                else:
                    print("❌ Результат формы: не отображается")
                    self.test_results.append("❌ Отправка формы Text Box: FAIL")

            except TimeoutException:
                print("❌ Результат формы: не найден")
                self.test_results.append("❌ Отправка формы Text Box: FAIL")

        except Exception as e:
            print(f"❌ Ошибка тестирования Text Box: {e}")
            self.test_results.append("❌ Тестирование Text Box: FAIL")

    def test_buttons_page(self):
        """Тест страницы с кнопками"""
        print("\n🔘 === ТЕСТИРОВАНИЕ BUTTONS ===")

        try:
            # Переходим на страницу Buttons
            buttons_menu = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Buttons']"))
            )
            buttons_menu.click()
            time.sleep(2)
            self.take_screenshot("07_buttons_page")

            # Проверяем наличие кнопок
            button_elements = [
                (By.ID, "doubleClickBtn", "Кнопка 'Double Click Me'"),
                (By.ID, "rightClickBtn", "Кнопка 'Right Click Me'"),
                (By.XPATH, "//button[text()='Click Me']", "Кнопка 'Click Me'")
            ]

            for locator, name in button_elements:
                self.check_element_exists(locator, name)
                self.check_element_clickable(locator, name)

            # Тестируем обычный клик
            try:
                click_btn = self.driver.find_element(By.XPATH, "//button[text()='Click Me']")
                click_btn.click()
                time.sleep(1)

                # Проверяем сообщение после клика
                try:
                    message = self.driver.find_element(By.ID, "dynamicClickMessage")
                    if message.is_displayed():
                        print(f"✅ Сообщение после клика: '{message.text}'")
                        self.test_results.append("✅ Обычный клик по кнопке: PASS")
                    else:
                        print("❌ Сообщение после клика: не отображается")
                        self.test_results.append("❌ Обычный клик по кнопке: FAIL")
                except NoSuchElementException:
                    print("❌ Сообщение после клика: не найдено")
                    self.test_results.append("❌ Обычный клик по кнопке: FAIL")

            except Exception as e:
                print(f"❌ Ошибка тестирования обычного клика: {e}")
                self.test_results.append("❌ Обычный клик по кнопке: FAIL")

            self.take_screenshot("08_buttons_tested")

        except Exception as e:
            print(f"❌ Ошибка тестирования кнопок: {e}")
            self.test_results.append("❌ Тестирование кнопок: FAIL")

    def test_navigation_elements(self):
        """Тест навигационных элементов"""
        print("\n🧭 === ТЕСТИРОВАНИЕ НАВИГАЦИИ ===")

        # Возвращаемся на главную страницу
        self.driver.get(self.base_url)
        time.sleep(2)

        # Проверяем навигационные элементы
        nav_elements = [
            (By.CSS_SELECTOR, "header", "Заголовок страницы"),
            (By.CSS_SELECTOR, "footer", "Подвал страницы"),
            (By.XPATH, "//div[contains(@class, 'banner')]", "Баннер"),
        ]

        for locator, name in nav_elements:
            element = self.check_element_exists(locator, name, timeout=3)
            if element and element.is_displayed():
                print(f"✅ {name}: видимый")
            elif element:
                print(f"⚠️ {name}: существует, но не видимый")

        # Проверяем ссылки (если есть)
        try:
            links = self.driver.find_elements(By.TAG_NAME, "a")
            visible_links = [link for link in links if link.is_displayed() and link.get_attribute("href")]

            if visible_links:
                print(f"✅ Найдено {len(visible_links)} видимых ссылок")
                self.test_results.append(f"✅ Навигационные ссылки ({len(visible_links)} шт.): PASS")
            else:
                print("⚠️ Видимые ссылки не найдены")
                self.test_results.append("⚠️ Навигационные ссылки: WARNING")

        except Exception as e:
            print(f"❌ Ошибка проверки ссылок: {e}")

    def run_all_tests(self):
        """Запуск всех тестов"""
        print("🚀 НАЧАЛО ТЕСТИРОВАНИЯ UI ЭЛЕМЕНТОВ НА DEMOQA.COM")
        print("=" * 60)

        if not self.setup_driver():
            return False

        try:
            # Запускаем все тесты
            self.test_homepage_elements()
            self.test_elements_page()
            self.test_text_box_functionality()
            self.test_buttons_page()
            self.test_navigation_elements()

            # Финальный скриншот
            self.take_screenshot("09_final_state")

        except Exception as e:
            print(f"❌ Критическая ошибка во время тестирования: {e}")
            self.take_screenshot("error_critical")

        finally:
            self.cleanup()
            self.print_test_summary()

    def print_test_summary(self):
        """Вывод итогового отчета"""
        print("\n" + "=" * 60)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        print("=" * 60)

        passed_tests = [result for result in self.test_results if "PASS" in result]
        failed_tests = [result for result in self.test_results if "FAIL" in result]
        warning_tests = [result for result in self.test_results if "WARNING" in result]

        print(f"✅ Пройдено: {len(passed_tests)}")
        print(f"❌ Провалено: {len(failed_tests)}")
        print(f"⚠️ Предупреждения: {len(warning_tests)}")
        print(f"📊 Всего проверок: {len(self.test_results)}")

        if len(passed_tests) > 0:
            success_rate = (len(passed_tests) / len(self.test_results)) * 100
            print(f"📈 Процент успешности: {success_rate:.1f}%")

        print("\nДЕТАЛИ:")
        for result in self.test_results:
            print(f"  {result}")

        print("\n" + "=" * 60)
        print("🎯 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
        print(f"📸 Скриншоты сохранены в папке: {SCREENSHOTS_DIR}")
        print("=" * 60)

    def cleanup(self):
        """Очистка ресурсов"""
        if self.driver:
            self.driver.quit()
            print("🔒 Браузер закрыт")


if __name__ == "__main__":
    # Запуск тестирования
    ui_test = DemoQAUITest()
    ui_test.run_all_tests()
