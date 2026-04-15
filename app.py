import os
import random
from flask import Flask, render_template, jsonify, send_from_directory

app = Flask(__name__)

PANEELIT_KANSIO = os.path.join(os.path.dirname(__file__), 'paneelit')


def hae_paneelit():
    """Palauttaa listan kaikista paneelitiedostoista."""
    if not os.path.exists(PANEELIT_KANSIO):
        return []
    return [f for f in os.listdir(PANEELIT_KANSIO) if f.lower().endswith('.png')]


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/arvo')
def arvo():
    """Arpoo kolme satunnaista paneelia ja palauttaa niiden nimet."""
    paneelit = hae_paneelit()
    if len(paneelit) < 3:
        return jsonify({'virhe': 'Ei tarpeeksi paneeleja'}), 400
    valitut = random.sample(paneelit, 3)
    return jsonify({'paneelit': valitut})


@app.route('/paneelit/<nimi>')
def paneeli(nimi):
    """Palauttaa yksittäisen paneelitiedoston."""
    return send_from_directory(PANEELIT_KANSIO, nimi)


if __name__ == '__main__':
    app.run(debug=True)
