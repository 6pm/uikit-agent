# Step 1: Base Python image
FROM python:3.11-slim

RUN pip install uv

# Step 2: Create working directory inside container
WORKDIR /app

# Step 3: Copy dependencies file
COPY requirements.txt .

# Step 4: Install dependencies using uv
# This will be cached and won't run every time
RUN uv pip install --system --no-cache -r requirements.txt

# Step 5: Copy ALL our code (main.py, tasks.py, etc.)
COPY . .

# Step 6: Tell Docker that our API will be on port 8000
EXPOSE 8000

# Step 7: Default command (for FastAPI)
# We will override it for Huey worker in docker-compose
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]