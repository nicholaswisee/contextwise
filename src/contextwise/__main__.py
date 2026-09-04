import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "contextwise.api.main:create_app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        factory=True,
    )
