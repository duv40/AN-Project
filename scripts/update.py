import subprocess
import sys

def run_script(script_name):
    print(f"\nLancement de {script_name}...")
    try:
        subprocess.run([sys.executable, script_name], check=True)
        print(f"-->{script_name} exécuté avec succès.")
    except subprocess.CalledProcessError as e:
        print(f"-->Erreur lors de l'exécution de {script_name}. Code de sortie : {e.returncode}")
        sys.exit(e.returncode)

if __name__ == "__main__":
    run_script("collecte_youtube.py")
    run_script("prediction_nlp.py")
