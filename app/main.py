"""Költési értékelő - grafikus felület.

Indítás:  python main.py

Hallgató: Novák Kitti Katalin (P5MJQX), monogram: NKK
"""
import math
import os
import tkinter as tk
from tkinter import messagebox, ttk

import sajat_modul_NKK as nkk

FAJL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "koltesek.csv")

SAJAT_SZIN = "#2f6fdb"
ATLAG_SZIN = "#8d99a6"
TOBB_SZIN = "#b3261e"
KEVESEBB_SZIN = "#1b7f3b"


class KoltesAblakNKK:
    """A főablak: bevitel (fizetés, költések), eredménytábla és oszlopdiagram."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.elemzo: nkk.KoltesElemzoNKK | None = None
        self.eredmeny: list[dict] = []
        self.kiveve_id: int | None = None
        self._toltes = False

        root.title("app - Költési értékelő (NKK)")
        root.minsize(900, 600)
        self.felulet_epit_NKK()

        root.bind("<Return>", self.ertekel_NKK)
        root.bind("<Escape>", self.torles_NKK)
        self.adat_betolt_NKK()


    def felulet_epit_NKK(self) -> None:
        bal = ttk.Frame(self.root, padding=10)
        bal.pack(side="left", fill="y")
        jobb = ttk.Frame(self.root, padding=10)
        jobb.pack(side="right", fill="both", expand=True)

        betolt = ttk.LabelFrame(bal, text="Meglévő ügyfél", padding=8)
        betolt.pack(fill="x")
        self.id_var = tk.StringVar()
        id_mezo = ttk.Entry(betolt, textvariable=self.id_var, width=8)
        id_mezo.grid(row=0, column=0, padx=(0, 6))
        id_mezo.bind("<Return>", self.ugyfel_betolt_NKK)
        ttk.Button(betolt, text="Betöltés", command=self.ugyfel_betolt_NKK).grid(row=0, column=1)

        adatok = ttk.LabelFrame(bal, text="Saját adatok (Ft / hó)", padding=8)
        adatok.pack(fill="x", pady=10)
        self.fizetes_var = tk.StringVar()
        self.mezok = {"fizetes": self.fizetes_var}
        ttk.Label(adatok, text="Fizetés").grid(row=0, column=0, sticky="w")
        ttk.Entry(adatok, textvariable=self.fizetes_var, width=14).grid(row=0, column=1, pady=2)
        for sor, kulcs in enumerate(nkk.KATEGORIAK, start=1):
            var = tk.StringVar()
            self.mezok[kulcs] = var
            ttk.Label(adatok, text=nkk.CIMKEK[kulcs]).grid(row=sor, column=0, sticky="w")
            ttk.Entry(adatok, textvariable=var, width=14).grid(row=sor, column=1, pady=2)
        for var in self.mezok.values():
            var.trace_add("write", self.mezo_valtozas_NKK)
        self.osszeg_cimke = ttk.Label(adatok, text="")
        self.osszeg_cimke.grid(row=len(self.mezok), column=0, columnspan=2, sticky="w", pady=(6, 0))

        gombok = ttk.Frame(bal)
        gombok.pack(fill="x")
        ttk.Button(gombok, text="Értékelés (Enter)", command=self.ertekel_NKK).pack(
            side="left", expand=True, fill="x", padx=(0, 4))
        ttk.Button(gombok, text="Törlés (Esc)", command=self.torles_NKK).pack(
            side="left", expand=True, fill="x")

        halmaz = ttk.LabelFrame(bal, text="Adathalmaz", padding=8)
        halmaz.pack(fill="x", pady=10)
        ttk.Label(halmaz, text="Ügyfelek száma").grid(row=0, column=0, sticky="w")
        self.db_var = tk.StringVar(value="500")
        ttk.Spinbox(halmaz, from_=50, to=5000, increment=50, textvariable=self.db_var,
                    width=7).grid(row=0, column=1, padx=6)
        ttk.Button(halmaz, text="Adatok generálása", command=self.generalas_NKK).grid(
            row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        self.allapot_cimke = ttk.Label(halmaz, text="", wraplength=200, justify="left")
        self.allapot_cimke.grid(row=2, column=0, columnspan=2, sticky="w", pady=(6, 0))

        oszlopok = ("kategoria", "sajat", "atlag", "elteres", "szazalek", "helyezes", "minosites")
        fejlecek = ("Kategória", "Saját", "Átlag", "Eltérés", "%", "Helyezés*", "Értékelés")
        self.tabla = ttk.Treeview(jobb, columns=oszlopok, show="headings", height=9)
        for oszlop, fejlec in zip(oszlopok, fejlecek):
            self.tabla.heading(oszlop, text=fejlec)
            self.tabla.column(oszlop, width=95, anchor="w" if oszlop == "kategoria" else "e")
        self.tabla.tag_configure("tobb", foreground=TOBB_SZIN)
        self.tabla.tag_configure("kevesebb", foreground=KEVESEBB_SZIN)
        self.tabla.tag_configure("osszesen", font=("TkDefaultFont", 9, "bold"))
        self.tabla.pack(fill="x")

        self.osszegzes_cimke = ttk.Label(jobb, text="Adja meg a fizetést és a költéseit, majd Enter.",
                                         wraplength=640, justify="left")
        self.osszegzes_cimke.pack(anchor="w", pady=(6, 0))
        ttk.Label(jobb, text="*Helyezés: a hasonló ügyfelek hány %-a költ ennél kevesebbet.",
                  foreground="#666").pack(anchor="w")

        self.vaszon = tk.Canvas(jobb, background="white", highlightthickness=1,
                                highlightbackground="#ccc", height=260)
        self.vaszon.pack(fill="both", expand=True, pady=(8, 0))
        self.vaszon.bind("<Configure>", self.diagram_rajzol_NKK)


    def adat_betolt_NKK(self) -> None:
        """Betölti a CSV-t; ha nincs vagy hibás, újat generál."""
        try:
            sorok = nkk.csv_beolvas_NKK(FAJL)
            self.allapot_cimke.config(text=f"{len(sorok)} ügyfél betöltve.")
        except (OSError, ValueError, KeyError):
            self.generalas_NKK()
            return
        self.elemzo = nkk.KoltesElemzoNKK(sorok)

    def generalas_NKK(self) -> None:
        db = self.db_var.get().strip()
        if not db.isdigit() or not 10 <= int(db) <= 100_000:
            messagebox.showerror("Hiba", "Az ügyfelek száma 10 és 100000 közötti egész szám legyen.")
            return
        sorok = nkk.adat_generalas_NKK(int(db))
        nkk.csv_mentes_NKK(sorok, FAJL)
        self.elemzo = nkk.KoltesElemzoNKK(sorok)
        self.allapot_cimke.config(text=f"{len(sorok)} ügyfél generálva és mentve:\n{os.path.basename(FAJL)}")

    def ugyfel_betolt_NKK(self, event: tk.Event | None = None) -> str:
        azonosito = self.id_var.get().strip()
        ugyfel = self.elemzo.ugyfel_NKK(int(azonosito)) if azonosito.isdigit() else None
        if ugyfel is None:
            messagebox.showerror("Hiba", "Nincs ilyen azonosítójú ügyfél.")
            return "break"
        self._toltes = True
        self.fizetes_var.set(str(ugyfel["fizetes"]))
        for kulcs in nkk.KATEGORIAK:
            self.mezok[kulcs].set(str(ugyfel[kulcs]))
        self._toltes = False
        self.kiveve_id = ugyfel["ugyfel_id"]
        self.osszeg_frissit_NKK()
        self.ertekel_NKK()
        return "break" 


    def mezo_valtozas_NKK(self, *_args) -> None:
        if not self._toltes:
            self.kiveve_id = None
            self.osszeg_frissit_NKK()

    def osszeg_frissit_NKK(self) -> None:
        try:
            fizetes = self.szam_NKK(self.fizetes_var.get())
            kiadas = sum(self.szam_NKK(self.mezok[k].get()) for k in nkk.KATEGORIAK)
        except ValueError:
            self.osszeg_cimke.config(text="Csak egész számot írjon!", foreground=TOBB_SZIN)
            return
        szoveg = f"Elköltve: {nkk.forint_formaz_NKK(kiadas)} / {nkk.forint_formaz_NKK(fizetes)} Ft"
        tullep = kiadas > fizetes
        self.osszeg_cimke.config(text=szoveg, foreground=TOBB_SZIN if tullep else "")

    def torles_NKK(self, event: tk.Event | None = None) -> None:
        self._toltes = True
        for var in self.mezok.values():
            var.set("")
        self._toltes = False
        self.kiveve_id = None
        self.eredmeny = []
        self.tabla.delete(*self.tabla.get_children())
        self.osszegzes_cimke.config(text="Adja meg a fizetést és a költéseit, majd Enter.")
        self.osszeg_frissit_NKK()
        self.diagram_rajzol_NKK()

    def ertekel_NKK(self, event: tk.Event | None = None) -> None:
        try:
            fizetes = self.szam_NKK(self.fizetes_var.get())
            sajat = {k: self.szam_NKK(self.mezok[k].get()) for k in nkk.KATEGORIAK}
        except ValueError:
            messagebox.showerror("Hiba", "Csak nemnegatív egész számot írjon a mezőkbe.")
            return
        if fizetes <= 0:
            messagebox.showerror("Hiba", "Adja meg a havi fizetést.")
            return
        if not nkk.koltes_ellenorzes_NKK(fizetes, sajat):
            messagebox.showerror("Hiba", "Csak a bevételét költheti: a költések összege "
                                         "meghaladja a fizetést.")
            return

        self.eredmeny = self.elemzo.osszehasonlit_NKK(fizetes, sajat, self.kiveve_id)
        self.tabla_kitolt_NKK()
        hasonlo_db = len(self.elemzo.hasonlok_NKK(fizetes, self.kiveve_id))
        megtakaritas = fizetes - self.eredmeny[-1]["sajat"]
        self.osszegzes_cimke.config(
            text=f"{hasonlo_db} hasonló fizetésű ügyfélhez képest. "
                 f"Megtakarítás: {nkk.forint_formaz_NKK(megtakaritas)} Ft "
                 f"({megtakaritas / fizetes:.0%} a fizetésből).")
        self.diagram_rajzol_NKK()


    @staticmethod
    def szam_NKK(szoveg: str) -> int:
        szoveg = szoveg.replace(" ", "")
        if not szoveg:
            return 0
        if not szoveg.isdigit():
            raise ValueError(szoveg)
        return int(szoveg)

    def tabla_kitolt_NKK(self) -> None:
        self.tabla.delete(*self.tabla.get_children())
        for s in self.eredmeny:
            osszesen = s["kategoria"] == "osszesen"
            nev = "ÖSSZESEN" if osszesen else nkk.CIMKEK[s["kategoria"]]
            tagek = ["osszesen"] if osszesen else []
            if s["minosites"] in ("több", "kevesebb"):
                tagek.append("tobb" if s["minosites"] == "több" else "kevesebb")
            self.tabla.insert("", "end", tags=tagek, values=(
                nev, nkk.forint_formaz_NKK(s["sajat"]), nkk.forint_formaz_NKK(s["atlag"]),
                nkk.forint_formaz_NKK(s["elteres"]), f"{s['szazalek']:+.0%}",
                "" if osszesen else f"{s['helyezes']:.0%}",
                {"több": "TÖBBET költ", "kevesebb": "KEVESEBBET költ"}.get(s["minosites"], "átlagos")))

    def diagram_rajzol_NKK(self, event: tk.Event | None = None) -> None:
        c = self.vaszon
        c.delete("all")
        szeles, magas = c.winfo_width(), c.winfo_height()
        if not self.eredmeny:
            c.create_text(szeles / 2, magas / 2, text="Az értékelés után itt jelenik meg a diagram.",
                          fill="#888")
            return

        sorok = self.eredmeny[:-1]
        bal, jobb, fent, lent = 75, 15, 34, 28
        terulet_m, terulet_sz = magas - fent - lent, szeles - bal - jobb
        felso = self.szep_maximum_NKK(max(max(s["sajat"], s["atlag"]) for s in sorok))

        for i in range(5):
            ertek = felso * i / 4
            y = fent + terulet_m * (1 - i / 4)
            c.create_line(bal, y, szeles - jobb, y, fill="#e3e6ea")
            c.create_text(bal - 6, y, text=nkk.forint_formaz_NKK(ertek), anchor="e", fill="#555",
                          font=("TkDefaultFont", 8))

        csoport = terulet_sz / len(sorok)
        oszlop = csoport * 0.3
        alap = fent + terulet_m
        for i, s in enumerate(sorok):
            kozep = bal + csoport * (i + 0.5)
            for eltolas, kulcs, szin in ((-oszlop, "sajat", SAJAT_SZIN), (0, "atlag", ATLAG_SZIN)):
                x0 = kozep + eltolas
                c.create_rectangle(x0, alap - terulet_m * s[kulcs] / felso, x0 + oszlop, alap,
                                   fill=szin, outline="")
            c.create_text(kozep, alap + 4, text=nkk.CIMKEK[s["kategoria"]], anchor="n", fill="#333",
                          font=("TkDefaultFont", 8))

        for x, szin, nev in ((bal, SAJAT_SZIN, "Saját"), (bal + 70, ATLAG_SZIN, "Hasonlók átlaga")):
            c.create_rectangle(x, 10, x + 12, 22, fill=szin, outline="")
            c.create_text(x + 17, 16, text=nev, anchor="w", fill="#333")

    @staticmethod
    def szep_maximum_NKK(ertek: float) -> float:
        """A következő "kerek" érték (1, 2, 2.5, 5 x 10^n) az ordinátatengelyhez."""
        if ertek <= 0:
            return 1
        nagysag = 10 ** math.floor(math.log10(ertek))
        return next(m * nagysag for m in (1, 2, 2.5, 5, 10) if m * nagysag >= ertek)


def main() -> None:
    root = tk.Tk()
    KoltesAblakNKK(root)
    root.mainloop()


if __name__ == "__main__":
    main()
