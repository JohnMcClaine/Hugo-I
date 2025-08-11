"""
🌍 FORM FILLING TEST WITH PROXY/TOR GEOLOCATION SIMULATION
Автотест заполнения формы с имитацией трафика из разных стран
- Ручной ввод данных
- Копирование/вставка данных
- Ротация прокси для смены геолокации
- Интеграция с Tor для анонимности
"""

import os
import time
import random
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pyperclip  # Для работы с буфером обмена

# Отключаем SSL проверки
os.environ['WDM_SSL_VERIFY'] = '0'


class GeoProxyFormTester:
    """Класс для тестирования форм с прокси и геолокацией"""

    def __init__(self):
        self.driver = None
        self.wait = None
        self.current_proxy = None
        self.current_country = None
        self.screenshots_dir = "geo_form_screenshots"
        self.test_results = []

        # Создаем папки
        os.makedirs(self.screenshots_dir, exist_ok=True)

        # Список бесплатных прокси для тестирования (в реальности используйте платные)
        self.proxy_pool = [
            {
                "ip": "47.74.152.29",
                "port": "8888",
                "country": "US",
                "name": "United States"
            },
            {
                "ip": "85.208.96.205",
                "port": "8080",
                "country": "UK",
                "name": "United Kingdom"
            },
            {
                "ip": "103.149.162.195",
                "port": "80",
                "country": "IN",
                "name": "India"
            },
            {
                "ip": "200.105.215.18",
                "port": "33630",
                "country": "BR",
                "name": "Brazil"
            },
        ]

        # Данные для заполнения формы по странам
        self.form_data_by_country = {
            "US": {
                "first_name": "John",
                "last_name": "Smith",
                "email": "john.smith.us@example.com",
                "phone": "+1 (555) 123-4567",
                "address": "123 Main Street, New York, NY 10001",
                "company": "American Corp LLC",
                "zip_code": "10001",
                "city": "New York"
            },
            "UK": {
                "first_name": "James",
                "last_name": "Wilson",
                "email": "james.wilson.uk@example.com",
                "phone": "+44 20 7946 0958",
                "address": "45 Baker Street, London, W1U 6TW",
                "company": "British Ltd",
                "zip_code": "W1U 6TW",
                "city": "London"
            },
            "IN": {
                "first_name": "Raj",
                "last_name": "Patel",
                "email": "raj.patel.in@example.com",
                "phone": "+91 98765 43210",
                "address": "MG Road, Bangalore, Karnataka 560001",
                "company": "Indian Tech Solutions",
                "zip_code": "560001",
                "city": "Bangalore"
            },
            "BR": {
                "first_name": "Carlos",
                "last_name": "Silva",
                "email": "carlos.silva.br@example.com",
                "phone": "+55 11 99999-8888",
                "address": "Av. Paulista, 1000, São Paulo, SP 01310-100",
                "company": "Brasil Empresa Ltda",
                "zip_code": "01310-100",
                "city": "São Paulo"
            }
        }

        # Настройки Tor (для более продвинутой анонимности)
        self.tor_config = {
            "tor_binary": "C:/Program Files/Tor Browser/Browser/firefox.exe",  # Путь к Tor браузеру
            "tor_profile": "C:/Program Files/Tor Browser/Browser/TorBrowser/Data/Browser/profile.default",
            "socks_port": 9150
        }

    def setup_driver_with_proxy(self, proxy_info=None, use_tor=False):
        """Настройка драйвера с прокси или Tor"""
        options = Options()

        # Базовые настройки для имитации реального пользователя
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # Случайный User-Agent
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        options.add_argument(f"--user-agent={random.choice(user_agents)}")

        if use_tor:
            # Настройка для Tor
            print("🧅 Настройка Tor...")
            options.add_argument("--proxy-server=socks5://127.0.0.1:9150")
            # Дополнительные настройки для Tor
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")

        elif proxy_info:
            # Настройка обычного прокси
            proxy_url = f"http://{proxy_info['ip']}:{proxy_info['port']}"
            options.add_argument(f"--proxy-server={proxy_url}")
            print(f"🌍 Подключение через прокси: {proxy_info['name']} ({proxy_info['ip']}:{proxy_info['port']})")

            # Устанавливаем фейковую геолокацию
            if proxy_info['country'] in ['US']:
                prefs = {
                    "profile.default_content_setting_values.geolocation": 1,
                    "profile.managed_default_content_settings.geolocation": 1
                }
                options.add_experimental_option("prefs", prefs)

        # Отключаем уведомления
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_setting_values.media_stream": 2,
        }
        options.add_experimental_option("prefs", prefs)

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.wait = WebDriverWait(self.driver, 15)

            # Скрываем автоматизацию
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            # Сохраняем текущие настройки
            self.current_proxy = proxy_info
            self.current_country = proxy_info['country'] if proxy_info else 'TOR'

            print(f"✅ Браузер запущен {'с Tor' if use_tor else 'с прокси' if proxy_info else 'без прокси'}")
            return True

        except Exception as e:
            print(f"❌ Ошибка запуска браузера: {e}")
            return False

    def verify_ip_and_location(self):
        """Проверка IP адреса и геолокации"""
        print("\n🔍 Проверка IP и геолокации...")

        try:
            # Проверяем IP через несколько сервисов
            ip_services = [
                "https://httpbin.org/ip",
                "https://api.ipify.org?format=json",
                "https://ipinfo.io/json"
            ]

            for service in ip_services:
                try:
                    self.driver.get(service)
                    time.sleep(3)

                    # Получаем JSON ответ
                    body = self.driver.find_element(By.TAG_NAME, "body").text

                    if "httpbin.org" in service:
                        import json
                        data = json.loads(body)
                        ip = data.get("origin", "Unknown")
                        print(f"📍 IP (httpbin): {ip}")

                    elif "ipify" in service:
                        data = json.loads(body)
                        ip = data.get("ip", "Unknown")
                        print(f"📍 IP (ipify): {ip}")

                    elif "ipinfo.io" in service:
                        data = json.loads(body)
                        ip = data.get("ip", "Unknown")
                        country = data.get("country", "Unknown")
                        city = data.get("city", "Unknown")
                        region = data.get("region", "Unknown")

                        print(f"📍 IP (ipinfo): {ip}")
                        print(f"🌍 Страна: {country}")
                        print(f"🏙️ Город: {city}, {region}")

                        # Проверяем соответствие ожидаемой стране
                        if self.current_proxy and country != self.current_proxy.get('country'):
                            print(f"⚠️ Предупреждение: ожидали {self.current_proxy['country']}, получили {country}")
                        else:
                            print("✅ Геолокация соответствует прокси")

                        break

                except Exception as e:
                    print(f"⚠️ Ошибка с сервисом {service}: {e}")
                    continue

            self.take_screenshot("ip_verification")
            return True

        except Exception as e:
            print(f"❌ Ошибка проверки IP: {e}")
            return False

    def take_screenshot(self, name):
        """Создание скриншота"""
        if self.driver:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            country = self.current_country or "unknown"
            filename = f"{name}_{country}_{timestamp}.png"
            filepath = os.path.join(self.screenshots_dir, filename)
            self.driver.save_screenshot(filepath)
            print(f"📸 Скриншот: {filename}")
            return filepath
        return None

    def human_type(self, element, text, typing_speed='normal'):
        """Имитация человеческого ввода с разной скоростью"""
        speeds = {
            'slow': (0.1, 0.3),
            'normal': (0.05, 0.15),
            'fast': (0.02, 0.08),
            'very_fast': (0.01, 0.03)
        }

        min_delay, max_delay = speeds.get(typing_speed, speeds['normal'])

        element.clear()
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(min_delay, max_delay))

    def copy_paste_data(self, element, text):
        """Копирование и вставка данных через буфер обмена"""
        print(f"📋 Копируем и вставляем: {text[:30]}...")

        # Копируем в буфер обмена
        pyperclip.copy(text)

        # Очищаем поле
        element.clear()
        time.sleep(0.2)

        # Имитируем Ctrl+V
        element.send_keys(Keys.CONTROL + 'v')
        time.sleep(0.5)

    def fill_form_with_mixed_input(self, form_data):
        """Заполнение формы смешанными методами ввода"""
        print(f"\n📝 Заполнение формы для страны: {self.current_country}")

        # Определяем методы ввода для каждого поля
        input_methods = {
            'first_name': 'type_slow',
            'last_name': 'type_normal',
            'email': 'copy_paste',
            'phone': 'type_fast',
            'address': 'copy_paste',
            'company': 'type_normal',
            'zip_code': 'type_fast',
            'city': 'type_normal'
        }

        # Селекторы полей формы (адаптируйте под конкретный сайт)
        field_selectors = {
            'first_name': "input[name='firstName'], input[id*='first'], input[placeholder*='First']",
            'last_name': "input[name='lastName'], input[id*='last'], input[placeholder*='Last']",
            'email': "input[type='email'], input[name='email'], input[id*='email']",
            'phone': "input[type='tel'], input[name='phone'], input[id*='phone']",
            'address': "textarea[name='address'], input[name='address'], input[id*='address']",
            'company': "input[name='company'], input[id*='company'], input[placeholder*='Company']",
            'zip_code': "input[name='zip'], input[name='postal'], input[id*='zip']",
            'city': "input[name='city'], input[id*='city'], input[placeholder*='City']"
        }

        filled_fields = 0

        for field_name, field_value in form_data.items():
            if field_name in field_selectors:
                try:
                    # Ищем поле
                    selectors = field_selectors[field_name].split(', ')
                    element = None

                    for selector in selectors:
                        try:
                            element = self.wait.until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                            break
                        except:
                            continue

                    if not element:
                        print(f"⚠️ Поле {field_name} не найдено")
                        continue

                    # Прокручиваем к элементу
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    time.sleep(0.5)

                    # Применяем метод ввода
                    input_method = input_methods.get(field_name, 'type_normal')

                    if input_method == 'copy_paste':
                        self.copy_paste_data(element, field_value)
                    elif input_method.startswith('type_'):
                        speed = input_method.replace('type_', '')
                        self.human_type(element, field_value, speed)

                    filled_fields += 1
                    print(f"✅ {field_name}: {field_value}")

                    # Случайная пауза между полями
                    time.sleep(random.uniform(0.5, 2.0))

                except Exception as e:
                    print(f"❌ Ошибка заполнения {field_name}: {e}")
                    continue

        print(f"📊 Заполнено полей: {filled_fields}/{len(form_data)}")
        return filled_fields > 0

    def test_form_with_proxy(self, proxy_info, target_url):
        """Тестирование формы с конкретным прокси"""
        print(f"\n🌍 === ТЕСТИРОВАНИЕ С ПРОКСИ {proxy_info['name']} ===")

        # Настраиваем браузер с прокси
        if not self.setup_driver_with_proxy(proxy_info):
            return False

        try:
            # Проверяем IP и локацию
            self.verify_ip_and_location()

            # Переходим на тестовый сайт
            print(f"🌐 Переходим на: {target_url}")
            self.driver.get(target_url)
            time.sleep(3)

            self.take_screenshot("01_page_loaded")

            # Получаем данные для текущей страны
            form_data = self.form_data_by_country.get(
                proxy_info['country'],
                self.form_data_by_country['US']  # По умолчанию US
            )

            # Заполняем форму
            success = self.fill_form_with_mixed_input(form_data)

            if success:
                self.take_screenshot("02_form_filled")

                # Ищем и нажимаем кнопку отправки
                submit_buttons = [
                    "button[type='submit']",
                    "input[type='submit']",
                    "button:contains('Submit')",
                    "button:contains('Send')",
                    ".submit-btn",
                    "#submit"
                ]

                for selector in submit_buttons:
                    try:
                        if 'contains' not in selector:
                            submit_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                        else:
                            # XPath для contains
                            xpath = selector.replace('button:contains', '//button[contains(text()').replace("')", "')]")
                            submit_btn = self.driver.find_element(By.XPATH, xpath)

                        if submit_btn.is_displayed() and submit_btn.is_enabled():
                            print("📤 Отправляем форму...")

                            # Прокручиваем к кнопке
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_btn)
                            time.sleep(1)

                            # Нажимаем кнопку
                            submit_btn.click()
                            time.sleep(3)

                            self.take_screenshot("03_form_submitted")
                            print("✅ Форма отправлена успешно!")

                            break
                    except Exception as e:
                        continue

                self.test_results.append({
                    'country': proxy_info['name'],
                    'proxy': f"{proxy_info['ip']}:{proxy_info['port']}",
                    'success': True,
                    'fields_filled': len(form_data)
                })

            else:
                print("❌ Не удалось заполнить форму")
                self.test_results.append({
                    'country': proxy_info['name'],
                    'proxy': f"{proxy_info['ip']}:{proxy_info['port']}",
                    'success': False,
                    'fields_filled': 0
                })

            return success

        except Exception as e:
            print(f"❌ Критическая ошибка: {e}")
            self.take_screenshot("error_critical")
            return False

        finally:
            if self.driver:
                self.driver.quit()
                print("🔒 Браузер закрыт")

    def test_form_with_tor(self, target_url):
        """Тестирование формы через Tor"""
        print(f"\n🧅 === ТЕСТИРОВАНИЕ ЧЕРЕЗ TOR ===")

        # Проверяем, запущен ли Tor
        print("🔍 Проверяем доступность Tor...")

        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', 9150))
            sock.close()

            if result != 0:
                print("❌ Tor не запущен на порту 9150")
                print("💡 Запустите Tor Browser вручную перед тестированием")
                return False

        except Exception as e:
            print(f"❌ Ошибка проверки Tor: {e}")
            return False

        # Настраиваем браузер с Tor
        if not self.setup_driver_with_proxy(use_tor=True):
            return False

        try:
            # Проверяем IP через Tor
            print("🧅 Проверяем IP через Tor...")
            self.verify_ip_and_location()

            # Переходим на тестовый сайт
            print(f"🌐 Переходим на: {target_url}")
            self.driver.get(target_url)
            time.sleep(5)  # Tor может быть медленнее

            self.take_screenshot("tor_01_page_loaded")

            # Используем случайные данные для Tor
            countries = list(self.form_data_by_country.keys())
            random_country = random.choice(countries)
            form_data = self.form_data_by_country[random_country]

            print(f"🎲 Используем данные для: {random_country}")

            # Заполняем форму
            success = self.fill_form_with_mixed_input(form_data)

            if success:
                self.take_screenshot("tor_02_form_filled")
                print("✅ Форма заполнена через Tor!")

                self.test_results.append({
                    'country': 'TOR Network',
                    'proxy': 'SOCKS5://127.0.0.1:9150',
                    'success': True,
                    'fields_filled': len(form_data)
                })

            return success

        except Exception as e:
            print(f"❌ Ошибка тестирования через Tor: {e}")
            return False

        finally:
            if self.driver:
                self.driver.quit()
                print("🔒 Браузер закрыт")

    def run_comprehensive_geo_test(self, target_url):
        """Запуск полного тестирования с ротацией прокси"""
        print("🌍 ЗАПУСК КОМПЛЕКСНОГО ГЕО-ТЕСТИРОВАНИЯ")
        print("=" * 60)
        print(f"🎯 Целевой URL: {target_url}")
        print(f"🌐 Прокси в пуле: {len(self.proxy_pool)}")
        print("=" * 60)

        start_time = time.time()

        # Тестируем каждый прокси
        for i, proxy in enumerate(self.proxy_pool, 1):
            print(f"\n🔄 ЭТАП {i}/{len(self.proxy_pool)}")
            print("-" * 40)

            success = self.test_form_with_proxy(proxy, target_url)

            if not success:
                print(f"⚠️ Прокси {proxy['name']} не работает")

            # Пауза между прокси
            if i < len(self.proxy_pool):
                print("⏳ Пауза перед следующим прокси...")
                time.sleep(random.uniform(3, 8))

        # Тестируем через Tor (опционально)
        print(f"\n🔄 ЭТАП {len(self.proxy_pool) + 1}: TOR")
        print("-" * 40)

        try:
            self.test_form_with_tor(target_url)
        except Exception as e:
            print(f"⚠️ Tor тест пропущен: {e}")

        # Итоговый отчет
        self.print_test_report(time.time() - start_time)

    def print_test_report(self, total_time):
        """Печать итогового отчета"""
        print("\n" + "=" * 60)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ГЕО-ТЕСТИРОВАНИЯ")
        print("=" * 60)

        successful_tests = [r for r in self.test_results if r['success']]
        failed_tests = [r for r in self.test_results if not r['success']]

        print(f"✅ Успешных тестов: {len(successful_tests)}")
        print(f"❌ Неуспешных тестов: {len(failed_tests)}")
        print(f"📊 Всего тестов: {len(self.test_results)}")
        print(f"⏱️ Общее время: {total_time:.1f} секунд")

        if len(successful_tests) > 0:
            success_rate = (len(successful_tests) / len(self.test_results)) * 100
            print(f"📈 Процент успешности: {success_rate:.1f}%")

        print(f"\n📋 ДЕТАЛИ ПО СТРАНАМ:")
        for result in self.test_results:
            status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
            print(f"  🌍 {result['country']}: {status}")
            print(f"     📡 Прокси: {result['proxy']}")
            print(f"     📝 Полей заполнено: {result['fields_filled']}")

        print(f"\n📸 Скриншоты сохранены в: {self.screenshots_dir}")
        print("=" * 60)

        # Рекомендации
        if len(successful_tests) == len(self.test_results):
            print("🎉 ОТЛИЧНО! Все тесты прошли успешно!")
        elif len(successful_tests) > len(failed_tests):
            print("👍 ХОРОШО! Большинство тестов успешны")
        else:
            print("⚠️ ВНИМАНИЕ! Много неуспешных тестов")
            print("💡 Рекомендации:")
            print("   - Проверьте работоспособность прокси")
            print("   - Убедитесь, что форма доступна")
            print("   - Проверьте селекторы полей формы")


