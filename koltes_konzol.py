"""Interaktív konzolos menü a költési adatok generálásához és értékeléséhez.

Használat:
    python koltes_konzol.py
"""
import os
import sys

import koltes_ertekeles as ert
import koltes_generator as gen

FAJL = "koltesek.csv"

MENU = """
==============================
  KÖLTÉSI ÉRTÉKELŐ
==============================
 1) Adatok (újra)generálása
 2) Meglévő ügyfél értékelése (azonosító alapján)
 3) Saját fizetés és költések megadása
 4) Hasonló fizetésűek átlaga
 0) Kilépés
"""


def szam_beker(kerdes: str, alap: int | None = None) -> int | None:
    """Egész számot kér; üres bevitelnél az alapértéket adja, hibánál None-t."""
    szoveg = input(kerdes).strip().replace(" ", "")
    if not szoveg and alap is not None:
        return alap
    if not szoveg.isdigit():
        print("Hiba: egész, nemnegatív számot adjon meg.")
        return None
    return int(szoveg)


def betolt() -> tuple[list[str], list[dict]] | None:
    if not os.path.exists(FAJL):
        print(f"Még nincs {FAJL}. Először generáljon adatot (1-es menüpont).")
        return None
    return ert.beolvas(FAJL)


def generalas() -> None:
    db = szam_beker("Hány ügyfél legyen? [500]: ", 500)
    if not db:
        return
    print(f"{gen.mentes(db, FAJL)} ügyfél mentve: {FAJL}")


def ugyfel_ertekeles() -> None:
    adat = betolt()
    if adat is None:
        return
    kategoriak, sorok = adat
    azonosito = szam_beker(f"Ügyfél azonosítója (1-{len(sorok)}): ")
    talalt = next((s for s in sorok if s["ugyfel_id"] == azonosito), None)
    if talalt is None:
        print("Nincs ilyen azonosítójú ügyfél.")
        return
    print()
    ert.ertekeles(kategoriak, ert.hasonlok(sorok, talalt["fizetes"], azonosito),
                  talalt["fizetes"], talalt)


def sajat_adatok() -> None:
    adat = betolt()
    if adat is None:
        return
    kategoriak, sorok = adat
    fizetes = szam_beker("Havi fizetése (Ft): ")
    if not fizetes:
        return
    print("Havi költései (Enter = 0):")
    sajat = {}
    for k in kategoriak:
        ertek = szam_beker(f"  {k}: ", 0)
        if ertek is None:
            return
        sajat[k] = ertek
        if sum(sajat.values()) > fizetes:
            print("Csak a bevételét költheti: a költések összege meghaladja a fizetést.")
            return
    print()
    ert.ertekeles(kategoriak, ert.hasonlok(sorok, fizetes, None), fizetes, sajat)


def atlag() -> None:
    adat = betolt()
    if adat is None:
        return
    kategoriak, sorok = adat
    fizetes = szam_beker("Havi fizetés (Ft): ")
    if not fizetes:
        return
    print()
    ert.ertekeles(kategoriak, ert.hasonlok(sorok, fizetes, None), fizetes, None)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    muveletek = {"1": generalas, "2": ugyfel_ertekeles, "3": sajat_adatok, "4": atlag}
    while True:
        print(MENU)
        valasz = input("Választás: ").strip()
        if valasz == "0":
            break
        muvelet = muveletek.get(valasz)
        if muvelet is None:
            print("Ismeretlen menüpont.")
            continue
        print()
        muvelet()
        input("\nEnter a folytatáshoz...")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nKilépés.")
