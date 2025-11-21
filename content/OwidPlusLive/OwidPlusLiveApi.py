# Dieser Code hat mehrere Blöcke - diese sind mit >>>>>>> und <<<<<<< markiert.
# Folgende Blöcke sind enthalten:
#   - Dependencies / Importierte Module: Hier werden alle benötigten Module importiert.
#   - Basis-Konfiguration: Hier werden notwendige Konfigurationen und Konstanten definiert.
#   - Klassen: Hier werden die Datenklassen definiert, die als Übergabeparameter dienen.
#   - Private Hilfsfunktionen: Diese Funktionen sind intern und sollten nicht direkt aufgerufen werden.
#   - Öffentliche API-Funktionen: Diese Funktionen stehen dem Nutzer zur Verfügung.

# >>>>>>> Dependencies / Importierte Module >>>>>>>
from enum import IntEnum
from pydantic import BaseModel
import matplotlib.pyplot as plt
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import dayplot as dp
# <<<<<<< Ende Dependencies / Importierte Module <<<<<<<

# >>>>>>> Basis-Konfiguration (bitte hier nichts verändern) >>>>>>> 
# Basis URL der OWIDplusLIVE-API und Layer-Definitionen.
baseUrl = "https://www.owid.de/plus/live-2021/api/v3"

# Layer Mapping
layer = {"Wortform": 0, "Lemma": 1, "POS": 2}

# Lade verfügbare Jahre.
years = requests.get(f"{baseUrl}/years").json()
years.sort(reverse=True)

# Lade Normdaten für N-Gramme (1, 2, 3).
response = requests.get(f"{baseUrl}/norm").json()
normGram = {i + 1: dict(sorted(response[i].items())) for i in range(3)}

# Vordefinierte Granulationsfunktionen
predefinedGranulationFuncs = {
    "date": lambda d: d,
    "week": lambda d: d - pd.to_timedelta(d.dt.weekday, unit='d'),
    "month": lambda d: d - pd.to_timedelta(d.dt.day - 1, unit='d'),
    "quarter": lambda d: d - pd.to_timedelta((d.dt.day - 1) + (d.dt.month - 1) % 3 * 30, unit='d'),
    "year": lambda d: d - pd.to_timedelta(d.dt.dayofyear - 1, unit='d'),
}
# <<<<<<< Ende Basis-Konfiguration <<<<<<<

# >>>>>>> Klassen - dürfen nicht verändert werden, da sie als Übergabeparameter dienen. >>>>>>>
class LayerName(IntEnum):
    Wortform = 0
    Lemma = 1
    POS = 2

class SearchItem(BaseModel):
    """
    Repräsentiert ein Suchobjekt für die OWIDplusLIVE-API.

    Attribute:
        Position (int): Die Position des Tokens im N-Gramm (0-basiert).
        Layer (int): Die Ebene (z. B. Wortform, Lemma, POS).
        Token (str): Das zu suchende Token.
    """
    Position: int = 0
    Layer: int = 0
    Token: str = ""
    
    def __init__(self, Position=0, LayerName=LayerName.Wortform, Token=""):
        """
        Initialisiert ein SearchItem-Objekt.

        Args:
            Position (int): Die Position des Tokens im N-Gramm.
            LayerName (str): Der Name der Ebene (z. B. "Wortform", "Lemma" oder "POS").
            Token (str): Das zu suchende Token.
        """
        super().__init__(Position=Position, Layer=LayerName, Token=Token)
# <<<<<<< Ende Klassen <<<<<<<  

# >>>>>>> Private Hilfsfunktionen (beginnen mit __) - diese sollten nicht direkt aufgerufen werden. >>>>>>>
def __getFocusYear(year: int) -> list[int]:
    """
    Hilfsfunktion, um die Reihenfolge der Jahre zu bestimmen.

    Args:
        year (int): Das gewünschte Fokusjahr.

    Returns:
        list: Die Liste der Jahre in der Reihenfolge [Fokusjahr, alle anderen Jahre].
    """
    return [year] + [y for y in years if y != year] # Fokusjahr zuerst

