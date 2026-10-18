import os
import urllib.request
import zipfile

URLS = [
    "https://www.dgterritorio.gov.pt/sites/default/files/ficheiros-cartografia/Cont_AAD_CAOP2021.zip",
    "https://www.dgterritorio.gov.pt/sites/default/files/ficheiros-cartografia/ArqMadeira_AAd_CAOP2021.zip",
    "https://www.dgterritorio.gov.pt/sites/default/files/ficheiros-cartografia/ArqAcores_GCentral_AAd_CAOP2021.zip",
    "https://www.dgterritorio.gov.pt/sites/default/files/ficheiros-cartografia/ArqAcores_GOriental_AAd_CAOP2021.zip",
    "https://www.dgterritorio.gov.pt/sites/default/files/ficheiros-cartografia/ArqAcores_GOcidental_AAd_CAOP2021.zip"
]

BASE_DIR = os.path.join(os.path.dirname(__file__), 'data', 'CAOP_2021')
os.makedirs(BASE_DIR, exist_ok=True)

for url in URLS:
    filename = url.split('/')[-1]
    zip_path = os.path.join(BASE_DIR, filename)
    
    if not os.path.exists(zip_path):
        print(f"Downloading {filename}...")
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response, open(zip_path, 'wb') as out_file:
                out_file.write(response.read())
        except Exception as e:
            print(f"Error downloading {filename}: {e}")
            continue

    extract_folder = os.path.join(BASE_DIR, filename.replace('.zip', ''))
    if not os.path.exists(extract_folder):
        print(f"Extracting {filename}...")
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(BASE_DIR)
        except Exception as e:
            print(f"Error extracting {filename}: {e}")

print("All CAOP downloads and extractions complete.")
