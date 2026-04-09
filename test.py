import pandas as pd

def choisir_feuille(sheet_url):
    # Transformer le lien en version exploitable
    base_url = sheet_url.split("/edit")[0]

    # Lire les infos du fichier (liste des feuilles)
    xls = pd.ExcelFile(base_url.replace("/d/", "/d/") + "/export?format=xlsx")

    sheets = xls.sheet_names

    # Afficher les feuilles
    print("\n📄 Liste des feuilles disponibles :")
    for i, name in enumerate(sheets):
        print(f"{i + 1}. {name}")

    # Choix utilisateur
    choix = int(input("\n👉 Choisis le numéro de la feuille : ")) - 1
    selected_sheet = sheets[choix]

    print(f"\n✅ Feuille sélectionnée : {selected_sheet}")

    # Lire la feuille choisie
    df = pd.read_excel(base_url + f"/export?format=xlsx&sheet={selected_sheet}")

    return df


# 🔗 Exemple
if __name__ == "__main__":
    url = input("🔗 Donne le lien du Google Sheet : ")
    df = choisir_feuille(url)

    print("\n📊 Aperçu :")
    print(df.head())