def __normalizeData(n: int, df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalisiert (in pro Mio. Token) die Suchergebnisse basierend auf den Normdaten.
    Hinweis: Diese Funktion ist privat und sollte nicht direkt aufgerufen werden.

    Args:
        n (int): Die Anzahl der Tokens (N-Gramm).
        data (DataFrame): Die Suchergebnisse.

    Returns:
        DataFrame: Die Suchergebnisse ergänzt um eine Spalte mit den normalisierten Werten.
    """
    if "Frequenz (ppm)" in df.columns: # Sind die Daten bereits normalisiert, dann:
        df.drop(columns=["Frequenz (ppm)"], inplace=True) # Entfernen, um Duplikate zu vermeiden
    df["Datum"] = df["Datum"].astype(str) # Sicherstellen, dass Datum als String vorliegt
    df["Norm"] = df["Datum"].map(normGram[n]) # Normdaten zuordnen
    df["Frequenz (ppm)"] = df.apply(
        lambda row: (row["Frequenz"] / row["Norm"] * 1_000_000) if row["Norm"] > 0 else 0, # Berechnung der normalisierten Frequenz und Vermeidung von Division durch 0
        axis=1,
    )
    
    df = df.drop(columns=["Norm"]) # Norm-Spalte entfernen
    df["Datum"] = pd.to_datetime(df["Datum"], format="%Y-%m-%d", errors='coerce') # Datum in datetime-Format umwandeln
    
    return df.sort_values(by=["Datum"]).reset_index(drop=True) # Sortieren nach Datum und Index zurücksetzen

def __search(n: int, year: int, items: list[SearchItem]) -> pd.DataFrame:
    """
    Führt die eigentliche API-Abfrage durch. Diese Funktion ist privat und sollte
    nicht direkt aufgerufen werden. Verwenden Sie stattdessen die `searchN1`, 
    `searchN2`, `searchN3` oder `searchAdvanced`-Funktionen.

    Args:
        n (int): Die Anzahl der Tokens (N-Gramm).
        year (int): Das Fokusjahr.
        items (list[SearchItem]): Die Liste der Suchobjekte.

    Returns:
        DataFrame: Die Suchergebnisse.
    """
    frames = []
    for y in __getFocusYear(year): # Jahre in der richtigen Reihenfolge durchlaufen
        payload = {
            "N": n,
            "Year": y,
            "Items": [item.model_dump(exclude={"LayerName"}) for item in items], # Pydantic-Modelle in Dictionaries umwandeln
        }
        response = requests.post(f"{baseUrl}/search", json=payload) # API-Anfrage
        response.raise_for_status() # Fehlerbehandlung
        tmp = response.json() # Suchergebnisse extrahieren

        for ngram, value in tmp.items(): # Ergebnisse in DataFrame umwandeln
            for date, freq in value.items(): # Datum und Frequenz extrahieren
                frames.append({"N-Gramm": ngram, "Datum": date, "Frequenz": freq}) # Ergebnis speichern

    if not frames: # Keine Ergebnisse gefunden
        return pd.DataFrame(columns=["N-Gramm", "Datum", "Frequenz"]) # Leeren DataFrame zurückgeben

    df = pd.DataFrame(frames) # DataFrame erstellen
    df["Frequenz"] = df["Frequenz"].astype(int) # Frequenz in Integer umwandeln

    return __normalizeData(n, df) # Daten normalisieren und zurückgeben

def __lookup(year: int, layer: LayerName, wordformSet: set) -> dict:
    """
    Führt eine Lookup-Abfrage für die angegebenen Tokens in der angegebenen Ebene durch.
    Diese Funktion ist privat und sollte nicht direkt aufgerufen werden.

    Args:
        year (int): Das Fokusjahr.
        layer (LayerName): Die Ebene (Lemma oder POS).
        wordformSet (set[str]): Die Liste der zu suchenden Tokens.

    Returns:
        dict: Die Lookup-Ergebnisse.
    """
    wordformSet = list(wordformSet) # In Liste umwandeln, da Sets nicht serialisierbar sind
    payload = {
        "Layer": layer,
        "Year": year,
        "Query": " ".join(wordformSet), # Tokens als einzelner String
    }
    response = requests.post(f"{baseUrl}/lookup", json=payload) # API-Anfrage
    response.raise_for_status() # Fehlerbehandlung
    tmp = response.json().get("Lookup", "").split(" ") # Lookup-Ergebnisse extrahieren
    if len(tmp) != len(wordformSet): # Überprüfen, ob die Anzahl der Ergebnisse mit der Anzahl der Suchbegriffe übereinstimmt
        print(len(tmp), len(wordformSet)) # Debug-Ausgabe
        raise ValueError("Lookup-Ergebnisse stimmen nicht mit der Anzahl der Suchbegriffe überein.") # Fehler werfen
        
    res = {}
    for i in range(len(wordformSet)): # Ergebnisse in Dictionary umwandeln
        res[wordformSet[i]] = tmp[i] # Ergebnis speichern
    return res
# <<<<<<< Ende Private Hilfsfunktionen <<<<<<<

# >>>>>>> Öffentliche API-Funktionen >>>>>>>
def searchSimple(year: int, layer1: LayerName, token1: str, layer2: LayerName = LayerName.Wortform, token2: str = None, layer3: LayerName = LayerName.Wortform, token3: str = None) -> pd.DataFrame:
    """
    Führt eine N-Gramm-Suche mit N=1, 2 oder 3 Tokens durch.

    Args:
        year (int): Das Fokusjahr.
        layer1 (LayerName): Die Ebene des ersten Tokens (z. B. "Wortform", "Lemma" oder "POS").
        token1 (str): Das erste zu suchende Token.
        layer2 (LayerName): Die Ebene des zweiten Tokens (z. B. "Wortform", "Lemma" oder "POS").
        token2 (str): Das zweite zu suchende Token.
        layer3 (LayerName): Die Ebene des dritten Tokens (z. B. "Wortform", "Lemma" oder "POS").
        token3 (str): Das dritte zu suchende Token.

    Returns:
        pd.DataFrame: Die Suchergebnisse.
    """
    if token2 is None: # Nur ein Token
        return __search(1, year, [SearchItem(Position=0, LayerName=layer1, Token=token1)]) # N=1 Suche
    if token3 is None: # Zwei Tokens
        return __search(2, year, [SearchItem(Position=0, LayerName=layer1, Token=token1), # N=2 Suche
                                  SearchItem(Position=1, LayerName=layer2, Token=token2)])    
    return __search(3, year, [SearchItem(Position=0, LayerName=layer1, Token=token1), # Drei Tokens
                              SearchItem(Position=1, LayerName=layer2, Token=token2),
                              SearchItem(Position=2, LayerName=layer3, Token=token3)])

def searchAdvanced(year: int, n: int, items: list) -> pd.DataFrame:
    """
    Führt eine erweiterte N-Gramm-Suche mit beliebig vielen Layern durch.

    Args:
        year (int): Das Fokusjahr.
        n (int): Die Anzahl der Tokens (N-Gramm) - N=1 bis N=3 möglich.
        items (list[SearchItem]): Die Liste der Suchobjekte.
        normalize (bool): Gibt an, ob die Ergebnisse normalisiert werden sollen.

    Returns:
        pd.DataFrame: Die Suchergebnisse.
    """
    return __search(n, year, items) # N-Gramm Suche durchreichen

def applyGranulation(n: int, df: pd.DataFrame, granulationFunc) -> pd.DataFrame:
    """
    Wendet die angegebene Granulationsfunktion auf die Daten an.
    Args:
        n (int): Die Anzahl der Tokens (N-Gramm).
        df (pd.DataFrame): Die Suchergebnisse.
        granulationFunc (function): Die Granulationsfunktion (z. B. granulationFunc_by_week). 
        Die Variable predefinedGranulationFuncs enthält vordefinierte Funktionen ("date", "week", "month", "quarter", "year").
        
    Returns:
        pd.DataFrame: Die granulierteren Suchergebnisse.
    """
    df["Datum"] = granulationFunc(df["Datum"])  # Granulationsfunktion anwenden
    df = (
        df.groupby(["N-Gramm", "Datum"], as_index=False) # Gruppieren nach N-Gramm und Datum
        .agg({"Frequenz": "sum", "Frequenz (ppm)": "sum"}) # Aggregieren der Frequenzen
    )
    return df.sort_values(by=["Datum"]).reset_index(drop=True) # Sortieren nach Datum und Index zurücksetzen

def applyMovingAvarage(df: pd.DataFrame, avarageSize: int) -> pd.DataFrame:
    """
    Wendet einen gleitenden Durchschnitt auf die Daten an.
    Args:
        data (pd.DataFrame): Die Suchergebnisse.
        avarageSize (int): Die Größe des gleitenden Durchschnittsfensters.
    Returns:
        pd.DataFrame: Die geglätteten Suchergebnisse.
    """
    if avarageSize < 2: # Kein gleitender Durchschnitt erforderlich
        return df

    df = df.sort_values(by=["Datum"]).reset_index(drop=True) # Sicherstellen, dass die Daten nach Datum sortiert sind
    df["Frequenz"] = (
        df.groupby("N-Gramm")["Frequenz"] # Gruppieren nach N-Gramm
        .transform(lambda x: x.rolling(window=avarageSize, min_periods=1).mean()) # Gleitenden Durchschnitt berechnen
    )
    df["Frequenz (ppm)"] = (
        df.groupby("N-Gramm")["Frequenz (ppm)"] # Gruppieren nach N-Gramm
        .transform(lambda x: x.rolling(window=avarageSize, min_periods=1).mean()) # Gleitenden Durchschnitt berechnen
    )
    return df

def mergeAllResuls(n: int, df: pd.DataFrame, newLabel="All") -> pd.DataFrame:
    """
    Führt die Suchergebnisse aller N-Gramme zusammen.
    Wichtig, führen Sie diese Funktion immer vor der Granulation oder dem gleitenden Durchschnitt aus.
    
    Args:
        n (int): Die Anzahl der Tokens (N-Gramm).
        df (pd.DataFrame): Die Suchergebnisse.
        newLabel (str): Das Label für die zusammengeführten Ergebnisse.
    Returns:
        pd.DataFrame: Die zusammengeführten Suchergebnisse.
    """
    df = (
        df.groupby("Datum", as_index=False)["Frequenz"] # Gruppieren nach Datum
        .sum() # Frequenzen summieren
        .assign(**{"N-Gramm": newLabel}) # Neues Label zuweisen
    )    
    return __normalizeData(1, df)

def createSankeyData(n: int, df: pd.DataFrame) -> go.Sankey:
    """
    Erstellt die Datenstruktur für einen Sankey-Plot aus den Suchergebnissen.
    Args:
        n (int): Die Anzahl der Tokens (N-Gramm), z. B. 2 oder 3.
        data (pd.DataFrame): Die Suchergebnisse.
    Returns:
        go.Sankey: Die Datenstruktur für den Sankey-Plot.
    """
    if n < 2 or n > 3: # Nur N=2 oder N=3 sind erlaubt
        raise ValueError("n must be 2 or 3 for Sankey diagram.")
    
    label_map = {}
    link_map = {}

    for _, row in df.iterrows(): # Durchlaufe alle Zeilen im DataFrame
        parts = row["N-Gramm"].split(" ") # Teile das N-Gramm in seine Bestandteile auf
        if len(parts) != n: # Überprüfe, ob die Anzahl der Teile mit n übereinstimmt
            continue

        for part in parts: # Erstelle eine Zuordnung der Labels zu Indizes
            if part not in label_map: # Neues Label hinzufügen
                label_map[part] = len(label_map) # Index zuweisen

        for i in range(len(parts) - 1): # Erstelle die Links zwischen den Teilen
            source = label_map[parts[i]] # Quell-Index
            target = label_map[parts[i + 1]] # Ziel-Index
            link_key = (source, target) # Schlüssel für das Link-Map
            link_map[link_key] = link_map.get(link_key, 0) + row["Frequenz (ppm)"] # Frequenz zum Link hinzufügen

    sources, targets, values = zip(*[(src, tgt, val) for (src, tgt), val in link_map.items()]) # Extrahiere Quellen, Ziele und Werte aus dem Link-Map

    return go.Sankey( # Erstelle die Sankey-Datenstruktur
        node=dict(label=list(label_map.keys())), # Labels der Knoten
        link=dict(source=sources, target=targets, value=values) # Links zwischen den Knoten
    )

def lookupSingle(year: int, layer: LayerName, ngram: str) -> dict:
    """
    Führt eine Lookup-Abfrage für ein einzelnes N-Gramm im angegebenen Layer durch.

    Args:
        year (int): Das Fokusjahr.
        layer (LayerName): Der Layer (Lemma oder POS).
        ngram (str): Das aufzulösende N-Gramm.

    Returns:
        dict: Die Lookup-Ergebnisse.
    """
    return __lookup(year, layer, {ngram}) # Lookup durchreichen

def lookupDataFrame(year: int, layer: LayerName, data: pd.DataFrame) -> pd.DataFrame:
    """
    Ergänzt den pd.DataFrame um die aufgelösten Werte des Layers.

    Args:
        year (int): Das Fokusjahr.
        layer (LayerName): Der Layer (Lemma oder POS).
        data (pd.DataFrame): Der DataFrame mit den N-Grammen.

    Returns:
        pd.DataFrame: Die Lookup-Ergebnisse als DataFrame.
    """
    wordformSet = set() # Einzigartige Wortformen sammeln
    for ngram in data["N-Gramm"]: # Durchlaufe alle N-Gramme
        parts = ngram.split(" ") # Teile das N-Gramm in seine Bestandteile auf
        for part in parts: # Füge jedes Teil zur Menge hinzu
            wordformSet.add(part) # Einzigartige Wortformen sammeln
    lookupRes = __lookup(year, layer, wordformSet) # Lookup durchführen
    
    data[f"{layer.name}"] = data["N-Gramm"].apply( # Ergänze den DataFrame um die aufgelösten Werte
        lambda ngram: " ".join([lookupRes.get(part, part) for part in ngram.split(" ")]) # Aufgelöste Werte zusammenfügen
    )
    return data
# <<<<<<< Ende Öffentliche API-Funktionen <<<<<<<