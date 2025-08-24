# pcRemote
pet-project

***<ins>WARNING: PROJECT VERY UNSECURITY, ITS JUST A PET PROJECT!!!</ins>***

## Overview

### Used technologies
- Language: ***Python***.
- Framework for server api: ***Django REST Framework***.
- Client use default package ***pty*** and ***aiopika*** (client for messages broker)
- Docker, Docker compose
- Also: RabbitMQ (as main message broker), Celery, Redis (message broker for celery)

## How to run
1. Run server on first pc (or terminal session): ``` docker compose up --build ```
2. Setup environment for client:
```
cd client
python3 -m venv .venv
pip install -r client-req.txt 
```
3. Run client.py and register new user with command ***reg***: ``` python client.py ```
4. Run exec.py on second pc (or terminal session): ``` python exec.py <room> ```
5. Run send.py on third pc (or terminal session): ``` python send.py <room> ```

All commands (and keys) from send.py (third pc) will send to exec.py (second pc) and will execute there.
