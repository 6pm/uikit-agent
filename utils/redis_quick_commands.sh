#!/bin/bash
# Швидкий довідник команд Redis для Huey
# Використання: ./utils/redis_quick_commands.sh

REDIS_CONTAINER="uikit-agent-redis-1"
REDIS_CLI="docker exec -it $REDIS_CONTAINER redis-cli"

echo "🔧 Швидкі команди Redis для Huey"
echo "=================================="
echo ""

# Функція для виконання команди
run_command() {
    echo "▶️  $1"
    $REDIS_CLI $2
    echo ""
}

# Перевірка підключення
echo "1️⃣  Перевірка підключення:"
run_command "PING" "PING"

# Всі ключі Huey
echo "2️⃣  Всі ключі Huey:"
run_command "KEYS huey.*" "KEYS 'huey.*'"

# Черги
echo "3️⃣  Черги тасок:"
run_command "KEYS huey.main.*" "KEYS 'huey.main.*'"

# Кількість тасок в черзі
echo "4️⃣  Кількість тасок в черзі:"
QUEUE_KEY=$($REDIS_CLI KEYS 'huey.main.*' | head -1)
if [ -n "$QUEUE_KEY" ]; then
    run_command "LLEN $QUEUE_KEY" "LLEN '$QUEUE_KEY'"
else
    echo "   ℹ️  Черга порожня"
fi

# Результати
echo "5️⃣  Результати тасок:"
run_command "KEYS huey.results.*" "KEYS 'huey.results.*'"

# Статистика
echo "6️⃣  Статистика Redis:"
run_command "INFO stats" "INFO stats | head -20"

echo "💡 Для більш детального аналізу використовуйте: python utils/redis_debug.py"
