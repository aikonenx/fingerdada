"""
Fingerpori-paneelien leikkaustyökalu
=====================================
Käyttö:
    python leikkaa_paneelit.py --kuvat ./stripit --paneelit ./paneelit

Skripti käy läpi kaikki AVIF-kuvat kansiosta, tunnistaa paneelimäärän
automaattisesti mustien reunaviivojen perusteella ja leikkaa paneelit
erillisiksi PNG-tiedostoiksi.
"""

import os
import sys
import argparse
import numpy as np
from PIL import Image


def etsi_tummat_viivaryhmät(brightness, kynnys=50, min_rako=3):
    """Löytää tummat pikseliryhmät brightness-listasta."""
    tummat = [i for i, b in enumerate(brightness) if b < kynnys]
    if not tummat:
        return []
    ryhmät = []
    alku = tummat[0]
    edellinen = tummat[0]
    for i in tummat[1:]:
        if i - edellinen > min_rako:
            ryhmät.append((alku, edellinen))
            alku = i
        edellinen = i
    ryhmät.append((alku, edellinen))
    return ryhmät


def tunnista_paneelit(img):
    """
    Tunnistaa paneelien rajat kuvasta.
    Palauttaa listan (x_alku, y_alku, x_loppu, y_loppu) -bokseja.
    """
    arr = np.array(img.convert('RGB'))
    h, w = arr.shape[:2]

    # Laske jokaisen kolonin ja rivin keskimääräinen kirkkaus
    col_brightness = arr.mean(axis=0).mean(axis=1)
    row_brightness = arr.mean(axis=1).mean(axis=1)

    x_ryhmät = etsi_tummat_viivaryhmät(col_brightness)
    y_ryhmät = etsi_tummat_viivaryhmät(row_brightness)

    if len(x_ryhmät) < 2:
        # Ei löydy reunaviivoja - palautetaan koko kuva yhtenä paneelina
        return [(0, 0, w, h)]

    # Ylä- ja alarajoiksi otetaan ensimmäisen y-viivaryhmän alku ja
    # viimeisen loppu (tai kuvan reunat jos viivoja ei löydy)
    if len(y_ryhmät) >= 2:
        y_alku = max(0, y_ryhmät[0][0] - 1)
        y_loppu = min(h, y_ryhmät[-1][1] + 2)
    elif len(y_ryhmät) == 1:
        # Vain yksi vaakaviivaryhmä - oletetaan se ylä- tai alareunaksi
        y_alku = 0
        y_loppu = h
    else:
        y_alku = 0
        y_loppu = h

    # Paneelien väliset viivat ovat x_ryhmät[1:-1] pareittain
    # Rakenne: [vasen_reuna, väli1_oikea_puoli, väli1_vasen_puoli, ..., oikea_reuna]
    # tai: [vasen_reuna, väli1, väli2, ..., oikea_reuna] jos välit ovat ohuempia

    vasen_reuna = x_ryhmät[0]
    oikea_reuna = x_ryhmät[-1]
    väliviivat = x_ryhmät[1:-1]

    # Paneelien lukumäärä
    # Jos väliviivoja on parillinen määrä -> ne ovat pareja (paksu viiva)
    # Jos pariton -> yksittäisiä viivoja
    paneelit = []

    if len(väliviivat) == 0:
        # Yksi paneeli
        x_alku = max(0, vasen_reuna[0] - 1)
        x_loppu = min(w, oikea_reuna[1] + 2)
        paneelit.append((x_alku, y_alku, x_loppu, y_loppu))

    elif len(väliviivat) % 2 == 0:
        # Parilliset väliviivat = paksu reunaviiva paneelien välissä (kaksi viivaa per väli)
        # Paneeli 1: vasen_reuna .. väliviivat[0]
        # Paneeli 2: väliviivat[1] .. väliviivat[2]
        # jne.
        rajat_x = [vasen_reuna] + väliviivat + [oikea_reuna]
        i = 0
        while i < len(rajat_x) - 1:
            x_alku = max(0, rajat_x[i][0] - 1)
            x_loppu = min(w, rajat_x[i + 1][1] + 2)
            paneelit.append((x_alku, y_alku, x_loppu, y_loppu))
            i += 2
    else:
        # Pariton väliviivat = yksittäiset ohuet viivat paneelien välissä
        rajat_x = [vasen_reuna] + väliviivat + [oikea_reuna]
        for i in range(len(rajat_x) - 1):
            x_alku = max(0, rajat_x[i][0] - 1)
            x_loppu = min(w, rajat_x[i + 1][1] + 2)
            paneelit.append((x_alku, y_alku, x_loppu, y_loppu))

    return paneelit


def leikkaa_kuvat(lähde_kansio, kohde_kansio, verbose=True):
    """Käy läpi kaikki AVIF-kuvat ja leikkaa paneelit."""
    os.makedirs(kohde_kansio, exist_ok=True)

    tiedostot = sorted([
        f for f in os.listdir(lähde_kansio)
        if f.lower().endswith(('.avif', '.jpg', '.jpeg', '.png'))
    ])

    if not tiedostot:
        print(f"Ei kuvatiedostoja kansiossa: {lähde_kansio}")
        return

    onnistuneet = 0
    virheet = 0
    paneelit_yht = 0

    for tiedosto in tiedostot:
        polku = os.path.join(lähde_kansio, tiedosto)
        nimi = os.path.splitext(tiedosto)[0]

        try:
            img = Image.open(polku)
            paneelit = tunnista_paneelit(img)
            n = len(paneelit)

            for i, boksi in enumerate(paneelit):
                paneeli = img.crop(boksi).convert('RGB')
                kohde_nimi = f"{nimi}_p{i+1:02d}.png"
                kohde_polku = os.path.join(kohde_kansio, kohde_nimi)
                paneeli.save(kohde_polku)
                paneelit_yht += 1

            if verbose:
                print(f"✓ {tiedosto} → {n} paneeli{'a' if n != 1 else ''}")
            onnistuneet += 1

        except Exception as e:
            print(f"✗ {tiedosto}: virhe - {e}")
            virheet += 1

    print(f"\nValmis! {onnistuneet} kuvaa käsitelty, {paneelit_yht} paneelia tallennettu kohteeseen '{kohde_kansio}'")
    if virheet:
        print(f"Virheitä: {virheet} kuvaa")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Leikkaa Fingerpori-stripit paneeleiksi")
    parser.add_argument("--kuvat", default="./stripit", help="Kansio jossa AVIF-kuvat ovat (oletus: ./stripit)")
    parser.add_argument("--paneelit", default="./paneelit", help="Kansio johon paneelit tallennetaan (oletus: ./paneelit)")
    parser.add_argument("--hiljainen", action="store_true", help="Ei tulosteita jokaisesta kuvasta")
    args = parser.parse_args()

    leikkaa_kuvat(args.kuvat, args.paneelit, verbose=not args.hiljainen)
