# Step 1: Base Python image
FROM python:3.11-slim

# 1. Встановлюємо uv правильно (копіюємо бінарник, це надійніше і швидше за pip install)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# 2. Вмикаємо компіляцію байт-коду (прискорює старт контейнера)
ENV UV_COMPILE_BYTECODE=1

# 3. Копіюємо файли залежностей (ОБИДВА файли)
# Це дозволяє Docker закешувати цей крок, якщо залежності не змінилися
COPY pyproject.toml uv.lock ./

# 4. Встановлюємо ТІЛЬКИ залежності (без самого коду проекту)
# --frozen: гарантує використання версій з uv.lock
# --no-install-project: не намагається встановити наш код (бо його ще немає)
RUN uv sync --frozen --no-install-project

# 5. Тепер копіюємо весь код
COPY . .

# 6. Довстановлюємо сам проект
RUN uv sync --frozen

# 7. ВАЖЛИВО: Додаємо віртуальне оточення в PATH
# Тепер python і uvicorn будуть автоматично братися з .venv
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# Запуск
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]