import pandas as pd
import io
import requests

def list_sheets(sheet_url: str) -> tuple[io.BytesIO, list]:
    """
    Retourne le fichier en mémoire et la liste des feuilles
    """
    base_url = sheet_url.split("/edit")[0].split("/pub")[0]
    export_url = base_url + "/export?format=xlsx"

    # Télécharger une seule fois
    response = requests.get(export_url, timeout=500)
    response.raise_for_status()
    fichier = io.BytesIO(response.content)

    # Lire les noms des feuilles
    xls = pd.ExcelFile(fichier)
    sheets = xls.sheet_names

    return fichier, sheets


def choisir_feuille(fichier: io.BytesIO, sheet_name: str) -> pd.DataFrame:
    """
    Lire une feuille spécifique depuis le fichier déjà téléchargé
    """
    fichier.seek(0)  # remise à zéro pour relire le fichier
    df = pd.read_excel(fichier, sheet_name=sheet_name)
    return df