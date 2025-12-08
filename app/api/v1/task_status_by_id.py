# @app.get("/task-status/{task_id}")
# async def get_task_status(task_id: str):
#     """
#     Get status and result of a task.

#     BEST PRACTICE: Provide status endpoint for async tasks.
#     """
#     from config import huey

#     try:
#         # BEST PRACTICE: Use Huey's storage to get result
#         # Huey stores results in Redis, we can access them via storage
#         storage = huey.storage

#         # Try to get result from storage
#         result = storage.get_result(task_id)

#         if result is None:
#             # Task might still be pending or doesn't exist
#             # Check if task is in queue
#             return {
#                 "task_id": task_id,
#                 "status": "pending",
#                 "result": None
#             }

#         return {
#             "task_id": task_id,
#             "status": "completed",
#             "result": result
#         }

#     except Exception as e:
#         logger.error("[FASTAPI]: Error retrieving task %s: %s", task_id, str(e), exc_info=True)
#         raise HTTPException(status_code=500, detail=f"Failed to retrieve task: {str(e)}") from e
