"""
🍪 COOKIE CLICKER AI AUTOMATION TEST
Автотест браузерной игры Cookie Clicker с ИИ-оптимизацией стратегии
- Автоматическое кликание по печеньке
- ИИ-анализ лучших покупок
- Динамическая оптимизация стратегии
- Детальная аналитика производительности
- Автосейвы и бэкапы прогресса
"""

import os
import time
import json
import math
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import threading
import queue

# Отключаем SSL проверки
os.environ['WDM_SSL_VERIFY'] = '0'


class CookieClickerAI:
    """ИИ-тестировщик для Cookie Clicker с продвинутой аналитикой"""

    def __init__(self):
        self.driver = None
        self.wait = None
        self.game_url = "https://orteil.dashnet.org/cookieclicker/"

        # Папки для данных
        self.screenshots_dir = "cookie_clicker_screenshots"
        self.data_dir = "cookie_clicker_data"
        self.reports_dir = "cookie_clicker_reports"

        for directory in [self.screenshots_dir, self.data_dir, self.reports_dir]:
            os.makedirs(directory, exist_ok=True)

        # Игровая статистика
        self.game_stats = {
            'start_time': None,
            'total_cookies': 0,
            'cookies_per_second': 0,
            'total_clicks': 0,
            'buildings_bought': {},
            'upgrades_bought': [],
            'achievements_unlocked': [],
            'golden_cookies_clicked': 0,
            'strategy_changes': 0,
            'efficiency_score': 0
        }

        # ИИ настройки
        self.ai_config = {
            'click_frequency': 15,  # кликов в секунду
            'strategy_review_interval': 30,  # секунд
            'efficiency_threshold': 0.7,  # порог эффективности для смены стратегии
            'max_price_ratio': 0.15,  # максимальный процент от текущих cookies для покупки
            'golden_cookie_priority': True,
            'achievement_hunting': True
        }

        # Стратегии покупок
        self.strategies = {
            'balanced': {'buildings': 0.6, 'upgrades': 0.4},
            'buildings_focus': {'buildings': 0.8, 'upgrades': 0.2},
            'upgrades_focus': {'buildings': 0.3, 'upgrades': 0.7},
            'adaptive': {'buildings': 0.5, 'upgrades': 0.5}  # будет адаптироваться
        }

        self.current_strategy = 'adaptive'
        self.click_thread = None
        self.analysis_thread = None
        self.running = False

    def setup_driver(self):
        """Настройка браузера для игрового тестирования"""
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # Отключаем уведомления и звук
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_setting_values.media_stream": 2,
            "profile.managed_default_content_settings.images": 1
        }
        options.add_experimental_option("prefs", prefs)

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.wait = WebDriverWait(self.driver, 20)

            # Скрываем автоматизацию
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            print("✅ Браузер для Cookie Clicker запущен")
            return True

        except Exception as e:
            print(f"❌ Ошибка запуска браузера: {e}")
            return False

    def take_screenshot(self, name):
        """Создание игрового скриншота"""
        if self.driver:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}.png"
            filepath = os.path.join(self.screenshots_dir, filename)
            self.driver.save_screenshot(filepath)
            print(f"📸 Игровой скриншот: {filename}")
            return filepath
        return None

    def load_game(self):
        """Загрузка игры Cookie Clicker"""
        print("🍪 Загружаем Cookie Clicker...")

        try:
            self.driver.get(self.game_url)

            # Ждем загрузки игры
            print("⏳ Ожидание загрузки игры...")

            # Ждем появления главного печенья
            big_cookie = self.wait.until(
                EC.element_to_be_clickable((By.ID, "bigCookie"))
            )

            time.sleep(5)  # Дополнительное время на загрузку ресурсов

            # Проверяем, есть ли язык по умолчанию
            try:
                language_selector = self.driver.find_element(By.ID, "langSelect-EN")
                if language_selector:
                    language_selector.click()
                    time.sleep(2)
            except:
                pass

            # Закрываем всплывающие окна, если есть
            try:
                close_buttons = self.driver.find_elements(By.CSS_SELECTOR, ".close, .closeButton, [onclick*='close']")
                for btn in close_buttons:
                    if btn.is_displayed():
                        btn.click()
                        time.sleep(1)
            except:
                pass

            self.take_screenshot("01_game_loaded")
            print("✅ Cookie Clicker загружен успешно!")

            # Инициализируем статистику
            self.game_stats['start_time'] = datetime.now()

            return True

        except Exception as e:
            print(f"❌ Ошибка загрузки игры: {e}")
            return False

    def get_game_stats(self):
        """Получение текущих игровых статистик"""
        try:
            stats = {}

            # Текущие cookies
            try:
                cookies_text = self.driver.find_element(By.ID, "cookies").text
                # Извлекаем числа из текста (например, "123 cookies")
                import re
                cookies_match = re.search(r'([\d,]+)', cookies_text.replace(',', ''))
                if cookies_match:
                    stats['current_cookies'] = int(cookies_match.group(1))
                else:
                    stats['current_cookies'] = 0
            except:
                stats['current_cookies'] = 0

            # Cookies per second
            try:
                cps_element = self.driver.find_element(By.ID, "cookiesPerSecond")
                cps_text = cps_element.text
                cps_match = re.search(r'([\d,\.]+)', cps_text.replace(',', ''))
                if cps_match:
                    stats['cookies_per_second'] = float(cps_match.group(1))
                else:
                    stats['cookies_per_second'] = 0
            except:
                stats['cookies_per_second'] = 0

            # Обновляем глобальную статистику
            self.game_stats['total_cookies'] = stats['current_cookies']
            self.game_stats['cookies_per_second'] = stats['cookies_per_second']

            return stats

        except Exception as e:
            print(f"⚠️ Ошибка получения статистики: {e}")
            return {'current_cookies': 0, 'cookies_per_second': 0}

    def click_cookie(self, clicks=1):
        """Клик по главному печенью"""
        try:
            big_cookie = self.driver.find_element(By.ID, "bigCookie")

            for _ in range(clicks):
                big_cookie.click()
                self.game_stats['total_clicks'] += 1

                # Небольшая случайная задержка для имитации человека
                time.sleep(random.uniform(0.01, 0.03))

            return True

        except Exception as e:
            print(f"⚠️ Ошибка клика по печенью: {e}")
            return False

    def auto_clicker_thread(self):
        """Поток автоматического кликания"""
        print("🖱️ Автокликер запущен")

        while self.running:
            try:
                # Кликаем с заданной частотой
                clicks_per_batch = max(1, self.ai_config['click_frequency'] // 10)
                self.click_cookie(clicks_per_batch)

                # Проверяем золотые печенья
                if self.ai_config['golden_cookie_priority']:
                    self.click_golden_cookies()

                time.sleep(0.1)  # 10 батчей в секунду

            except Exception as e:
                print(f"⚠️ Ошибка в автокликере: {e}")
                time.sleep(1)

    def click_golden_cookies(self):
        """Поиск и клик по золотым печеньям"""
        try:
            golden_cookies = self.driver.find_elements(By.CSS_SELECTOR, ".shimmer")

            for cookie in golden_cookies:
                if cookie.is_displayed():
                    cookie.click()
                    self.game_stats['golden_cookies_clicked'] += 1
                    print("✨ Кликнули по золотому печенью!")
                    time.sleep(0.1)

        except Exception as e:
            pass  # Не критично, если золотых печений нет

    def analyze_buildings(self):
        """Анализ доступных зданий для покупки"""
        buildings = []

        try:
            # Получаем список всех зданий
            building_elements = self.driver.find_elements(By.CSS_SELECTOR, "#products .product")

            for i, building in enumerate(building_elements):
                try:
                    # Название здания
                    name_element = building.find_element(By.CSS_SELECTOR, ".title")
                    name = name_element.text.strip()

                    # Цена здания
                    price_element = building.find_element(By.CSS_SELECTOR, ".price")
                    price_text = price_element.text.strip()

                    # Извлекаем цену
                    import re
                    price_match = re.search(r'([\d,\.]+)', price_text.replace(',', ''))
                    if price_match:
                        price = float(price_match.group(1))
                    else:
                        continue

                    # Количество зданий
                    owned_element = building.find_element(By.CSS_SELECTOR, ".owned")
                    owned = int(owned_element.text) if owned_element.text.isdigit() else 0

                    # Проверяем доступность
                    is_enabled = "enabled" in building.get_attribute("class")

                    buildings.append({
                        'index': i,
                        'name': name,
                        'price': price,
                        'owned': owned,
                        'enabled': is_enabled,
                        'element': building
                    })

                except Exception as e:
                    continue

            return buildings

        except Exception as e:
            print(f"⚠️ Ошибка анализа зданий: {e}")
            return []

    def analyze_upgrades(self):
        """Анализ доступных улучшений"""
        upgrades = []

        try:
            upgrade_elements = self.driver.find_elements(By.CSS_SELECTOR, "#upgrades .crate:not(.ghosted)")

            for i, upgrade in enumerate(upgrade_elements):
                try:
                    # Получаем информацию об улучшении через title или onclick
                    title = upgrade.get_attribute("title") or upgrade.get_attribute("data-title")
                    onclick = upgrade.get_attribute("onclick")

                    if onclick and "Game.UpgradesById" in onclick:
                        # Извлекаем ID улучшения
                        import re
                        id_match = re.search(r'UpgradesById\[(\d+)\]', onclick)
                        if id_match:
                            upgrade_id = int(id_match.group(1))

                            upgrades.append({
                                'index': i,
                                'id': upgrade_id,
                                'title': title,
                                'element': upgrade,
                                'enabled': upgrade.is_displayed()
                            })

                except Exception as e:
                    continue

            return upgrades

        except Exception as e:
            print(f"⚠️ Ошибка анализа улучшений: {e}")
            return []

    def calculate_building_efficiency(self, building, current_cookies):
        """Расчет эффективности здания"""
        try:
            # Базовая эффективность = производство за секунду / цена
            # Это упрощенный расчет, в реальности нужен более сложный анализ

            # Примерные значения производства для зданий Cookie Clicker
            base_production = {
                'Cursor': 0.1,
                'Grandma': 1,
                'Farm': 8,
                'Mine': 47,
                'Factory': 260,
                'Bank': 1400,
                'Temple': 7800,
                'Wizard tower': 44000,
                'Shipment': 260000,
                'Alchemy lab': 1600000,
                'Portal': 10000000,
                'Time machine': 65000000,
                'Antimatter condenser': 430000000
            }

            # Получаем базовое производство
            base_cps = base_production.get(building['name'], 1)

            # Учитываем количество уже имеющихся зданий (уменьшающаяся эффективность)
            owned_multiplier = 1 / (1 + building['owned'] * 0.1)

            # Рассчитываем эффективность
            efficiency = (base_cps * owned_multiplier) / building['price']

            # Учитываем доступность (можем ли купить)
            affordability = min(1.0, current_cookies / building['price'])

            # Итоговая оценка
            score = efficiency * affordability

            return score

        except Exception as e:
            return 0

    def ai_purchase_decision(self):
        """ИИ принятие решения о покупке"""
        try:
            stats = self.get_game_stats()
            current_cookies = stats['current_cookies']

            if current_cookies < 10:  # Слишком мало cookies
                return None

            # Анализируем здания и улучшения
            buildings = self.analyze_buildings()
            upgrades = self.analyze_upgrades()

            # Фильтруем доступные для покупки здания
            affordable_buildings = [
                b for b in buildings
                if b['enabled'] and b['price'] <= current_cookies * self.ai_config['max_price_ratio']
            ]

            best_building = None
            best_efficiency = 0

            # Находим самое эффективное здание
            for building in affordable_buildings:
                efficiency = self.calculate_building_efficiency(building, current_cookies)
                if efficiency > best_efficiency:
                    best_efficiency = efficiency
                    best_building = building

            # Решаем между зданием и улучшением
            strategy = self.strategies[self.current_strategy]

            # Приоритет зданиям
            if best_building and random.random() < strategy['buildings']:
                return {'type': 'building', 'item': best_building}

            # Приоритет улучшениям
            elif upgrades and random.random() < strategy['upgrades']:
                # Выбираем случайное доступное улучшение
                return {'type': 'upgrade', 'item': random.choice(upgrades)}

            # По умолчанию покупаем здание
            elif best_building:
                return {'type': 'building', 'item': best_building}

            return None

        except Exception as e:
            print(f"⚠️ Ошибка ИИ решения: {e}")
            return None

    def make_purchase(self, decision):
        """Выполнение покупки"""
        try:
            if decision['type'] == 'building':
                building = decision['item']
                building['element'].click()

                # Обновляем статистику
                building_name = building['name']
                if building_name not in self.game_stats['buildings_bought']:
                    self.game_stats['buildings_bought'][building_name] = 0
                self.game_stats['buildings_bought'][building_name] += 1

                print(
                    f"🏗️ Купили здание: {building_name} (всего: {self.game_stats['buildings_bought'][building_name]})")

            elif decision['type'] == 'upgrade':
                upgrade = decision['item']
                upgrade['element'].click()

                # Обновляем статистику
                self.game_stats['upgrades_bought'].append(upgrade.get('title', f"Upgrade {upgrade['id']}"))

                print(f"⬆️ Купили улучшение: {upgrade.get('title', f'ID {upgrade['id']}')}")

            time.sleep(0.5)  # Небольшая пауза после покупки
            return True

        except Exception as e:
            print(f"⚠️ Ошибка покупки: {e}")
            return False

    def ai_analysis_thread(self):
        """Поток ИИ анализа и покупок"""
        print("🧠 ИИ анализатор запущен")

        last_strategy_review = time.time()

        while self.running:
            try:
                # Принимаем решение о покупке
                decision = self.ai_purchase_decision()

                if decision:
                    success = self.make_purchase(decision)
                    if success:
                        # Сохраняем прогресс после важных покупок
                        self.save_game_progress()

                # Периодически пересматриваем стратегию
                if time.time() - last_strategy_review > self.ai_config['strategy_review_interval']:
                    self.review_strategy()
                    last_strategy_review = time.time()

                time.sleep(2)  # Анализ каждые 2 секунды

            except Exception as e:
                print(f"⚠️ Ошибка в ИИ анализаторе: {e}")
                time.sleep(5)

    def review_strategy(self):
        """Пересмотр текущей стратегии"""
        try:
            stats = self.get_game_stats()

            # Простая логика смены стратегии на основе производительности
            if stats['cookies_per_second'] < 100:
                # В начале игры фокусируемся на зданиях
                new_strategy = 'buildings_focus'
            elif stats['cookies_per_second'] < 10000:
                # В средней стадии балансируем
                new_strategy = 'balanced'
            else:
                # В поздней стадии фокусируемся на улучшениях
                new_strategy = 'upgrades_focus'

            if new_strategy != self.current_strategy:
                self.current_strategy = new_strategy
                self.game_stats['strategy_changes'] += 1
                print(f"🎯 Смена стратегии на: {new_strategy}")

        except Exception as e:
            print(f"⚠️ Ошибка пересмотра стратегии: {e}")

    def save_game_progress(self):
        """Сохранение прогресса игры"""
        try:
            # Сохраняем статистику в JSON
            stats_with_time = self.game_stats.copy()
            stats_with_time['current_time'] = datetime.now().isoformat()

            timestamp = time.strftime("%Y%m%d_%H%M%S")
            stats_file = os.path.join(self.data_dir, f"game_stats_{timestamp}.json")

            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats_with_time, f, indent=2, ensure_ascii=False, default=str)

            # Создаем игровой сейв (через консоль браузера)
            try:
                save_data = self.driver.execute_script("return Game.WriteSave(1);")
                if save_data:
                    save_file = os.path.join(self.data_dir, f"cookie_save_{timestamp}.txt")
                    with open(save_file, 'w', encoding='utf-8') as f:
                        f.write(save_data)
                    print(f"💾 Прогресс сохранен: {timestamp}")
            except:
                pass

        except Exception as e:
            print(f"⚠️ Ошибка сохранения: {e}")

    def generate_performance_report(self):
        """Генерация отчета о производительности"""
        try:
            if not self.game_stats['start_time']:
                return

            # Рассчитываем время игры
            play_time = datetime.now() - self.game_stats['start_time']
            play_minutes = play_time.total_seconds() / 60

            # Рассчитываем эффективность
            cookies_per_minute = self.game_stats['total_cookies'] / max(play_minutes, 1)
            clicks_per_minute = self.game_stats['total_clicks'] / max(play_minutes, 1)

            # Создаем отчет
            report = {
                'test_summary': {
                    'start_time': self.game_stats['start_time'].isoformat(),
                    'end_time': datetime.now().isoformat(),
                    'total_play_time_minutes': round(play_minutes, 2),
                    'total_cookies_earned': self.game_stats['total_cookies'],
                    'final_cookies_per_second': self.game_stats['cookies_per_second'],
                    'total_clicks_made': self.game_stats['total_clicks'],
                    'golden_cookies_clicked': self.game_stats['golden_cookies_clicked'],
                    'strategy_changes': self.game_stats['strategy_changes']
                },
                'performance_metrics': {
                    'cookies_per_minute': round(cookies_per_minute, 2),
                    'clicks_per_minute': round(clicks_per_minute, 2),
                    'efficiency_score': round(cookies_per_minute / max(clicks_per_minute, 1), 4),
                    'automation_effectiveness': 'HIGH' if cookies_per_minute > 1000 else 'MEDIUM' if cookies_per_minute > 100 else 'LOW'
                },
                'buildings_purchased': self.game_stats['buildings_bought'],
                'upgrades_count': len(self.game_stats['upgrades_bought']),
                'achievements_unlocked': len(self.game_stats['achievements_unlocked']),
                'ai_configuration': self.ai_config,
                'final_strategy': self.current_strategy
            }

            # Сохраняем отчет
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            report_file = os.path.join(self.reports_dir, f"performance_report_{timestamp}.json")

            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)

            # Печатаем краткий отчет
            self.print_performance_summary(report)

            return report_file

        except Exception as e:
            print(f"⚠️ Ошибка генерации отчета: {e}")
            return None

    def print_performance_summary(self, report):
        """Печать краткого отчета производительности"""
        print("\n" + "=" * 60)
        print("🍪 ОТЧЕТ О ПРОИЗВОДИТЕЛЬНОСТИ COOKIE CLICKER AI")
        print("=" * 60)

        summary = report['test_summary']
        metrics = report['performance_metrics']

        print(f"⏱️ Время игры: {summary['total_play_time_minutes']} минут")
        print(f"🍪 Всего cookies: {summary['total_cookies_earned']:,}")
        print(f"⚡ Cookies/сек: {summary['final_cookies_per_second']:,}")
        print(f"🖱️ Всего кликов: {summary['total_clicks_made']:,}")
        print(f"✨ Золотых cookies: {summary['golden_cookies_clicked']}")

        print(f"\n📊 МЕТРИКИ ПРОИЗВОДИТЕЛЬНОСТИ:")
        print(f"   Cookies в минуту: {metrics['cookies_per_minute']:,}")
        print(f"   Кликов в минуту: {metrics['clicks_per_minute']:,}")
        print(f"   Эффективность: {metrics['efficiency_score']}")
        print(f"   Оценка автоматизации: {metrics['automation_effectiveness']}")

        print(f"\n🏗️ ЗДАНИЯ КУПЛЕНО:")
        for building, count in summary['buildings_purchased'].items():
            print(f"   {building}: {count}")

        print(f"\n⬆️ Улучшений куплено: {summary['upgrades_count']}")
        print(f"🎯 Смен стратегии: {summary['strategy_changes']}")
        print(f"🧠 Финальная стратегия: {summary['final_strategy']}")

        print("=" * 60)

    def run_ai_cookie_test(self, duration_minutes=10):
        """Запуск полного ИИ теста Cookie Clicker"""
        print("🍪 ЗАПУСК AI COOKIE CLICKER ТЕСТА")
        print("=" * 50)
        print(f"⏱️ Продолжительность: {duration_minutes} минут")
        print(f"🧠 ИИ конфигурация: {self.ai_config}")
        print("=" * 50)

        # Настройка браузера
        if not self.setup_driver():
            return False

        try:
            # Загружаем игру
            if not self.load_game():
                return False

            # Запускаем автоматизацию
            self.running = True

            # Создаем потоки для параллельной работы
            self.click_thread = threading.Thread(target=self.auto_clicker_thread, daemon=True)
            self.analysis_thread = threading.Thread(target=self.ai_analysis_thread, daemon=True)

            # Запускаем потоки
            self.click_thread.start()
            self.analysis_thread.start()

            print("🚀 ИИ автоматизация запущена!")

            # Основной цикл мониторинга
            start_time = time.time()
            last_screenshot = time.time()
            last_stats_print = time.time()

            while time.time() - start_time < duration_minutes * 60:
                try:
                    # Периодические скриншоты
                    if time.time() - last_screenshot > 60:  # каждую минуту
                        self.take_screenshot("gameplay")
                        last_screenshot = time.time()

                    # Периодический вывод статистики
                    if time.time() - last_stats_print > 30:  # каждые 30 секунд
                        stats = self.get_game_stats()
                        elapsed = (time.time() - start_time) / 60
                        print(
                            f"📊 [{elapsed:.1f}мин] Cookies: {stats['current_cookies']:,}, CPS: {stats['cookies_per_second']:,}")
                        last_stats_print = time.time()

                    time.sleep(5)  # Основной цикл каждые 5 секунд

                except KeyboardInterrupt:
                    print("\n⏹️ Тест прерван пользователем")
                    break
                except Exception as e:
                    print(f"⚠️ Ошибка в основном цикле: {e}")
                    time.sleep(5)

            # Завершение теста
            self.running = False

            print("\n🏁 Тест завершен!")
            self.take_screenshot("final_result")

            # Генерируем итоговый отчет
            report_file = self.generate_performance_report()

            if report_file:
                print(f"📄 Отчет сохранен: {report_file}")

            return True

        except Exception as e:
            print(f"❌ Критическая ошибка теста: {e}")
            return False

        finally:
            self.running = False
            if self.driver:
                self.driver.quit()
                print("🔒 Браузер закрыт")


