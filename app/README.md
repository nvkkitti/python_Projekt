# Költési értékelő

## Hallgató
- **Név:** Novák Kitti Katalin
- **Neptun-kód:** P5MJQX
- **Monogram:** NKK (a saját függvények, osztályok és a modul nevében szerepel)

## Feladat leírása

### Röviden
A program véletlenszerű költési listát generál ügyfelekről (fizetés, valamint kaja, lakás, utazás,
szórakozás, ruha, egészség, oktatás és egyéb költések), és CSV fájlba menti. Egy ügyfél csak a
bevételét költheti, vagyis a költései összege nem haladhatja meg a fizetését.

Az értékelés megmutatja, hogy egy megadott fizetésű ügyfél a hozzá hasonló fizetésűekhez képest
kategóriánként többet vagy kevesebbet költ-e. Hasonlónak a fizetésükben legfeljebb 15%-kal eltérő
ügyfelek számítanak. Ha ebben a sávban 10-nél kevesebb ügyfél van, a fizetés szerint legközelebbi 10 ügyfelet használja. Az eltérés 10%-ig „átlagos", efölött „TÖBBET költ", alatta „KEVESEBBET költ". Az eredményt táblázat és oszlopdiagram mutatja.

### Felhasználói leírás
- **Telepíteni nem kell semmit**: Python 3.10 vagy újabb szükséges (a `tkinter` a Python része).
- **Indítás:** a projekt mappájából `python main.py`
- Az első indításkor a program létrehozza a `koltesek.csv` fájlt (500 ügyféllel); ez futásidőben
  keletkező adatfájl, nem a forráskód része.
- **Használat:**
  1. *Meglévő ügyfél:* írja be az azonosítót (pl. 17), majd *Betöltés* (vagy Enter). A mezők
     kitöltődnek és az értékelés lefut. Az ügyfelet magát kihagyja az összehasonlításból.
  2. *Saját adatok:* írja be a havi fizetését és a költéseit (üres mező = 0), majd *Értékelés*
     (vagy Enter). Ha a költések összege meghaladja a fizetést, hibaüzenetet kap.
  3. *Törlés* (vagy Esc): kiüríti a mezőket és az eredményt.
  4. *Adatok generálása:* új, tetszőleges létszámú adathalmazt készít, és felülírja a CSV-t.

## Felépítés

### Fájlok
| Fájl | Szerep |
|------|--------|
| `README.md` | ez a leírás |
| `main.py` | indítás, grafikus felület (`tkinter`), eseménykezelés |
| `sajat_modul_NKK.py` | saját modul: adatgenerálás, CSV-kezelés, értékelés |

### Modul: `sajat_modul_NKK`
Saját függvények:
- `fizetes_generalas_NKK(rng)`: véletlen havi fizetés
- `ugyfel_generalas_NKK(rng, ugyfel_id)`: egy ügyfél fizetése és költései (az összeg ≤ fizetés)
- `adat_generalas_NKK(db, seed)`: ügyfelek listája
- `csv_mentes_NKK(sorok, fajl)` / `csv_beolvas_NKK(fajl)`: fájlkezelés (CSV)
- `koltes_ellenorzes_NKK(fizetes, sajat)`: csak a bevétel költhető el
- `forint_formaz_NKK(x)`: ezres tagolású összeg

### Osztályok
- `KoltesElemzoNKK` (modul): a hasonló ügyfelekkel való összehasonlítás. Metódusai:
  `ugyfel_NKK`, `hasonlok_NKK`, `minosit_NKK`, `osszehasonlit_NKK`, `_sor_NKK`
- `KoltesAblakNKK` (`main.py`): a főablak. Metódusai: `felulet_epit_NKK`, `adat_betolt_NKK`,
  `generalas_NKK`, `ugyfel_betolt_NKK`, `ertekel_NKK`, `torles_NKK`, `tabla_kitolt_NKK`,
  `diagram_rajzol_NKK` stb.

### Grafikus modul és eseménykezelés
A `tkinter` modult használja (ablak, `ttk.Treeview` táblázat, `Canvas` diagram). Eseményei:
gombnyomások (`command`), `<Return>` és `<Escape>` billentyűk, a beviteli mezők változása
(`trace_add`), valamint a diagram `<Configure>` eseménye, amely átméretezéskor újrarajzolja azt.
