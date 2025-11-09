"""FastAPI REST API for handling background tasks with Huey."""
from fastapi import FastAPI
from tasks import long_running_task

app = FastAPI()

@app.get("/")
def read_root():
    """Simple check if API works"""
    return {"message": "FastAPI works!"}

@app.post("/create-task/{data}")
async def create_task(data: str):
    """
    This endpoint instantly creates a background task
    and returns a response.
    """
    print(f"[FASTAPI]: Received request to create task. Data: {data}")

    # Instantly send task to queue (Redis)
    # Huey will handle executing it in the background
    task = long_running_task(data)


    # Instantly return Task ID (though we don't use it)
    return {
        "message": "Task accepted for processing!",
        "task_id": task.id
    }
