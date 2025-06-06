import os
import subprocess

class ExifToolManager:
    def __init__(self, console_debug=False):
        self.exiftool_path = self.get_exiftool_path()
        self.console_debug = console_debug
        if not self.exiftool_path and console_debug:
            print("/!\\ ExifTool non trouvé. Installez-le pour utiliser les fonctionnalités XMP.")
    
    @staticmethod
    def get_exiftool_path():
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
        """Extrait les métadonnées XMP spécifiques d'une image"""
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

    def extract_all_xmp_metadata(self, image_path):
        """Extrait toutes les métadonnées XMP d'une image"""
        if not self.exiftool_path:
            return {"error": "ExifTool non trouvé"}

        try:
            # Essayer plusieurs variantes de commandes pour récupérer les métadonnées XMP
            commands = [
                f'"{self.exiftool_path}" -XMP-all "{image_path}"',
                f'"{self.exiftool_path}" -XMP:all "{image_path}"', 
                f'"{self.exiftool_path}" -g1 -XMP "{image_path}"',
                f'"{self.exiftool_path}" -XMP-dc:all -XMP-xmp:all -XMP-photoshop:all -XMP-lr:all -XMP-crs:all "{image_path}"'
            ]
            
            best_result = {}
            best_stdout = ""
            
            for cmd in commands:
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
                    if result.returncode == 0 and result.stdout.strip():
                        metadata = {}
                        for line in result.stdout.split("\n"):
                            line = line.strip()
                            if ":" in line and line:
                                # Exclure les lignes d'erreur ou d'information système
                                if not any(line.startswith(x) for x in ["Warning", "Error", "File not found", "========"]):
                                    try:
                                        key, value = line.split(":", 1)
                                        key = key.strip()
                                        value = value.strip()
                                        if key and value and not key.startswith("-"):
                                            metadata[key] = value
                                    except ValueError:
                                        continue
                        
                        # Garder le résultat avec le plus de métadonnées
                        if len(metadata) > len(best_result):
                            best_result = metadata
                            best_stdout = result.stdout
                            
                except Exception:
                    continue
            
            if self.console_debug:
                print("--- Sortie d'ExifTool (ALL XMP) ---")
                print(f"Found {len(best_result)} metadata entries:")
                for key, value in best_result.items():
                    print(f"  {key}: {value}")
                print("----------------------------------")

            return best_result if best_result else {"info": "Aucune métadonnée XMP trouvée"}
            
        except Exception as e:
            return {"error": str(e)}