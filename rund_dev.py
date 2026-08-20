import threading
import webbrowser
import uvicorn


def abrir_swagger():
    webbrowser.open("http://127.0.0.1:8000/docs")


if __name__ == "__main__":
    threading.Timer(2, abrir_swagger).start()

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )