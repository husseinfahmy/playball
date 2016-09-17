import os
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def main():
	return render_template('main.html')

port = os.getenv('PORT', '5000')
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(port))