import os
import subprocess

class ExifToolManager:
    def __init__(self, console_debug=False):
        self.exiftool_path = self.get_exiftool_path()
        self.console_debug = console_debug
        if not self.exiftool_path and console_debug:
            print("/!\\ ExifTool non trouvé. Installez-le pour utiliser les fonctionnalités XMP.")
    
    def get_exiftool_path(self):
        """Trouve le chemin d'ExifTool, en cherchant d'abord dans le PATH, puis localement"""
        try:
            result = subprocess.run(['exiftool', '-ver'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            if result.returncode == 0:
                return "exiftool"
        except Exception:
            pass

        if os.name == 'nt':
            module_path = os.path.dirname(os.path.abspath(__file__))
            exiftool_local = os.path.join(module_path, "../exiftool/exiftool.exe")
            if os.path.exists(exiftool_local):
                return exiftool_local
        return None

    def extract_metadata(self, image_path):
        """Extrait les métadonnées XMP d'une image"""
        if not self.exiftool_path:
            return {"error": "ExifTool non trouvé"}

        try:
            result = subprocess.run(
                f'"{self.exiftool_path}" -XMP-dc:Subject -XMP-dc:Description -XMP-xmp:CreateDate -XMP-xmp:ModifyDate "{image_path}"',
                capture_output=True,
                text=True,
                shell=True
            )

            if self.console_debug:
                print("--- Sortie d'ExifTool ---")
                for line in result.stdout.split("\n"):
                    if line.strip():  # Affiche uniquement les lignes non vides
                        # Nettoyage des espaces excessifs pour l'affichage
                        parts = line.split(":", 1)
                        if len(parts) == 2:
                            key = parts[0].strip()
                            value = parts[1].strip()
                            print(f"{key}: {value}")
                        else:
                            print(line)
                if result.stderr.strip():
                    print("--- Erreurs d'ExifTool ---")
                    print(result.stderr)
                print("------------------------")

            metadata = {}
            for line in result.stdout.split("\n"):
                line = line.strip()
                if ":" in line:
                    key, value = line.split(":", 1)
                    metadata[key.strip()] = value.strip()

            return metadata
        except Exception as e:
            return {"error": str(e)}
