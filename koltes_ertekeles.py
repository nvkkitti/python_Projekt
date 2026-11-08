"""Értékelés: egy adott fizetésű ügyfél a hozzá hasonlókhoz képest többet vagy
kevesebbet költ-e az egyes kategóriákra.

"Hozzá hasonló" = a fizetése a megadott fizetés +/- SAV százalékán belül van.
Ha így túl kevés a hasonló ügyfél, a fizetés szerint legközelebbi MIN_HASONLO
ügyfelet használjuk.

Használat:
    python koltes_ertekeles.py --ugyfel 17
    python koltes_ertekeles.py --fizetes 450000 --koltes kaja=120000 utazas=40000 ruha=30000
    python koltes_ertekeles.py --fizetes 450000        # csak a hasonlók átlaga
"""
import argparse
import csv
import statistics
import sys

SAV = 0.15          # +/-15% fizetési sáv
MIN_HASONLO = 10    # ennél kevesebb hasonló esetén a legközelebbieket vesszük
KUSZOB = 0.10       # +/-10% eltérésen belül "átlagos"


def beolvas(fajl: str) -> tuple[list[str], list[dict]]:
    with open(fajl, newline="", encoding="utf-8-sig") as f:
        olvaso = csv.DictReader(f)
        kategoriak = [m for m in olvaso.fieldnames if m not in ("ugyfel_id", "fizetes")]
        sorok = [{m: int(v) for m, v in sor.items()} for sor in olvaso]
    return kategoriak, sorok


def hasonlok(sorok: list[dict], fizetes: int, kiveve_id: int | None) -> list[dict]:
    mezo = [s for s in sorok if s["ugyfel_id"] != kiveve_id]
    savban = [s for s in mezo if abs(s["fizetes"] - fizetes) <= SAV * fizetes]
    if len(savban) >= MIN_HASONLO:
        return savban
    return sorted(mezo, key=lambda s: abs(s["fizetes"] - fizetes))[:MIN_HASONLO]


def minosites(sajat: float, atlag: float) -> str:
    if atlag == 0:
        return "átlagos" if sajat == 0 else "több"
    elteres = (sajat - atlag) / atlag
    if elteres > KUSZOB:
        return "TÖBBET költ"
    if elteres < -KUSZOB:
        return "KEVESEBBET költ"
    return "átlagos"


def ft(x: float) -> str:
    return f"{x:,.0f}".replace(",", " ")


def ertekeles(kategoriak: list[str], hasonlo: list[dict], fizetes: int,
              sajat: dict[str, int] | None) -> None:
    f_min = min(s["fizetes"] for s in hasonlo)
    f_max = max(s["fizetes"] for s in hasonlo)
    print(f"Fizetés: {ft(fizetes)} Ft | hasonló ügyfelek: {len(hasonlo)} db "
          f"(fizetésük {ft(f_min)} – {ft(f_max)} Ft)\n")

    if sajat is None:
        print(f"{'kategória':<12}{'átlag (Ft)':>12}{'medián (Ft)':>13}{'átlag (% fiz.)':>16}")
        for k in kategoriak:
            ertekek = [s[k] for s in hasonlo]
            atlag = statistics.mean(ertekek)
            print(f"{k:<12}{ft(atlag):>12}{ft(statistics.median(ertekek)):>13}"
                  f"{atlag / fizetes:>16.1%}")
        return

    print(f"{'kategória':<12}{'saját':>10}{'átlag':>10}{'eltérés':>10}{'%':>8}"
          f"{'helyezés*':>11}  értékelés")
    for k in kategoriak:
        ertekek = [s[k] for s in hasonlo]
        atlag = statistics.mean(ertekek)
        sz = sajat.get(k, 0)
        szazalek = (sz - atlag) / atlag if atlag else 0.0
        # hány hasonló költ ennél kevesebbet
        kevesebb = sum(1 for e in ertekek if e < sz) / len(ertekek)
        print(f"{k:<12}{ft(sz):>10}{ft(atlag):>10}{ft(sz - atlag):>10}{szazalek:>8.0%}"
              f"{kevesebb:>11.0%}  {minosites(sz, atlag)}")

    ossz = sum(sajat.get(k, 0) for k in kategoriak)
    ossz_atlag = statistics.mean(sum(s[k] for k in kategoriak) for s in hasonlo)
    szazalek = (ossz - ossz_atlag) / ossz_atlag if ossz_atlag else 0.0
    print(f"{'ÖSSZESEN':<12}{ft(ossz):>10}{ft(ossz_atlag):>10}{ft(ossz - ossz_atlag):>10}"
          f"{szazalek:>8.0%}{'':>11}  {minosites(ossz, ossz_atlag)}")
    print(f"\nMegtakarítás: {ft(fizetes - ossz)} Ft ({(fizetes - ossz) / fizetes:.0%} a fizetésből)")
    print("*helyezés: a hasonló ügyfelek hány %-a költ ennél kevesebbet az adott kategóriára")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fajl", default="koltesek.csv")
    parser.add_argument("--ugyfel", type=int, help="ügyfél azonosító a CSV-ből")
    parser.add_argument("--fizetes", type=int, help="havi fizetés Ft-ban")
    parser.add_argument("--koltes", nargs="*", default=[], metavar="KATEGORIA=OSSZEG",
                        help="saját költések, pl. kaja=120000")
    args = parser.parse_args()

    kategoriak, sorok = beolvas(args.fajl)

    if args.ugyfel is not None:
        talalt = next((s for s in sorok if s["ugyfel_id"] == args.ugyfel), None)
        if talalt is None:
            parser.error(f"nincs {args.ugyfel} azonosítójú ügyfél")
        fizetes, sajat, kiveve = talalt["fizetes"], talalt, args.ugyfel
    elif args.fizetes is not None:
        fizetes, kiveve = args.fizetes, None
        sajat = None
        if args.koltes:
            sajat = {}
            for elem in args.koltes:
                nev, _, ertek = elem.partition("=")
                if nev not in kategoriak or not ertek.isdigit():
                    parser.error(f"hibás költés: {elem!r} (kategóriák: {', '.join(kategoriak)})")
                sajat[nev] = int(ertek)
            if sum(sajat.values()) > fizetes:
                parser.error("csak a bevételét költheti: a költések összege meghaladja a fizetést")
    else:
        parser.error("add meg az --ugyfel vagy a --fizetes kapcsolót")

    ertekeles(kategoriak, hasonlok(sorok, fizetes, kiveve), fizetes, sajat)


if __name__ == "__main__":
    main()
