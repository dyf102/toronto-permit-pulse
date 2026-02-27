from fastapi import FastAPI

app = FastAPI(title="CrossBeam Toronto API")

@app.get("/")
async def root():
    return {"message": "Welcome to the CrossBeam Toronto Permit System API", "status": "online"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
