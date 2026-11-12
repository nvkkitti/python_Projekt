"""Saját modul (NKK): költési adatok generálása, CSV kezelése és értékelése.

Hallgató: Novák Kitti Katalin (P5MJQX), monogram: NKK
"""
import csv
import random
import statistics

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

CIMKEK = {
    "kaja": "Kaja",
    "lakas": "Lakás",
    "utazas": "Utazás",
    "szorakozas": "Szórakozás",
    "ruha": "Ruha",
    "egeszseg": "Egészség",
    "oktatas": "Oktatás",
    "egyeb": "Egyéb",
}

SAV = 0.15          
MIN_HASONLO = 10    
KUSZOB = 0.10       

def fizetes_generalas_NKK(rng: random.Random) -> int:
    """Havi nettó fizetés Ft-ban, 200 ezer és 1,5 millió között, 1000-esre kerekítve."""
    ertek = rng.lognormvariate(12.9, 0.4)  
    ertek = min(max(ertek, 200_000), 1_500_000)
    return int(round(ertek, -3))


def ugyfel_generalas_NKK(rng: random.Random, ugyfel_id: int) -> dict:
    """Egy ügyfél fizetése és kategóriánkénti költése; az összeg sosem haladja meg a fizetést."""
    fizetes = fizetes_generalas_NKK(rng)
    szint = min(fizetes / 1_500_000, 1)
    
    keret = fizetes * (rng.uniform(0.55, 1.0) - 0.1 * szint)

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
        
        sor[nev] = int(keret * suly / osszeg // 100 * 100)
    return sor


def adat_generalas_NKK(db: int, seed: int | None = None) -> list[dict]:
    rng = random.Random(seed)
    return [ugyfel_generalas_NKK(rng, i) for i in range(1, db + 1)]


def csv_mentes_NKK(sorok: list[dict], fajl: str) -> None:
    mezok = ["ugyfel_id", "fizetes", *KATEGORIAK]
    
    with open(fajl, "w", newline="", encoding="utf-8-sig") as f:
        iro = csv.DictWriter(f, fieldnames=mezok)
        iro.writeheader()
        iro.writerows(sorok)


def csv_beolvas_NKK(fajl: str) -> list[dict]:
    with open(fajl, newline="", encoding="utf-8-sig") as f:
        return [{m: int(v) for m, v in sor.items()} for sor in csv.DictReader(f)]


def koltes_ellenorzes_NKK(fizetes: int, sajat: dict[str, int]) -> bool:
    """Igaz, ha az ügyfél csak a bevételét költi (az összeg nem haladja meg a fizetést)."""
    return sum(sajat.values()) <= fizetes


def forint_formaz_NKK(x: float) -> str:
    return f"{x:,.0f}".replace(",", " ")


class KoltesElemzoNKK:
    """Egy ügyfél költéseit hasonlítja a hasonló fizetésű ügyfelekéhez."""

    def __init__(self, sorok: list[dict], sav: float = SAV,
                 min_hasonlo: int = MIN_HASONLO, kuszob: float = KUSZOB) -> None:
        self.sorok = sorok
        self.sav = sav
        self.min_hasonlo = min_hasonlo
        self.kuszob = kuszob

    def ugyfel_NKK(self, ugyfel_id: int) -> dict | None:
        return next((s for s in self.sorok if s["ugyfel_id"] == ugyfel_id), None)

    def hasonlok_NKK(self, fizetes: int, kiveve_id: int | None = None) -> list[dict]:
        """A +/-sáv fizetésű ügyfelek; ha kevés van, a fizetés szerint legközelebbiek."""
        mezo = [s for s in self.sorok if s["ugyfel_id"] != kiveve_id]
        savban = [s for s in mezo if abs(s["fizetes"] - fizetes) <= self.sav * fizetes]
        if len(savban) >= self.min_hasonlo:
            return savban
        return sorted(mezo, key=lambda s: abs(s["fizetes"] - fizetes))[:self.min_hasonlo]

    def minosit_NKK(self, sajat: float, atlag: float) -> str:
        if atlag == 0:
            return "átlagos" if sajat == 0 else "több"
        elteres = (sajat - atlag) / atlag
        if elteres > self.kuszob:
            return "több"
        if elteres < -self.kuszob:
            return "kevesebb"
        return "átlagos"

    def osszehasonlit_NKK(self, fizetes: int, sajat: dict[str, int],
                          kiveve_id: int | None = None) -> list[dict]:
        """Kategóriánként egy-egy sor; az utolsó az összesítés ("osszesen")."""
        hasonlo = self.hasonlok_NKK(fizetes, kiveve_id)
        sorok = []
        for k in KATEGORIAK:
            ertekek = [s[k] for s in hasonlo]
            sorok.append(self._sor_NKK(k, sajat.get(k, 0), statistics.mean(ertekek), ertekek))
        osszesen = [sum(s[k] for k in KATEGORIAK) for s in hasonlo]
        sorok.append(self._sor_NKK("osszesen", sum(sajat.get(k, 0) for k in KATEGORIAK),
                                   statistics.mean(osszesen), osszesen))
        return sorok

    def _sor_NKK(self, kategoria: str, sajat: int, atlag: float, ertekek: list[int]) -> dict:
        return {
            "kategoria": kategoria,
            "sajat": sajat,
            "atlag": atlag,
            "elteres": sajat - atlag,
            "szazalek": (sajat - atlag) / atlag if atlag else 0.0,
            
            "helyezes": sum(1 for e in ertekek if e < sajat) / len(ertekek),
            "minosites": self.minosit_NKK(sajat, atlag),
        }
