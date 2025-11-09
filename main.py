"""FastAPI REST API for handling background tasks with Huey."""
from fastapi import FastAPI, Request
from tasks.testing import long_running_task

app = FastAPI()

@app.get("/")
def read_root(request: Request):
    """Simple check if API works"""

    print(f"URL: {request.url}")
    print(f"Headers: {dict(request.headers)}")
    print(f"Query params: {dict(request.query_params)}")
    print(f"Client IP: {request.client.host if request.client else 'unknown'}")

    task = long_running_task('Test get data')

    print(task)

    resp = {"message": "FastAPI works!", "task_id": task.id}
    return resp


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
