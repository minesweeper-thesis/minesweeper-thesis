if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", reload=True)
