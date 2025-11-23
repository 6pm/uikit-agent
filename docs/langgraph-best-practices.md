# LangGraph Best Practices для FastAPI + Huey + Redis

## 📋 Зміст
1. [Архітектура](#архітектура)
2. [Найкращі практики](#найкращі-практики)
3. [Антипатерни (що НЕ робити)](#антипатерни-що-не-робити)
4. [Покрокова інтеграція](#покрокова-інтеграція)
5. [Приклади використання](#приклади-використання)

---

## 🏗️ Архітектура

### Правильна архітектура (✅ BEST PRACTICE)

```
FastAPI (REST API)
    ↓
Huey Task Queue (Redis)
    ↓
LangGraph Agent (Background Worker)
    ↓
Multi-stage Code Generation
```

**Чому це правильно:**
- FastAPI обробляє HTTP запити швидко (не блокується)
- Huey чергує завдання в Redis (надійність, масштабованість)
- LangGraph виконується в background worker (може тривати довго)
- Кожен компонент має одну відповідальність

---

## ✅ Найкращі практики

### 1. **Розділення відповідальностей**

#### ✅ ПРАВИЛЬНО:
```python
# models/figma.py - Моделі даних
class FigmaComponent(BaseModel):
    ...

# agents/code_generator.py - Бізнес-логіка (без Huey)
class CodeGeneratorAgent:
    def generate(self, request_data: dict) -> dict:
        ...

# tasks/code_generation.py - Тонкий шар для Huey
@huey.task()
def generate_code_from_figma(request_data: dict):
    agent = CodeGeneratorAgent.create()
    return agent.generate(request_data)

# main.py - API endpoints
@app.post("/generate-code")
async def generate_code(request: FigmaRequest):
    task = generate_code_from_figma(request_dict)
    return {"task_id": task.id}
```

**Переваги:**
- Агента можна тестувати окремо
- Агента можна використовувати без Huey (наприклад, в CLI)
- Легко замінити Huey на іншу чергу
- Чіткі межі між шарами

#### ❌ НЕПРАВИЛЬНО:
```python
# АНТИПАТЕРН: Все в одному файлі
@app.post("/generate-code")
async def generate_code(request: FigmaRequest):
    # LLM виклики прямо в endpoint - блокує FastAPI!
    llm = ChatOpenAI(...)
    result = llm.invoke(...)  # ❌ Блокує на 30+ секунд!
    return result
```

---

### 2. **Управління станом (State Management)**

#### ✅ ПРАВИЛЬНО: TypedDict для стану
```python
class GenerationState(TypedDict):
    """Чітко визначена структура стану."""
    figma_components: list[FigmaComponent]
    target_framework: str
    analysis: NotRequired[str]
    generated_code: NotRequired[str]
    errors: NotRequired[list[str]]
```

**Переваги:**
- Type safety (IDE підказує поля)
- Чіткий контракт між нодами
- Легко додавати нові поля

#### ❌ НЕПРАВИЛЬНО: Dict без структури
```python
# АНТИПАТЕРН: Неструктурований стан
state = {}  # ❌ Немає типізації, легко зробити помилку
state["analsis"] = "..."  # ❌ Typo! Не знайдено помилку
```

---

### 3. **Серіалізація для Redis/Huey**

#### ✅ ПРАВИЛЬНО: JSON-серіалізовані дані
```python
# Конвертуємо Pydantic моделі в dict
request_dict = {
    "figma_components": [comp.model_dump() for comp in request.components],
    "target_framework": request.target_framework
}

# Передаємо dict в Huey
task = generate_code_from_figma(request_dict)
```

#### ❌ НЕПРАВИЛЬНО: Пряма передача Pydantic моделей
```python
# АНТИПАТЕРН: Huey не може серіалізувати Pydantic моделі
task = generate_code_from_figma(request)  # ❌ Помилка серіалізації!
```

---

### 4. **Обробка помилок**

#### ✅ ПРАВИЛЬНО: Обробка на кожному етапі
```python
def _analyze_components(self, state: GenerationState) -> GenerationState:
    try:
        # Логіка аналізу
        state["analysis"] = response.content
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        if "errors" not in state:
            state["errors"] = []
        state["errors"].append(str(e))
        # Продовжуємо виконання з помилкою
    return state
```

**Переваги:**
- Граф не падає на першій помилці
- Можна зібрати всі помилки
- Легко дебажити

#### ❌ НЕПРАВИЛЬНО: Необроблені винятки
```python
# АНТИПАТЕРН: Виняток вб'є весь граф
def _analyze_components(self, state: GenerationState):
    response = self.llm.invoke(...)  # ❌ Якщо помилка - все падає
    return state
```

---

### 5. **Логування**

#### ✅ ПРАВИЛЬНО: Структуроване логування
```python
import logging

logger = logging.getLogger(__name__)

logger.info("Stage 1: Analyzing components")
logger.debug(f"Request data: {request_data}")
logger.error(f"Analysis failed: {str(e)}", exc_info=True)
```

**Переваги:**
- Легко відстежувати виконання
- Можна фільтрувати по рівнях
- `exc_info=True` дає stack trace

#### ❌ НЕПРАВИЛЬНО: print() замість логування
```python
# АНТИПАТЕРН: print() не структурований
print("Starting...")  # ❌ Немає рівнів, timestamps, контексту
```

---

### 6. **Ініціалізація агента**

#### ✅ ПРАВИЛЬНО: Ініціалізація в завданні
```python
@huey.task()
def generate_code_from_figma(request_data: dict):
    # Створюємо агента при кожному виконанні
    agent = CodeGeneratorAgent(model_provider="openai")
    return agent.generate(request_data)
```

**Переваги:**
- Свіжий стан для кожного завдання
- Ізоляція помилок
- Можна змінювати конфігурацію між завданнями

#### ❌ НЕПРАВИЛЬНО: Глобальний агент
```python
# АНТИПАТЕРН: Глобальний стан
agent = CodeGeneratorAgent()  # ❌ На рівні модуля

@huey.task()
def generate_code_from_figma(request_data: dict):
    return agent.generate(request_data)  # ❌ Стан може бути забруднений
```

---

### 7. **Асинхронність FastAPI**

#### ✅ ПРАВИЛЬНО: Швидкий повернення task_id
```python
@app.post("/generate-code")
async def generate_code(request: FigmaRequest):
    # Швидко чергуємо завдання
    task = generate_code_from_figma(request_dict)

    # Повертаємо одразу
    return {"task_id": task.id, "status": "queued"}
```

**Переваги:**
- FastAPI не блокується
- Клієнт отримує відповідь миттєво
- Можна обробляти багато запитів одночасно

#### ❌ НЕПРАВИЛЬНО: Очікування результату
```python
# АНТИПАТЕРН: Блокування FastAPI
@app.post("/generate-code")
async def generate_code(request: FigmaRequest):
    task = generate_code_from_figma(request_dict)
    result = task.get()  # ❌ Блокує на 30+ секунд!
    return result
```

---

### 8. **Моделі Pydantic для валідації**

#### ✅ ПРАВИЛЬНО: Валідація на вході
```python
class FigmaRequest(BaseModel):
    components: List[FigmaComponent]
    target_framework: str = Field(default="react")

    @validator('target_framework')
    def validate_framework(cls, v):
        allowed = ['react', 'vue', 'angular']
        if v not in allowed:
            raise ValueError(f"Framework must be one of {allowed}")
        return v
```

**Переваги:**
- Автоматична валідація
- Чіткі повідомлення про помилки
- Type hints для IDE

---

## ❌ Антипатерни (що НЕ робити)

### 1. **Блокування FastAPI**

```python
# ❌ АНТИПАТЕРН
@app.post("/generate-code")
async def generate_code(request: FigmaRequest):
    # Виклик LLM прямо в endpoint
    llm = ChatOpenAI()
    result = llm.invoke(...)  # Блокує на 30+ секунд!
    return result
```

**Проблеми:**
- FastAPI не може обробляти інші запити
- Таймаути клієнтів
- Неможливість масштабування

**Рішення:** Використовуйте Huey для background tasks.

---

### 2. **Глобальний стан**

```python
# ❌ АНТИПАТЕРН
agent = CodeGeneratorAgent.create()  # Глобальна змінна

@huey.task()
def generate_code_from_figma(request_data: dict):
    return agent.generate(request_data)  # Використовує глобальний стан
```

**Проблеми:**
- Стан може бути забруднений між завданнями
- Race conditions при паралельному виконанні
- Важко тестувати

**Рішення:** Створюйте агента в кожному завданні.

---

### 3. **Неструктурований стан**

```python
# ❌ АНТИПАТЕРН
state = {}  # Немає типізації
state["analsis"] = "..."  # Typo не виявлено
state["generatedCode"] = "..."  # Inconsistent naming
```

**Проблеми:**
- Помилки типізації не виявлені
- Важко відстежити структуру
- Легко зробити помилку

**Рішення:** Використовуйте TypedDict.

---

### 4. **Відсутність обробки помилок**

```python
# ❌ АНТИПАТЕРН
def _generate_code(self, state: GenerationState):
    response = self.llm.invoke(...)  # Якщо помилка - все падає
    state["generated_code"] = response.content
    return state
```

**Проблеми:**
- Весь граф падає на одній помилці
- Немає інформації про помилку
- Неможливо відновитися

**Рішення:** Обробляйте винятки в кожній ноді.

---

### 5. **Пряма передача Pydantic моделей в Huey**

```python
# ❌ АНТИПАТЕРН
@app.post("/generate-code")
async def generate_code(request: FigmaRequest):
    task = generate_code_from_figma(request)  # Помилка серіалізації!
    return {"task_id": task.id}
```

**Проблеми:**
- Huey не може серіалізувати Pydantic моделі
- Помилка при чергуванні завдання

**Рішення:** Конвертуйте в dict через `model_dump()`.

---

### 6. **Відсутність логування**

```python
# ❌ АНТИПАТЕРН
def _analyze_components(self, state: GenerationState):
    response = self.llm.invoke(...)  # Немає логів
    state["analysis"] = response.content
    return state
```

**Проблеми:**
- Неможливо відстежити виконання
- Важко дебажити
- Немає метрик

**Рішення:** Використовуйте `logging` модуль.

---

### 7. **Жорстко закодовані API ключі**

```python
# ❌ АНТИПАТЕРН
llm = ChatOpenAI(api_key="sk-...")  # Ключ в коді!
```

**Проблеми:**
- Безпека (ключ в Git)
- Неможливість змінити без деплою

**Рішення:** Використовуйте environment variables.

---

### 8. **Великі промпти без структури**

```python
# ❌ АНТИПАТЕРН
prompt = f"Generate code for {components}"  # Занадто загально
```

**Проблеми:**
- Непередбачувані результати
- Важко контролювати вихід

**Рішення:** Використовуйте структуровані SystemMessage + HumanMessage.

---

## 📝 Покрокова інтеграція

### Крок 1: Встановлення залежностей

```bash
pip install langgraph langchain-core langchain-openai pydantic
```

### Крок 2: Створення моделей (models/figma.py)

```python
from pydantic import BaseModel

class FigmaComponent(BaseModel):
    component_id: str
    name: str
    root_node: FigmaNode
```

### Крок 3: Створення агента (agents/code_generator.py)

```python
from langgraph.graph import StateGraph, MessagesState, START, END

def mock_llm(state: MessagesState):
    return {"messages": [{"role": "ai", "content": "hello world"}]}

codeGenGraph = StateGraph(MessagesState)
codeGenGraph.add_node(mock_llm)
codeGenGraph.add_edge(START, "mock_llm")
codeGenGraph.add_edge("mock_llm", END)
codeGenGraph = codeGenGraph.compile()

```

### Крок 4: Створення Huey task (tasks/code_generation.py)

```python
@huey.task()
def generate_code_from_figma(request_data: dict):
    codeGenGraph.invoke({"messages": [{"role": "user", "content": "hi!"}]})
    return agent.generate(request_data)
```

### Крок 5: Створення API endpoint (main.py)

```python
@app.post("/generate-code")
async def generate_code(request: FigmaRequest):
    request_dict = {
        "figma_components": [comp.model_dump() for comp in request.components]
    }
    task = generate_code_from_figma(request_dict)
    return {"task_id": task.id}
```

---

## 🚀 Приклади використання

### Приклад 1: Генерація коду з одного компонента

```bash
curl -X POST http://localhost:8000/generate-code \
  -H "Content-Type: application/json" \
  -d '{
    "request": [
      {
        "component_id": "comp_123",
        "name": "PrimaryButton",
        "root_node": {
          "id": "1:23",
          "name": "Button",
          "type": "FRAME",
          "properties": {"width": 120, "height": 40}
        }
      }
    ],
    "target_framework": "react",
    "style_approach": "tailwind"
  }'
```

### Приклад 2: Перевірка статусу завдання

```bash
curl http://localhost:8000/task-status/{task_id}
```

### Приклад 3: Python клієнт

```python
import requests

response = requests.post(
    "http://localhost:8000/generate-code",
    json={
        "components": [...],
        "target_framework": "react"
    }
)

task_id = response.json()["task_id"]

# Перевірка результату
result = requests.get(f"http://localhost:8000/task-status/{task_id}")
print(result.json())
```

---

## 🔧 Налаштування environment variables

Створіть `.env` файл:

```bash
OPENAI_API_KEY=sk-...
# або
ANTHROPIC_API_KEY=sk-ant-...

REDIS_HOST=localhost  # для локальної розробки
```

Завантажте в коді:

```python
from dotenv import load_dotenv
load_dotenv()
```

---

## 📊 Моніторинг та дебагінг

### Перевірка черги Huey

```python
from config import huey

# Список pending tasks
pending = huey.pending()

# Результат task
result = huey.get_result(task_id)
```

### Логування

Всі етапи логуються автоматично. Перевіряйте логи:

```bash
# Логи Huey worker
tail -f logs/huey.log

# Логи FastAPI
tail -f logs/fastapi.log
```

---

## 🎯 Висновки

**Ключові принципи:**
1. ✅ Розділення відповідальностей
2. ✅ Асинхронність (FastAPI не блокується)
3. ✅ Типізація (TypedDict, Pydantic)
4. ✅ Обробка помилок на кожному етапі
5. ✅ Логування для дебагу
6. ✅ JSON-серіалізація для Redis
7. ✅ Environment variables для конфігурації

**Уникайте:**
1. ❌ Блокування FastAPI
2. ❌ Глобального стану
3. ❌ Неструктурованих даних
4. ❌ Відсутності обробки помилок
5. ❌ Жорстко закодованих ключів
