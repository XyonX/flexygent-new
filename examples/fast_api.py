from fastapi import FastAPI


app = FastAPI()




@app.get("/")
async def main():
    return {"result":"hello world!"}