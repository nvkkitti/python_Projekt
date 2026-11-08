"""Véletlenszerű költési lista generálása CSV fájlba.

Minden ügyfél havi fizetéssel rendelkezik, és legfeljebb ennyit költhet el
(a kategóriánkénti költések összege nem haladhatja meg a fizetést).

Használat:
    python koltes_generator.py [--db 500] [--fajl koltesek.csv] [--seed 42]
"""
import argparse
import csv
import random

# kategória -> alap arány a költött összegből (a fizetés növekedésével némelyik eltolódik)
KATEGORIAK = {
    "kaja": 0.28,
    "lakas": 0.30,
    "utazas": 0.10,
    "szorakozas": 0.07,
    "ruha": 0.06,
    "egeszseg": 0.04,
    "oktatas": 0.03,
    "egyeb": 0.12,
}


def fizetes_generalas(rng: random.Random) -> int:
    """Havi nettó fizetés Ft-ban, 200 ezer és 1,5 millió között, 1000-esre kerekítve."""
    ertek = rng.lognormvariate(12.9, 0.4)  # medián kb. 400 ezer
    ertek = min(max(ertek, 200_000), 1_500_000)
    return int(round(ertek, -3))


def ugyfel_generalas(rng: random.Random, ugyfel_id: int) -> dict:
    fizetes = fizetes_generalas(rng)
    # a magasabb fizetésűek az arányaiban kisebb részt költik el (többet megtakarítanak)
    koltesi_hanyad = rng.uniform(0.55, 1.0) - 0.1 * min(fizetes / 1_500_000, 1)
    keret = fizetes * koltesi_hanyad

    # a magasabb fizetésűek a lakásra kisebb, szórakozásra/utazásra nagyobb arányt költenek
    szint = min(fizetes / 1_500_000, 1)
    sulyok = {}
    for nev, alap in KATEGORIAK.items():
        if nev == "lakas":
            alap *= 1.2 - 0.6 * szint
        elif nev in ("utazas", "szorakozas", "ruha"):
            alap *= 0.8 + 0.8 * szint
        sulyok[nev] = alap * rng.uniform(0.4, 1.8)
    osszeg = sum(sulyok.values())

    sor = {"ugyfel_id": ugyfel_id, "fizetes": fizetes}
    for nev, suly in sulyok.items():
        # lefelé kerekítés 100 Ft-ra: az összeg így sosem lépi túl a fizetést
        sor[nev] = int(keret * suly / osszeg // 100 * 100)
    return sor


def mentes(db: int, fajl: str, seed: int | None = None) -> int:
    rng = random.Random(seed)
    mezok = ["ugyfel_id", "fizetes", *KATEGORIAK]
    sorok = [ugyfel_generalas(rng, i) for i in range(1, db + 1)]

    for sor in sorok:
        assert sum(sor[k] for k in KATEGORIAK) <= sor["fizetes"]

    # utf-8-sig: az Excel is helyesen nyitja meg
    with open(fajl, "w", newline="", encoding="utf-8-sig") as f:
        iro = csv.DictWriter(f, fieldnames=mezok)
        iro.writeheader()
        iro.writerows(sorok)
    return len(sorok)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", type=int, default=500, help="ügyfelek száma")
    parser.add_argument("--fajl", default="koltesek.csv", help="kimeneti CSV")
    parser.add_argument("--seed", type=int, default=None, help="reprodukálható véletlen")
    args = parser.parse_args()

    db = mentes(args.db, args.fajl, args.seed)
    print(f"{db} ügyfél mentve: {args.fajl}")


if __name__ == "__main__":
    main()