def run_interactive_cookie_test():
    """Интерактивный запуск теста с настройками"""
    print("🍪 COOKIE CLICKER AI TESTER")
    print("=" * 40)

    # Создаем тестировщик
    ai_tester = CookieClickerAI()

    print("Настройки теста:")
    print("1. Быстрый тест (5 минут)")
    print("2. Средний тест (15 минут)")
    print("3. Длинный тест (30 минут)")
    print("4. Пользовательские настройки")

    try:
        choice = input("\nВыберите тип теста (1-4): ").strip()

        if choice == "1":
            duration = 5
            ai_tester.ai_config['click_frequency'] = 20
        elif choice == "2":
            duration = 15
            ai_tester.ai_config['click_frequency'] = 15
        elif choice == "3":
            duration = 30
            ai_tester.ai_config['click_frequency'] = 10
        elif choice == "4":
            duration = int(input("Введите продолжительность в минутах: "))
            frequency = int(input("Введите частоту кликов (1-30): "))
            ai_tester.ai_config['click_frequency'] = max(1, min(30, frequency))
        else:
            duration = 10  # По умолчанию

        print(f"\n🎮 Запускаем тест на {duration} минут...")
        print("💡 Совет: откройте диспетчер задач для мониторинга производительности")

        # Запускаем тест
        success = ai_tester.run_ai_cookie_test(duration)

        if success:
            print("\n🎉 Тест завершен успешно!")
            print(f"📸 Скриншоты: {ai_tester.screenshots_dir}")
            print(f"📊 Данные: {ai_tester.data_dir}")
            print(f"📄 Отчеты: {ai_tester.reports_dir}")
        else:
            print("\n❌ Тест завершен с ошибками")

    except KeyboardInterrupt:
        print("\n⏹️ Тест прерван пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")


if __name__ == "__main__":
    run_interactive_cookie_test()
