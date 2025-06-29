EXE_VERSION = 'python'

DESC_TEXT_FORMAT = "Should contain: PointName(optional), lat, lon in any format (DD or DMS) and height as float"

DEF_MULTILIST = ["DEMO1 44°34\'31.54821\" 22°39\'02.48758\" 198.848",
                 "DEMO2 N44g34m31.54821s 22 39 02.48758 E 198.848",
                 "DEMO3 44.84821 22.48758 198.848m"]


PREGEX_DMS   = r"([NEne]?)(\d+)(\D+)(\d+)(\D+)([\d.]+)(\D)*"

# PREGEX_DMS4  = r"((?P<name>([\w\-\_\s\S])*)(?P<s0>[\s,;\t]))*(?P<lat>(([NEne]?)(?P<lat_d>[4][345678]+)(\D+)(?P<lat_m>\d+)(\D+)(?P<lat_s>[\d]{1,2}([.][\d]+)*)|(?P<lat_dd>[4][345678]\.[\d]*))(\D)*)(?P<s1>[\s,;\t])(?P<lon>(([NEne]?)(?P<lon_d>[23][\d]+)(\D+)(?P<lon_m>\d+)(\D+)(?P<lon_s>[\d]{1,2}([.][\d]+)*)|(?P<lon_dd>[23][\d]\.[\d]*))(\D)*)(?P<s2>[\s,;\t])(?P<height>[\d.]+)"
# PREGEX_DMS4_FLIPPED = r"((?P<name>([\w\-\_\s\S])*)(?P<s0>[\s,;\t]))*(?P<lat>(([NEne]?)(?P<lat_d>[23][\d]+)(\D+)(?P<lat_m>\d+)(\D+)(?P<lat_s>[\d]{1,2}([.][\d]+)*)|(?P<lat_dd>[23][\d]\.[\d]*))(\D)*)(?P<s1>[\s,;\t])(?P<lon>(([NEne]?)(?P<lon_d>[4][345678]+)(\D+)(?P<lon_m>\d+)(\D+)(?P<lon_s>[\d]{1,2}([.][\d]+)*)|(?P<lon_dd>[4][345678]\.[\d]*))(\D)*)(?P<s2>[\s,;\t])(?P<height>[\d.]+)"

PREGEX_DMS4         = r"(?:(?P<name>(?![NnEe]\d|[4-5]\d)[^\d\t\r\n][^\t\r\n]*?)(?P<s0>[\s,])+)?(?P<lat>(([NEne]?)(?P<lat_d>[4][345678]+)(\D+)(?P<lat_m>\d+)(\D+)(?P<lat_s>[\d]{1,2}([.][\d]+)*)|(?P<lat_dd>[4][345678]\.[\d]*))(\D)*)(?P<s1>[\s,;\t])(?P<lon>(([NEne]?)(?P<lon_d>[23][\d]+)(\D+)(?P<lon_m>\d+)(\D+)(?P<lon_s>[\d]{1,2}([.][\d]+)*)|(?P<lon_dd>[23][\d]\.[\d]*))(\D)*)(?P<s2>[\s,;\t])(?P<height>[\d.]+)"
PREGEX_DMS4_FLIPPED = r"(?:(?P<name>(?![NnEe]\d|[4-5]\d)[^\d\t\r\n][^\t\r\n]*?)(?P<s0>[\s,])+)?(?P<lon>(([NEne]?)(?P<lon_d>2[3-9]|3[0-6])(\D+)(?P<lon_m>\d+)(\D+)(?P<lon_s>[\d]{1,2}([.][\d]+)*)|(?P<lon_dd>(2[3-9]|3[0-6])\.[\d]*))(\D)*)(?P<s1>[\s,;\t])(?P<lat>(([NEne]?)(?P<lat_d>[4][345678]+)(\D+)(?P<lat_m>\d+)(\D+)(?P<lat_s>[\d]{1,2}([.][\d]+)*)|(?P<lat_dd>[4][345678]\.[\d]*))(\D)*)(?P<s2>[\s,;\t])(?P<height>[\d.]+)"

# name in test (?P<name>(?![NnEe]\d|\d{2}[\s\d])[^ \t\r\n][^\t\r\n]*?)

