import asyncio
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI(title="sse test")

async def process_stream():
    words = (
        "Lorem ipsum dolor sit amet consectetur adipiscing elit. "
        "Ex sapien vitae pellentesque sem placerat in id. "
        "Pretium tellus duis convallis tempus leo eu aenean. "
        "Urna tempor pulvinar vivamus fringilla lacus nec metus. "
        "Iaculis massa nisl malesuada lacinia integer nunc posuere. "
        "Semper vel class aptent taciti sociosqu ad litora. "
        "Conubia nostra inceptos himenaeos orci varius natoque penatibus. "
        "Dis parturient montes nascetur ridiculus mus donec rhoncus. "
        "Nulla molestie mattis scelerisque maximus eget fermentum odio. "
        "Purus est efficitur laoreet mauris pharetra vestibulum fusce."
    ).split()

    for word in words:
        await asyncio.sleep(0.5)
        yield f"data: {word}\n\n"

@app.get("/test")  # Changed to GET
async def test_endpoint():
    return StreamingResponse(process_stream(), media_type="text/event-stream")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("testsseserver:app", host="0.0.0.0", port=8000, reload=True)
