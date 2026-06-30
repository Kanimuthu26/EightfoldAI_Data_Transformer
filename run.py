from app.app import create_app

app = create_app()

if __name__ == '__main__':
    # Run locally on port 5000
    app.run(debug=True, host='127.0.0.1', port=8080)
