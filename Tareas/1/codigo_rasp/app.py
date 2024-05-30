from flask import Flask, render_template, request, redirect, url_for
from utils import set_active

app = Flask(__name__, template_folder="templates")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/change', methods=["POST"])
def change():
    option = request.form['protocol-tl']
    protocol = option[9]
    transport_layer = 0 if option[11] == "T" else 1
    set_active(protocol=protocol ,transport_layer=transport_layer)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