# Name and separator regex, split into two parts for clarity
PREGEX_NAME = r"(?:(?P<name>(?![NnEe]\d|[4-5]\d)[^\d\t\r\n][^\t\r\n]*?))?"
PREGEX_S0   = r"(?P<s0>[\s,]+)?"
PREGEX_LAT = r"(?P<lat>(([NEne]?)(?P<lat_d>[4][345678]+)(\D+)(?P<lat_m>\d+)(\D+)(?P<lat_s>[\d]{1,2}([.][\d]+)*)|(?P<lat_dd>[4][345678]\.[\d]*))(\D)*)"
PREGEX_LON = r"(?P<lon>(([NEne]?)(?P<lon_d>2[3-9]|3[0-6])(\D+)(?P<lon_m>\d+)(\D+)(?P<lon_s>[\d]{1,2}([.][\d]+)*)|(?P<lon_dd>(2[3-9]|3[0-6])\.[\d]*))(\D)*)"
PREGEX_S1 = r"(?P<s1>[\s,;\t])"
PREGEX_S2 = r"(?P<s2>[\s,;\t])"
PREGEX_HEIGHT = r"(?P<height>[\d.]+)"

PREGEX_4_MERGE_LATLON = (
  PREGEX_NAME +
  PREGEX_S0 +
  PREGEX_LAT +
  PREGEX_S1 +
  PREGEX_LON +
  PREGEX_S2 +
  PREGEX_HEIGHT
)

PREGEX_4_MERGE_LONLAT = (
  PREGEX_NAME +
  PREGEX_S0 +
  PREGEX_LON +
  PREGEX_S1 +
  PREGEX_LAT +
  PREGEX_S2 +
  PREGEX_HEIGHT
)

# PREGEX_DMS4 = PREGEX_4_MERGE_LATLON
# PREGEX_DMS4_FLIPPED = PREGEX_4_MERGE_LONLAT

INFO_TEXT = """
The DXF file is in projected coordinates, EPSG:3844 (Stereo70) with heights referenced to Black Sea 1975.

Fisierul DXF este in coordonate EPSG:3844 (Stereo70) cu inaltimi referite la Marea Neagra 1975 (sistem local romanesc).

https://epsg.io/3844
"""

PRJ_CONTENT = """PROJCS["Pulkovo 1942(58) / Stereo70",
GEOGCS["Pulkovo 1942(58)",
    DATUM["Pulkovo_1942_58",
        SPHEROID["Krasovsky 1940",6378245,298.3,
            AUTHORITY["EPSG","7024"]],
        AUTHORITY["EPSG","6170"]],
    PRIMEM["Greenwich",0,
        AUTHORITY["EPSG","8901"]],
    UNIT["degree",0.0174532925199433,
        AUTHORITY["EPSG","9122"]],
    AUTHORITY["EPSG","4170"]],
PROJECTION["Oblique_Stereographic"],
PARAMETER["latitude_of_origin",46],
PARAMETER["central_meridian",25],
PARAMETER["scale_factor",0.99975],
PARAMETER["false_easting",500000],
PARAMETER["false_northing",500000],
UNIT["metre",1,
    AUTHORITY["EPSG","9001"]],
AUTHORITY["EPSG","3844"]],
VERT_CS["Black Sea 1975 Height",
    VERT_DATUM["Black Sea 1975",2005,
        AUTHORITY["CUSTOM","BlackSea_1975"]],
    UNIT["metre",1,
        AUTHORITY["EPSG","9001"]],
    AXIS["Gravity-related Height",UP]]]"""

SHP_PRJ_CONTENT="""PROJCS["Pulkovo_1942_Adj_58_Stereo_70",GEOGCS["GCS_Pulkovo_1942_Adj_1958",DATUM["D_Pulkovo_1942_Adj_1958",SPHEROID["Krasovsky_1940",6378245.0,298.3]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Double_Stereographic"],PARAMETER["False_Easting",500000.0],PARAMETER["False_Northing",500000.0],PARAMETER["Central_Meridian",25.0],PARAMETER["Scale_Factor",0.99975],PARAMETER["Latitude_Of_Origin",46.0],UNIT["Meter",1.0]],VERTCS["BlackSea_1975",VDATUM["BlackSea_1975"],PARAMETER["Vertical_Shift",0.0],PARAMETER["Direction",1.0],UNIT["Meter",1.0]]"""


