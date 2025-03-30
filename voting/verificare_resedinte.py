import pickle
import os
import pandas as pd

# Maparea corectă a județelor cu reședințele lor
resedinte_complete = {
    'AB': 'MUNICIPIUL ALBA IULIA',
    'AG': 'MUNICIPIUL PITEȘTI',
    'AR': 'MUNICIPIUL ARAD',
    'B': 'MUNICIPIUL BUCUREȘTI',
    'BC': 'MUNICIPIUL BACĂU',
    'BH': 'MUNICIPIUL ORADEA',
    'BN': 'MUNICIPIUL BISTRIȚA',
    'BR': 'MUNICIPIUL BRĂILA',
    'BT': 'MUNICIPIUL BOTOȘANI',
    'BV': 'MUNICIPIUL BRAȘOV',
    'BZ': 'MUNICIPIUL BUZĂU',
    'CJ': 'MUNICIPIUL CLUJ-NAPOCA',
    'CL': 'MUNICIPIUL CĂLĂRAȘI',
    'CS': 'MUNICIPIUL REȘIȚA',
    'CT': 'MUNICIPIUL CONSTANȚA',
    'CV': 'MUNICIPIUL SFÂNTU GHEORGHE',
    'DB': 'MUNICIPIUL TÂRGOVIȘTE',
    'DJ': 'MUNICIPIUL CRAIOVA',
    'GJ': 'MUNICIPIUL TÂRGU JIU',
    'GL': 'MUNICIPIUL GALAȚI',
    'GR': 'MUNICIPIUL GIURGIU',
    'HD': 'MUNICIPIUL DEVA',
    'HR': 'MUNICIPIUL MIERCUREA-CIUC',
    'IF': 'ORAȘUL BUFTEA',  # Pentru Ilfov este oraș, nu municipiu
    'IL': 'MUNICIPIUL SLOBOZIA',
    'IS': 'MUNICIPIUL IAȘI',
    'MH': 'MUNICIPIUL DROBETA-TURNU SEVERIN',
    'MM': 'MUNICIPIUL BAIA MARE',
    'MS': 'MUNICIPIUL TÂRGU MUREȘ',
    'NT': 'MUNICIPIUL PIATRA-NEAMȚ',
    'OT': 'MUNICIPIUL SLATINA',
    'PH': 'MUNICIPIUL PLOIEȘTI',
    'SB': 'MUNICIPIUL SIBIU',
    'SJ': 'MUNICIPIUL ZALĂU',
    'SM': 'MUNICIPIUL SATU MARE',
    'SV': 'MUNICIPIUL SUCEAVA',
    'TL': 'MUNICIPIUL TULCEA',
    'TM': 'MUNICIPIUL TIMIȘOARA',
    'TR': 'MUNICIPIUL ALEXANDRIA',
    'VL': 'MUNICIPIUL RÂMNICU VÂLCEA',
    'VN': 'MUNICIPIUL FOCȘANI',
    'VS': 'MUNICIPIUL VASLUI'
}

# Calea către directorul cu fișierele
dir_path = 'C:/Users/brj/Desktop/voting/vote/ai_models/judet_uat_data'
pkl_file = os.path.join(dir_path, 'resedinte_judete.pkl')
csv_file = os.path.join(dir_path, 'resedinte_judete.csv')

# Verifică dacă există fișierul PKL și încarcă-l
resedinte_existente = {}
if os.path.exists(pkl_file):
    try:
        with open(pkl_file, 'rb') as f:
            resedinte_existente = pickle.load(f)
        print(f"Fișierul PKL existent conține {len(resedinte_existente)} reședințe de județ.")
    except Exception as e:
        print(f"Eroare la încărcarea fișierului PKL: {e}")
else:
    print("Fișierul PKL nu există, se va crea unul nou.")

# Verifică și fișierul CSV (în caz că PKL e corupt sau nu conține toate datele)
if os.path.exists(csv_file):
    try:
        df = pd.read_csv(csv_file)
        print(f"Fișierul CSV existent conține {len(df)} reședințe de județ.")

        # Dacă PKL-ul nu a putut fi încărcat sau e gol, folosim datele din CSV
        if not resedinte_existente:
            for _, row in df.iterrows():
                if 'JUDET' in df.columns and 'RESEDINTA' in df.columns:
                    resedinte_existente[row['JUDET']] = row['RESEDINTA']
    except Exception as e:
        print(f"Eroare la încărcarea fișierului CSV: {e}")
