# Cubix – simulator Rubik

Aplicatie Python (doar biblioteca standard) cu interfata web locala, plus motorul C++ imbunatatit.

## Pornire
```
python app.py            # deschide http://127.0.0.1:8765
python -m pytest         # teste (necesita pytest; testul de paritate are nevoie de g++)
```

## Ce face
- Cub 3D: trage ca sa il inclini, apasa sagetile din jurul fetei din fata ca sa rotesti un rand/coloana.
- **V (viteza de rotire)** in grade/secunda; **Pauza** opreste intre rotiri.
- **Straturi rotite odata** 1 sau 2 (randuri/coloane adiacente).
- **Pas compus**: aduna mai multe miscari (ex. 3x Rand 2 → si 2x Coloana 3 ↑); se numara ca UN pas.
- **Cub desfasurat** colorat, actualizat la fiecare rotire; casutele aluneca din pozitia veche in cea noua.
- **Cum se interschimba matricial**: arata numerele 1–6 din matrici, ciclul fetelor si perechile `Fata[r][c] → Dreapta[r][c]`.
- **Export**: `.html` colorat si `.txt` (ca MatriceDesfasurata.txt), fiecare pas cu numarul lui.
- **Auto-resolve**: anuleaza pasii inregistrati (cei mai noi primii), fiecare pas inversat ramane un pas.
  Nu este un solver general pentru orice stare: rezolva ce s-a amestecat prin aplicatie.

## C++
`cpp/rubik_engine.cpp` – aceeasi logica si aceeasi iesire text ca exportul `.txt`:
```
g++ -std=c++17 -O2 -o rubik_engine cpp/rubik_engine.cpp
./rubik_engine examples/exemplu.txt MatriceDesfasurata.txt
```
Corecturi fata de varianta initiala: verificarea „randuri consecutive” folosea `||` in loc de `&&`
(refuza mereu); rotirea unui strat exterior roteste acum si fata atinsa; mutarile sunt validate inainte de aplicare.

## Structura
`cubix/cube.py` modelul si permutarile · `session.py` istoric/amestecare/auto-resolve · `export.py` txt+html ·
`server.py` API local · `web/` interfata · `tests/` verificare contra unui model fizic 3D.
