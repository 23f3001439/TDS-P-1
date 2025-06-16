from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# ✅ Add this part
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "API is working!"}

# Optional: create this test route
@app.get("/api/test")
def test_api():
    return {"success": True, "message": "API is working properly!"}
