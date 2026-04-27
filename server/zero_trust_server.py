from server.app import app #type: ignore

if __name__ == "__main__":
    print("Starting Zero Trust Server...")
    app.run(port=5000)