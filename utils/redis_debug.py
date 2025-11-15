#!/usr/bin/env python3
"""
Redis Debugging and Monitoring Tool for Huey Tasks

Цей скрипт допомагає дебажити Redis та Huey:
- Переглядати всі ключі в Redis
- Переглядати черги Huey
- Переглядати статистику
- Моніторити таски в реальному часі
"""
import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Any

try:
    import redis
except ImportError:
    print("Потрібно встановити redis: pip install redis")
    sys.exit(1)

# Налаштування
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
HUEY_PREFIX = 'huey'  # Префікс для Huey


class RedisDebugger:
    """
    Клас для дебагу Redis та Huey.

    Дозволяє моніторити та аналізувати стан Redis, черги Huey, таски та результати.

    Приклади використання:

    ```python
    # Базове використання з налаштуваннями за замовчуванням
    debugger = RedisDebugger()

    # Перевірка підключення
    if debugger.ping():
        print("Redis доступний")

    # Показати інформацію про черги
    debugger.show_queue_info()

    # Показати статистику
    debugger.show_statistics()

    # Отримати всі ключі Huey
    keys = debugger.get_all_keys('huey.*')
    print(f"Знайдено {len(keys)} ключів")

    # Моніторити таски протягом 60 секунд
    debugger.monitor_tasks(duration=60)

    # Показати деталі конкретного ключа
    debugger.show_key_details('huey.main.queue')
    ```

    ```python
    # Використання з кастомними налаштуваннями Redis
    debugger = RedisDebugger(host='192.168.1.100', port=6380)

    # Отримати ключі, згруповані за типом
    keys_by_type = debugger.get_huey_keys()
    print(f"Черги: {len(keys_by_type['queue'])}")
    print(f"Результати: {len(keys_by_type['result'])}")
    ```

    ```python
    # Програмне використання (без інтерактивного меню)
    from utils.redis_debug import RedisDebugger

    debugger = RedisDebugger()

    # Перевірити стан черг
    keys_by_type = debugger.get_huey_keys()
    queue_keys = keys_by_type['queue']

    for queue_key in queue_keys:
        length = debugger.redis_client.llen(queue_key)
        if length > 0:
            print(f"Черга {queue_key} має {length} тасок")
    ```
    """

    def __init__(self, host: str = REDIS_HOST, port: int = REDIS_PORT):
        """
        Ініціалізує RedisDebugger з підключенням до Redis.

        Args:
            host: Хост Redis сервера (за замовчуванням з REDIS_HOST або 'localhost')
            port: Порт Redis сервера (за замовчуванням з REDIS_PORT або 6379)

        Приклади:
            ```python
            # Підключення до локального Redis
            debugger = RedisDebugger()

            # Підключення до віддаленого Redis
            debugger = RedisDebugger(host='redis.example.com', port=6379)

            # Використання змінних оточення
            import os
            os.environ['REDIS_HOST'] = '192.168.1.100'
            os.environ['REDIS_PORT'] = '6380'
            debugger = RedisDebugger()  # Використає значення з оточення
            ```
        """
        self.redis_client = redis.Redis(host=host, port=port, decode_responses=True)
        self.huey_prefix = HUEY_PREFIX

    def ping(self) -> bool:
        """
        Перевірка підключення до Redis.

        Returns:
            bool: True якщо підключення успішне, False якщо є помилка

        Приклади:
            ```python
            debugger = RedisDebugger()

            if debugger.ping():
                print("✅ Redis доступний")
                # Продовжити роботу
            else:
                print("❌ Не вдалося підключитися до Redis")
                sys.exit(1)
            ```

            ```python
            # Використання в скрипті для перевірки перед роботою
            debugger = RedisDebugger()
            if not debugger.ping():
                raise ConnectionError("Redis недоступний")
            ```
        """
        try:
            response = self.redis_client.ping()
            print(f"✅ Redis підключений: {response}")
            return True
        except Exception as e:
            print(f"❌ Помилка підключення до Redis: {e}")
            return False

    def get_all_keys(self, pattern: str = None) -> List[str]:
        """
        Отримати всі ключі Redis (або за паттерном).

        Args:
            pattern: Опціональний паттерн для фільтрації ключів (використовує Redis KEYS)
                    Якщо None, повертає всі ключі

        Returns:
            List[str]: Список ключів, що відповідають паттерну

        Приклади:
            ```python
            debugger = RedisDebugger()

            # Отримати всі ключі
            all_keys = debugger.get_all_keys()
            print(f"Всього ключів: {len(all_keys)}")

            # Отримати тільки ключі Huey
            huey_keys = debugger.get_all_keys('huey.*')
            print(f"Ключів Huey: {len(huey_keys)}")

            # Отримати ключі конкретної черги
            queue_keys = debugger.get_all_keys('huey.main.*')
            for key in queue_keys:
                print(key)

            # Отримати ключі результатів
            result_keys = debugger.get_all_keys('huey.results.*')
            print(f"Результатів: {len(result_keys)}")
            ```

            ```python
            # Перевірити наявність конкретного ключа
            debugger = RedisDebugger()
            keys = debugger.get_all_keys('huey.main.queue')
            if keys:
                print("Черга існує")
            ```
        """
        if pattern:
            return self.redis_client.keys(pattern)
        return self.redis_client.keys('*')

    def get_huey_keys(self) -> Dict[str, List[str]]:
        """
        Отримати всі ключі Huey, згруповані за типом.

        Returns:
            Dict[str, List[str]]: Словник з ключами, згрупованими за типами:
                - 'queue': ключі черг (містять '.main.')
                - 'result': ключі результатів (містять '.results.')
                - 'schedule': ключі розкладу (містять '.schedule.')
                - 'lock': ключі блокувань (містять '.lock.')
                - 'signal': ключі сигналів (містять '.signal.')
                - 'other': інші ключі Huey

        Приклади:
            ```python
            debugger = RedisDebugger()
            keys_by_type = debugger.get_huey_keys()

            # Перевірити кількість тасок в чергах
            queue_keys = keys_by_type['queue']
            print(f"Знайдено {len(queue_keys)} черг")

            for queue_key in queue_keys:
                length = debugger.redis_client.llen(queue_key)
                print(f"{queue_key}: {length} тасок")

            # Перевірити результати
            result_keys = keys_by_type['result']
            print(f"Знайдено {len(result_keys)} результатів")

            # Перевірити заплановані таски
            schedule_keys = keys_by_type['schedule']
            if schedule_keys:
                print(f"Заплановано {len(schedule_keys)} тасок")
            ```

            ```python
            # Отримати статистику по типах
            debugger = RedisDebugger()
            keys_by_type = debugger.get_huey_keys()

            stats = {
                'queues': len(keys_by_type['queue']),
                'results': len(keys_by_type['result']),
                'scheduled': len(keys_by_type['schedule']),
                'locks': len(keys_by_type['lock']),
                'signals': len(keys_by_type['signal']),
                'other': len(keys_by_type['other'])
            }

            for key_type, count in stats.items():
                print(f"{key_type}: {count}")
            ```
        """
        all_keys = self.get_all_keys(f'{self.huey_prefix}.*')

        keys_by_type = {
            'queue': [],
            'result': [],
            'schedule': [],
            'lock': [],
            'signal': [],
            'other': []
        }

        for key in all_keys:
            if '.main.' in key:
                keys_by_type['queue'].append(key)
            elif '.results.' in key:
                keys_by_type['result'].append(key)
            elif '.schedule.' in key:
                keys_by_type['schedule'].append(key)
            elif '.lock.' in key:
                keys_by_type['lock'].append(key)
            elif '.signal.' in key:
                keys_by_type['signal'].append(key)
            else:
                keys_by_type['other'].append(key)

        return keys_by_type

    def show_queue_info(self):
        """
        Показати інформацію про черги Huey в консолі.

        Виводить:
            - Список всіх черг з кількістю тасок
            - Перші 3 таски з кожної черги
            - Список результатів (перші 10)

        Приклади:
            ```python
            debugger = RedisDebugger()
            debugger.show_queue_info()
            # Виведе:
            # ============================================================
            # 📋 ІНФОРМАЦІЯ ПРО ЧЕРГИ HUEY
            # ============================================================
            #
            # 🔵 Черги (1):
            #   • huey.main.queue: 5 тасок в черзі
            #     1. tasks.test_task
            #     2. tasks.process_data
            #     3. tasks.send_email
            #
            # ✅ Результати (3):
            #   • huey.results.abc123: {"status": "success", ...}
            ```

            ```python
            # Використання в скрипті для моніторингу
            import time

            debugger = RedisDebugger()
            while True:
                debugger.show_queue_info()
                time.sleep(10)  # Оновлювати кожні 10 секунд
            ```
        """
        print("\n" + "="*60)
        print("📋 ІНФОРМАЦІЯ ПРО ЧЕРГИ HUEY")
        print("="*60)

        keys_by_type = self.get_huey_keys()

        # Черги
        if keys_by_type['queue']:
            print(f"\n🔵 Черги ({len(keys_by_type['queue'])}):")
            for key in keys_by_type['queue']:
                length = self.redis_client.llen(key)
                print(f"  • {key}: {length} тасок в черзі")
                if length > 0:
                    # Показати перші 3 таски
                    tasks = self.redis_client.lrange(key, 0, 2)
                    for i, task in enumerate(tasks, 1):
                        try:
                            task_data = json.loads(task)
                            task_name = task_data.get('task', 'unknown')
                            print(f"    {i}. {task_name}")
                        except:
                            print(f"    {i}. {task[:50]}...")
        else:
            print("\n🔵 Черги: порожні")

        # Результати
        if keys_by_type['result']:
            print(f"\n✅ Результати ({len(keys_by_type['result'])}):")
            for key in keys_by_type['result'][:10]:  # Показати перші 10
                result = self.redis_client.get(key)
                if result:
                    try:
                        result_data = json.loads(result)
                        print(f"  • {key}: {result_data.get('result', 'N/A')[:50]}")
                    except:
                        print(f"  • {key}: {result[:50]}")
        else:
            print("\n✅ Результати: немає")

    def show_statistics(self):
        """
        Показати статистику Redis в консолі.

        Виводить:
            - Використання пам'яті (поточне та пікове)
            - Кількість ключів (всього та Huey)
            - Кількість підключених клієнтів
            - Статистику команд (всього та на секунду)

        Приклади:
            ```python
            debugger = RedisDebugger()
            debugger.show_statistics()
            # Виведе:
            # ============================================================
            # 📊 СТАТИСТИКА REDIS
            # ============================================================
            #
            # 💾 Пам'ять:
            #   • Використано: 2.5M
            #   • Пік використання: 3.1M
            #
            # 📈 Ключі:
            #   • Всього ключів: 150
            #   • Huey ключів: 45
            #
            # 🔌 Підключення:
            #   • Підключених клієнтів: 3
            #
            # ⚡ Команди:
            #   • Всього команд: 12345
            #   • Команд/сек: 25
            ```

            ```python
            # Зберегти статистику в файл
            import sys

            debugger = RedisDebugger()
            original_stdout = sys.stdout
            with open('redis_stats.txt', 'w') as f:
                sys.stdout = f
                debugger.show_statistics()
            sys.stdout = original_stdout
            ```
        """
        print("\n" + "="*60)
        print("📊 СТАТИСТИКА REDIS")
        print("="*60)

        info = self.redis_client.info()

        print(f"\n💾 Пам'ять:")
        print(f"  • Використано: {info.get('used_memory_human', 'N/A')}")
        print(f"  • Пік використання: {info.get('used_memory_peak_human', 'N/A')}")

        print(f"\n📈 Ключі:")
        print(f"  • Всього ключів: {info.get('db0', {}).get('keys', 0)}")
        print(f"  • Huey ключів: {len(self.get_all_keys(f'{self.huey_prefix}.*'))}")

        print(f"\n🔌 Підключення:")
        print(f"  • Підключених клієнтів: {info.get('connected_clients', 0)}")

        print(f"\n⚡ Команди:")
        print(f"  • Всього команд: {info.get('total_commands_processed', 0)}")
        print(f"  • Команд/сек: {info.get('instantaneous_ops_per_sec', 0)}")

    def monitor_tasks(self, duration: int = 30):
        """
        Моніторити таски в реальному часі.

        Відстежує зміни в ключах Huey (нові та видалені) протягом вказаного часу.
        Оновлює інформацію кожну секунду.

        Args:
            duration: Тривалість моніторингу в секундах (за замовчуванням 30)

        Приклади:
            ```python
            debugger = RedisDebugger()

            # Моніторити протягом 30 секунд (за замовчуванням)
            debugger.monitor_tasks()

            # Моніторити протягом 60 секунд
            debugger.monitor_tasks(duration=60)

            # Моніторити протягом 5 хвилин
            debugger.monitor_tasks(duration=300)
            ```

            ```python
            # Моніторити до ручного зупинення (Ctrl+C)
            debugger = RedisDebugger()
            try:
                debugger.monitor_tasks(duration=999999)  # Дуже довгий час
            except KeyboardInterrupt:
                print("Моніторинг зупинено користувачем")
            ```

            Приклад виводу:
            ```
            ============================================================
            👀 МОНІТОРИНГ ТАСОК (протягом 30 секунд)
            ============================================================

            [14:23:15] ✨ Нові ключі:
              • huey.main.queue
            [14:23:16] ✨ Нові ключі:
              • huey.results.abc123
            [14:23:20] 🗑️  Видалені ключі:
              • huey.results.abc123
            ```
        """
        print("\n" + "="*60)
        print(f"👀 МОНІТОРИНГ ТАСОК (протягом {duration} секунд)")
        print("="*60)
        print("Натисніть Ctrl+C для зупинки\n")

        start_time = time.time()
        initial_keys = set(self.get_all_keys(f'{self.huey_prefix}.*'))

        try:
            while time.time() - start_time < duration:
                current_keys = set(self.get_all_keys(f'{self.huey_prefix}.*'))

                # Нові ключі
                new_keys = current_keys - initial_keys
                if new_keys:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✨ Нові ключі:")
                    for key in new_keys:
                        print(f"  • {key}")

                # Видалені ключі
                deleted_keys = initial_keys - current_keys
                if deleted_keys:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🗑️  Видалені ключі:")
                    for key in deleted_keys:
                        print(f"  • {key}")

                # Оновити початкові ключі
                initial_keys = current_keys

                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n⏹️  Моніторинг зупинено")

    def clear_all_huey_data(self):
        """
        ⚠️ ОЧИСТИТИ ВСІ ДАНІ HUEY (використовуйте обережно!).

        Видаляє всі ключі, що починаються з префіксу Huey.
        Потрібне підтвердження через інтерактивний ввід.

        Увага: Ця операція незворотна! Видалить:
            - Всі черги та таски
            - Всі результати
            - Всі заплановані таски
            - Всі блокування та сигнали

        Приклади:
            ```python
            debugger = RedisDebugger()

            # Інтерактивне очищення (потрібне підтвердження)
            debugger.clear_all_huey_data()
            # Запитає: "Ви впевнені? (yes/no): "
            # Якщо ввести "yes" - видалить дані
            # Якщо ввести щось інше - скасує операцію
            ```

            ```python
            # Програмне очищення (без підтвердження)
            # Увага: використовуйте тільки в тестах або скриптах!
            debugger = RedisDebugger()
            keys = debugger.get_all_keys('huey.*')
            if keys:
                debugger.redis_client.delete(*keys)
                print(f"Видалено {len(keys)} ключів")
            ```

            ```python
            # Очистити тільки конкретний тип даних
            debugger = RedisDebugger()
            keys_by_type = debugger.get_huey_keys()

            # Очистити тільки результати
            if keys_by_type['result']:
                debugger.redis_client.delete(*keys_by_type['result'])
                print("Результати очищено")
            ```
        """
        print("\n⚠️  УВАГА: Це видалить ВСІ дані Huey!")
        response = input("Ви впевнені? (yes/no): ")

        if response.lower() == 'yes':
            keys = self.get_all_keys(f'{self.huey_prefix}.*')
            if keys:
                deleted = self.redis_client.delete(*keys)
                print(f"✅ Видалено {deleted} ключів")
            else:
                print("ℹ️  Немає ключів для видалення")
        else:
            print("❌ Скасовано")

    def show_key_details(self, key: str):
        """
        Показати деталі конкретного ключа Redis.

        Виводить:
            - Тип ключа (string, list, hash, set, etc.)
            - TTL (час життя) ключа
            - Вміст ключа (форматований для JSON, обмежений для великих значень)

        Args:
            key: Назва ключа для аналізу

        Приклади:
            ```python
            debugger = RedisDebugger()

            # Показати деталі черги
            debugger.show_key_details('huey.main.queue')
            # Виведе:
            # 🔍 ДЕТАЛІ КЛЮЧА: huey.main.queue
            # ============================================================
            # Тип: list
            # TTL: -1 секунд (без обмеження)
            # Довжина: 5
            # Перші елементи:
            #   1. {
            #     "task": "tasks.test_task",
            #     "args": [],
            #     "kwargs": {}
            #   }
            ```

            ```python
            # Показати деталі результату
            debugger = RedisDebugger()
            result_keys = debugger.get_all_keys('huey.results.*')

            if result_keys:
                # Показати деталі першого результату
                debugger.show_key_details(result_keys[0])
            ```

            ```python
            # Перевірити всі ключі певного типу
            debugger = RedisDebugger()
            keys_by_type = debugger.get_huey_keys()

            for queue_key in keys_by_type['queue']:
                print(f"\n{'='*60}")
                debugger.show_key_details(queue_key)
            ```

            ```python
            # Знайти та показати деталі ключа за паттерном
            debugger = RedisDebugger()
            keys = debugger.get_all_keys('huey.*.queue')

            for key in keys:
                debugger.show_key_details(key)
            ```
        """
        print(f"\n🔍 ДЕТАЛІ КЛЮЧА: {key}")
        print("="*60)

        key_type = self.redis_client.type(key)
        ttl = self.redis_client.ttl(key)

        print(f"Тип: {key_type}")
        print(f"TTL: {ttl} секунд ({'без обмеження' if ttl == -1 else f'{ttl//60} хвилин'})")

        if key_type == 'list':
            length = self.redis_client.llen(key)
            print(f"Довжина: {length}")
            if length > 0:
                items = self.redis_client.lrange(key, 0, 4)
                print("Перші елементи:")
                for i, item in enumerate(items, 1):
                    try:
                        item_data = json.loads(item)
                        print(f"  {i}. {json.dumps(item_data, indent=2, ensure_ascii=False)}")
                    except:
                        print(f"  {i}. {item[:100]}")
        elif key_type == 'string':
            value = self.redis_client.get(key)
            try:
                value_data = json.loads(value)
                print(f"Значення:\n{json.dumps(value_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"Значення: {value}")
        elif key_type == 'hash':
            value = self.redis_client.hgetall(key)
            print(f"Значення: {value}")
        elif key_type == 'set':
            members = self.redis_client.smembers(key)
            print(f"Елементи: {list(members)}")


def main():
    """Головна функція з інтерактивним меню"""
    debugger = RedisDebugger()

    if not debugger.ping():
        sys.exit(1)

    print("\n" + "="*60)
    print("🔧 REDIS DEBUGGER ДЛЯ HUEY")
    print("="*60)

    while True:
        print("\n📋 МЕНЮ:")
        print("1. Показати інформацію про черги")
        print("2. Показати статистику Redis")
        print("3. Показати всі ключі Huey")
        print("4. Показати деталі ключа")
        print("5. Моніторити таски в реальному часі")
        print("6. Очистити всі дані Huey (⚠️ небезпечно)")
        print("0. Вихід")

        choice = input("\nОберіть опцію: ").strip()

        if choice == '1':
            debugger.show_queue_info()
        elif choice == '2':
            debugger.show_statistics()
        elif choice == '3':
            keys = debugger.get_all_keys(f'{HUEY_PREFIX}.*')
            print(f"\n🔑 Всі ключі Huey ({len(keys)}):")
            for key in sorted(keys):
                print(f"  • {key}")
        elif choice == '4':
            key = input("Введіть ключ: ").strip()
            if key:
                debugger.show_key_details(key)
        elif choice == '5':
            duration = input("Тривалість моніторингу (секунд, за замовчуванням 30): ").strip()
            duration = int(duration) if duration.isdigit() else 30
            debugger.monitor_tasks(duration)
        elif choice == '6':
            debugger.clear_all_huey_data()
        elif choice == '0':
            print("👋 До побачення!")
            break
        else:
            print("❌ Невірний вибір")


if __name__ == '__main__':
    main()
