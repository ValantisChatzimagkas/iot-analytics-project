from fastapi import FastAPI
import uvicorn
# from iot_analytics_project.api.db.db_connection import init_db
# from iot_analytics_project.api.routes import endpoints

from db.db_connection import init_db
from routes import endpoints

app = FastAPI()
app.include_router(endpoints.router)

@app.get("/")
def read_root():
    return {"message": "API is running"}

@app.on_event("startup")
async def startup_event():
    """Run tasks needed before the application starts serving requests."""
    await init_db()





if __name__ == "__main__":
    #uvicorn.run("iot_analytics_project.api.main:app", host="127.0.0.1", port=8000, reload=True)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)