# Функция для тестирования конкретных сайтов
def create_test_scenarios():
    """Создание сценариев тестирования для популярных сайтов"""

    scenarios = [
        {
            "name": "Contact Form Test",
            "url": "https://www.selenium.dev/selenium/web/web-form.html",
            "description": "Тестовая форма Selenium"
        },
        {
            "name": "DemoQA Practice Form",
            "url": "https://demoqa.com/automation-practice-form",
            "description": "Практическая форма DemoQA"
        },
        {
            "name": "HTTPBin Forms",
            "url": "https://httpbin.org/forms/post",
            "description": "HTTPBin тестовая форма"
        }
    ]

    return scenarios


if __name__ == "__main__":
    print("🌍 GEO PROXY FORM TESTER v1.0")
    print("Тестирование форм с ротацией прокси и геолокацией")
    print("=" * 60)

    # Создаем тестировщик
    geo_tester = GeoProxyFormTester()

    # Выбираем сценарий тестирования
    scenarios = create_test_scenarios()

    print("Доступные сценарии тестирования:")
    for i, scenario in enumerate(scenarios, 1):
        print(f"{i}. {scenario['name']} - {scenario['description']}")

    try:
        choice = input(f"\nВыберите сценарий (1-{len(scenarios)}) или нажмите Enter для первого: ").strip()
        if not choice:
            choice = "1"

        scenario_index = int(choice) - 1
        if 0 <= scenario_index < len(scenarios):
            selected_scenario = scenarios[scenario_index]
            print(f"\n✅ Выбран сценарий: {selected_scenario['name']}")

            # Запускаем тестирование
            geo_tester.run_comprehensive_geo_test(selected_scenario['url'])

        else:
            print("❌ Неверный выбор сценария")

    except KeyboardInterrupt:
        print("\n⏹️ Тестирование прервано пользователем")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

    print("\n🎯 Тестирование завершено!")