ETRS_INPUT_HELP="""
<p>
  <strong style="color: #1e90ff;">Notă privind formatul de intrare</strong>
</p>
<p>
  Unul dintre cele mai mari avantaje ale ROMGEO este parserul flexibil pentru datele de intrare.
  Poți lipi coordonate într-o gamă largă de formate lizibile de om, atâta timp cât se respectă următoarea structură:
</p>

<p>
  <strong style="color: #4682b4;">Format general pe linie</strong>
</p>
<pre>[NumePunct]  [Separator]  Latitudine  [Separator]  Longitudine  [Separator]  Altitudine</pre>

<ul style="margin-top: 6px; padding-left: 18px;">
  <li><strong>NumePunct</strong>: opțional (alfanumeric), trebuie să înceapă cu o literă</li>
  <li><strong>Separatoare</strong>: spațiu, tab, virgulă, punct și virgulă, bară verticală <code>|</code> – pot fi mixate liber</li>
  <li><strong>Latitudine</strong>: trebuie să fie în limitele geografice ale României (~43,5° – 48,5°)</li>
  <li><strong>Longitudine</strong>: între 20° – 30°</li>
  <li><strong>Altitudine</strong>: obligatorie; poate fi pozitivă sau negativă, exprimată în metri (spre deosebire de TransDAT, unde era opțională)</li>
</ul>

<p>
  <strong style="color: #4682b4;">Exemple acceptate</strong>
</p>
<pre>
P01 45.123456 25.123456 120.5
45.123456,25.123456,112
Alpha|46.345;26.999;134.2
45 12 34 N 25 12 34 E 100
45°12′34″N, 25°12′34″E, 100
45 12.3456 N; 25 34.5678 E; 105
</pre>

<ul style="margin-top: 6px; padding-left: 18px;">
  <li>Se acceptă atât formate cu grade zecimale, cât și formate DMS (grade, minute, secunde)</li>
  <li>Valorile de minute/secunde se normalizează automat: ex. <code>100 minute</code> = <code>1 grad, 40 minute</code></li>
</ul>
"""

ST70_INPUT_HELP = """
<p>
  <strong style="color: #1e90ff;">Notă privind formatul de intrare STEREO70</strong>
</p>
<p>
  Poți introduce date în formatul național de proiecție STEREO70 (EPSG:3844), atâta timp cât se respectă structura de mai jos:
</p>

<p>
  <strong style="color: #4682b4;">Format general pe linie</strong>
</p>
<pre>[NumePunct]  [Separator]  X_nord  [Separator]  Y_est  [Separator]  H_mn</pre>

<ul style="margin-top: 6px; padding-left: 18px;">
  <li><strong>NumePunct</strong>: opțional (alfanumeric)</li>
  <li><strong>Separatoare</strong>: spațiu, tab, virgulă, punct și virgulă, bară verticală <code>|</code> – pot fi mixate liber</li>
  <li><strong>X_nord</strong>: Coordonata Nord (valoare între aproximativ 400.000 – 750.000 m pentru România)</li>
  <li><strong>Y_est</strong>: Coordonata Est (valoare între aproximativ 300.000 – 650.000 m pentru România)</li>
  <li><strong>H_mn</strong>: Înălțime normală (față de Marea Neagră 1975), în metri (poate fi negativă sau pozitivă)</li>
</ul>

<p>
  <strong style="color: #b22222;">Atenție:</strong> aplicația nu poate detecta automat dacă valorile <code>X</code> și <code>Y</code> sunt inversate. Verifică ordinea câmpurilor înainte de trimitere!
</p>

<p>
  <strong style="color: #4682b4;">Exemple acceptate</strong>
</p>
<pre>
P01 620123.45 335678.90 124.5
620123.45,335678.90,118
Alpha|623000;336100;137.2
</pre>
"""

