## ROMGEO Table Convert GUI

![Version](https://img.shields.io/badge/version-v1.0.0-blue.svg)

[🇬🇧 English](README.md) | [🇷🇴 Română](README_RO.md)

**ROMGEO Table Convert GUI** este o aplicație desktop pentru Windows, concepută pentru a ajuta topografii, inginerii și profesioniștii GIS să convertească cu ușurință datele de puncte geospațiale. Aplicația oferă o interfață grafică prietenoasă pentru importul, vizualizarea și exportul tabelelor de coordonate.

### Funcționalități principale

- **Import date:** Încarcă tabele de puncte geospațiale din formate uzuale precum CSV sau Excel. Detectare extinsă a formatului de intrare.
- **Transformare coordonate:** Detectează automat inversarea coloanelor lat/lon sau convertește coordonatele după necesități.
- **Export DXF:** Salvează punctele filtrate și procesate în fișiere DXF, compatibile cu majoritatea programelor CAD.
- **Flux de lucru simplu:** Proiectată pentru procesarea rapidă și eficientă a datelor, fără a fi nevoie de software GIS complex.

Acest depozit oferă momentan doar fișierul EXE compilat, pentru distribuire și utilizare facilă. Codul sursă va fi disponibil într-o actualizare viitoare.

---

## Descarcare
Puteți descărca versiunea executabila compilată pentru Windows 64-bit de la 
[romgeo.ro](https://romgeo.ro/sdm_categories/romgeo/)


---

## Conversie online ETRS → Stereo70

Pentru conversia imediată a coordonatelor între sistemele **ETRS** și **Stereo70**, folosiți convertorul web oficial **ROMGEO** și API-ul aferent:

- **Demo web:** [ROMGEO Coordinate Transformation Demo](https://api.romgeo.ro/api/v1/demo.html#ro)
- **Documentație API:** [API Reference](https://api.romgeo.ro/api/v1/docs#)
- **Cod sursă API:** [cartografie-ro/romgeo-api pe GitHub](https://github.com/cartografie-ro/romgeo-api)

Nu este necesară instalarea sau crearea unui cont. Interfața web și API-ul utilizează același motor de conversie ca aplicația desktop — ideale pentru conversii rapide sau fluxuri de lucru automatizate.
