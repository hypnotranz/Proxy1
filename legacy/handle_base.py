from fastapi import APIRouter

class HandleBase:
    def __init__(self):
        self.router = APIRouter()

        @self.router.get("/example")
        async def example_endpoint():
            return {"message": "This is an example endpoint"}