ETRS_EXPORT_HELP = """
<p>
  <strong style="color: #b22222;">Notă privind exportul datelor</strong>
</p>
<p> La export, datele vor fi transformate din nou plecând de la valorile introduse, indiferent de conținutul afișat în zona de transformare. Fișierele <code>DXF</code>, <code>XLS</code> și <code>SHP</code> generate reflectă rezultatul unei transformări proaspete, aplicate direct pe datele de intrare.Aceasta asigură că exportul este mereu sincronizat cu datele inițiale, evitând erori cauzate de editări manuale. </p>
<p>
  <strong style="color: #4682b4;">Campurile fișierelor exportate</strong>
<ul style="margin-top: 6px; padding-left: 18px;">
  <li>
    <strong>Name</strong>: Eticheta punctului, dacă este specificată
  </li>
  <li>
    <strong>st70_X</strong>: Coordonata Nord în sistemul STEREO70 (EPSG:3844)
  </li>
  <li>
    <strong>st70_Y</strong>: Coordonata Est în sistemul STEREO70 (EPSG:3844)
  </li>
  <li>
    <strong>H_mn</strong>: Înălțime normală (față de Marea Neagră 1975)
  </li>
  <li>
    <strong>Latitude</strong>: Latitudine în sistemul ETRS89 (EPSG:4258)
  </li>
  <li>
    <strong>Longitude</strong>: Longitudine în sistemul ETRS89 (EPSG:4258)
  </li>
  <li>
    <strong>Height_Ellipsoidal</strong>: Altitudine elipsoidală
  </li>
</ul>
<p>
  <strong style="color: #8b0000;">Posibile erori în rezultatul exportat</strong>
<ul style="margin-top: 6px; padding-left: 18px;">
  <li>
    <code>NaN</code>: Reflectă o eroare de transformare sau o coordonată în afara zonei suportate
  </li>
  <li>
    <code>invalid format</code>: Formatul valorii introduse nu a putut fi interpretat corect
  </li>
</ul>
"""

ST70_EXPORT_HELP = ETRS_EXPORT_HELP

EXPORT_POPUP_HELP = """<div>
  <strong>🛈Notă:</strong> La export, datele vor fi transformate din nou plecând de la valorile introduse, indiferent de conținutul afișat în zona de transformare.
  Fișierele <code>DXF</code>, <code>XLS</code> și <code>SHP</code> generate reflectă rezultatul unei transformări proaspete, aplicate direct pe datele de intrare.</span>
  <br/><span>Aceasta asigură că exportul este mereu sincronizat cu datele inițiale, evitând erori cauzate de editări manuale.</span>
</div>
"""

EXPORT_POPUP_HELP_DXF_ETRS = EXPORT_POPUP_HELP
EXPORT_POPUP_HELP_SHP_ETRS = EXPORT_POPUP_HELP
EXPORT_POPUP_HELP_XLS_ETRS = EXPORT_POPUP_HELP

EXPORT_POPUP_HELP_DXF_ST70 = EXPORT_POPUP_HELP
EXPORT_POPUP_HELP_SHP_ST70 = EXPORT_POPUP_HELP
EXPORT_POPUP_HELP_XLS_ST70 = EXPORT_POPUP_HELP


TMP_ROOT = "/tmp/api-shapefiles"

ZBOX_RO_ETRS = [-100, 2600]
ZBOX_RO_ST70 = [ -50, 2600]

BBOX_RO_ST70 = [116424.61, 215561.44, 1018946.51, 771863.53] 
BBOX_RO_ETRS = [    20.26,     43.44,      31.41,     48.27]

HIDE_INFO_ETRS_EXPORT = False
HIDE_INFO_ETRS_IMPORT = False

HIDE_INFO_ST70_EXPORT = False
HIDE_INFO_ST70_IMPORT = False

AUTO_UPDATE = True
CHECK_PRERELEASE = True
EXE_AUTO_UPDATE = True

DEV = False

URL_FAQ = "https://romgeo.ro/faq"
URL_FEEDBACK = "https://romgeo.ro/feedback"

LOGLEVEL = 'info'

SWAP_XY_DXF = False
SWAP_XY_SHP = True 