else:
    print("Fișierul CSV nu există, se va crea unul nou.")

# Verificăm ce reședințe lipsesc sau sunt diferite
judete_lipsa = []
judete_diferite = []

for judet, resedinta in resedinte_complete.items():
    if judet not in resedinte_existente:
        judete_lipsa.append(judet)
    elif resedinte_existente[judet] != resedinta:
        judete_diferite.append((judet, resedinte_existente[judet], resedinta))

print(f"\nS-au găsit {len(judete_lipsa)} județe lipsă și {len(judete_diferite)} reședințe diferite.")

if judete_lipsa:
    print("Județe lipsă:", judete_lipsa)

if judete_diferite:
    print("\nResedințe diferite (se va înlocui prima valoare cu a doua):")
    for judet, resedinta_veche, resedinta_noua in judete_diferite:
        print(f"{judet}: '{resedinta_veche}' -> '{resedinta_noua}'")

# Întreabă utilizatorul dacă vrea să actualizeze fișierele
raspuns = input("\nVrei să actualizezi fișierele cu reședința corectă pentru județele lipsă/diferite? (Da/Nu): ")

# Actualizăm dicționarul dacă utilizatorul dorește
resedinte_actualizate = resedinte_existente.copy()

if raspuns.lower() in ['da', 'd', 'yes', 'y']:
    # Adăugăm județele lipsă
    for judet in judete_lipsa:
        resedinte_actualizate[judet] = resedinte_complete[judet]

    # Actualizăm reședințele diferite
    for judet, _, resedinta_noua in judete_diferite:
        resedinte_actualizate[judet] = resedinta_noua

    # Salvăm înapoi în fișierele PKL și CSV
    with open(pkl_file, 'wb') as f:
        pickle.dump(resedinte_actualizate, f)

    # Pentru CSV
    df_new = pd.DataFrame([(judet, uat) for judet, uat in resedinte_actualizate.items()],
                          columns=['JUDET', 'RESEDINTA'])
    df_new.to_csv(csv_file, index=False)

    print(f"\nFișierele au fost actualizate. Acum avem {len(resedinte_actualizate)} județe cu reședințe.")
else:
    print("Fișierele nu au fost modificate.")

# Afișează un raport final
print("\nRaport final:")
print(f"Total județe în lista completă: {len(resedinte_complete)}")
print(f"Total județe în fișierele după procesare: {len(resedinte_actualizate)}")
print(f"Județe lipsă: {len(judete_lipsa)}")
print(f"Reședințe diferite: {len(judete_diferite)}")

# Afișează toate județele și reședințele pentru verificare
print("\n=== LISTĂ COMPLETĂ JUDEȚE ȘI REȘEDINȚE ===")
print("-" * 50)
print("| JUDEȚ | REȘEDINȚĂ")
print("-" * 50)

# Sortăm județele alfabetic pentru o afișare mai clară
for judet in sorted(resedinte_actualizate.keys()):
    resedinta = resedinte_actualizate[judet]
    print(f"| {judet}    | {resedinta}")

print("-" * 50)
print("\nVerifică lista de mai sus pentru a te asigura că toate reședințele sunt corecte.")

# Verifică dacă există fișierul judet_uat_list.pkl necesar pentru populate_candidates
uat_list_file = os.path.join(dir_path, 'judet_uat_list.pkl')
if os.path.exists(uat_list_file):
    try:
        with open(uat_list_file, 'rb') as f:
            judet_uat_list = pickle.load(f)
        print(f"\nFișierul judet_uat_list.pkl există și conține {len(judet_uat_list)} asocieri județ-UAT.")
    except Exception as e:
        print(f"\nEroare la încărcarea fișierului judet_uat_list.pkl: {e}")
else:
    print(
        "\nATENȚIE: Fișierul judet_uat_list.pkl nu există în director! Acest fișier este necesar pentru comanda de populare a candidaților.")