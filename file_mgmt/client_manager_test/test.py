from fastapi import FastAPI, APIRouter

class Hello:

    def __init__(self, name: str):
        self.name = name
        self.router = APIRouter()
        self.router.add_api_route("/hello", self.hello, methods=["GET"])

    def hello(self):
        return {"Hello": self.name}


app = FastAPI()
hello = Hello("SomethingNew")
app.include_router(hello.router)

import uvicorn
uvicorn.run(app, host="127.0.0.1", port=8002)