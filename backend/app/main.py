from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.single_label import router as single_label_router
from app.routes.batch_label import router as batch_label_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(single_label_router)
app.include_router(batch_label_router)

@app.get("/")
def root():
    return {"status": "running"}