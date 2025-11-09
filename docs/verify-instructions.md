# Vefify whole stack


## 1 Check: Are all containers running?
Bash

docker ps
You should see something like this (3 containers, status "Up"):

✅ CHECK 1: **All 3 containers are running.**
----------------------------------------------------


## 2 Check: Is Redis working?
Let's go inside the Redis container and give it a command:
```sh
docker exec -it uikit-agent-redis-1 redis-cli PING
```
You should get the response:
PONG

 ✅ CHECK 2: Redis is alive and responds "PONG".
----------------------------------------------------

## 1.2. Check: Is FastAPI working?
Open your browser and go to http://localhost:8000 Or run in terminal:
```sh
curl http://localhost:8000
```

You should get the response:
```json
{"message":"FastAPI works!"}
```
----------------------------------------------------

## 3. Check: Is the entire chain working (FastAPI -> Redis -> Huey)?
Now we will check the entire cycle.
#### A. Open a second terminal and start monitoring Huey worker logs.
We won't touch this terminal, just observe:
```sh
docker logs uikit-agent-worker-1 --follow
```
You will see Huey startup logs. Keep this terminal open.

#### B. Return to the first terminal and send a request to our API to create a task.

```sh
curl -X POST http://localhost:8000/create-task/HelloDocker
```

You will instantly get a response:

```json
{"message":"Task accepted for processing!","task_id":"..."}
```

#### C. Now look at the second terminal (with Huey logs)
Almost immediately you will see how Huey "picked up" the task from Redis:

```txt
[YOUR DATE] INFO:huey:Worker-1:Executing tasks.long_running_task: e33e32fc-d11d-4ba6-86f5-44229718352d
...after 5 seconds...
[YOUR DATE] INFO:huey:Worker-1:tasks.long_running_task: e33e32fc-d11d-4ba6-86f5-44229718352d executed in 5.005s
```

If everything works as described, the entire cycle is working! FastAPI received the request, put it in Redis, and Huey picked it up from Redis and executed it.