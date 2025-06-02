import os
import subprocess
import shutil
import datetime
import uuid

class WriteXMPMetadataLossless:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_image_path": ("STRING", {"default": ""}),
                "metadata": ("STRING", {"multiline": True, "default": "1girl, black hair"}),
            },
            "optional": {
                "output_dir": ("STRING", {"default": ""}),
                "console_debug": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_path",)
    FUNCTION = "write_xmp"
    CATEGORY = "too/xmp-metadata"
    OUTPUT_NODE = True

    def get_exiftool_path(self):
        """Trouve le chemin d'ExifTool, en cherchant d'abord dans le PATH, puis localement"""
        try:
            result = subprocess.run(['exiftool', '-ver'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            if result.returncode == 0:
                return "exiftool"
        except Exception:
            pass

        module_path = os.path.dirname(os.path.abspath(__file__))
        exiftool_local = os.path.join(module_path, "../exiftool/exiftool.exe")
        if os.path.exists(exiftool_local):
            return os.path.abspath(exiftool_local)  # Utiliser le chemin absolu
        return None

    def get_output_path(self, input_image_path, output_dir=""):
        """
        Génère un chemin de sortie pour l'image traitée, en préservant le nom du fichier original
        """
        # Obtenir le nom et l'extension du fichier original
        original_name = os.path.basename(input_image_path)
        filename_base, file_extension = os.path.splitext(original_name)
        
        # Déterminer le répertoire de sortie
        if output_dir:
            # Si un répertoire de sortie est spécifié, l'utiliser
            base_dir = output_dir.rstrip("\\/")
        else:
            # Sinon, utiliser le même répertoire que l'image d'origine
            # et créer un sous-répertoire 'tagged'
            original_dir = os.path.dirname(os.path.abspath(input_image_path))
            base_dir = os.path.join(original_dir, "tagged")
        
        os.makedirs(base_dir, exist_ok=True)
        
        # Créer un nom de fichier avec le même nom de base mais dans le répertoire de sortie
        return os.path.join(base_dir, f"{filename_base}{file_extension}")

    def write_xmp(self, input_image_path, metadata, output_dir="", console_debug=False):
        """
        Ajoute des métadonnées XMP à une image existante, en préservant toutes les métadonnées d'origine
        """
        # Vérifier si ExifTool est disponible
        exiftool_path = self.get_exiftool_path()
        if not exiftool_path:
            print("/!\\ ExifTool non trouvé. Installez-le pour utiliser les fonctionnalités XMP.")
            return ("Erreur: ExifTool non trouvé",)
            
        # Vérifier si le fichier d'entrée existe
        # Supprimer les guillemets autour du chemin s'ils sont présents
        if input_image_path.startswith('"') and input_image_path.endswith('"'):
            input_image_path = input_image_path[1:-1]
                
        if not input_image_path or not os.path.exists(input_image_path):
            print(f"/!\\ Fichier d'entrée non trouvé: {input_image_path}")
            return (f"Erreur: Fichier non trouvé - {input_image_path}",)
            
        # Vérifier si le fichier d'entrée est dans un dossier "tagged" pour éviter les boucles
        input_dir = os.path.dirname(os.path.abspath(input_image_path)).lower()
        if "tagged" in input_dir.split(os.path.sep):
            print(f"/!\\ Attention: Le fichier d'entrée est déjà dans un dossier 'tagged': {input_image_path}")
            if not output_dir:  # Si aucun répertoire de sortie n'est spécifié, c'est risqué
                print("/!\\ Traitement annulé pour éviter une boucle de traitement.")
                return (f"Erreur: Fichier déjà dans un dossier 'tagged' - {input_image_path}",)
            elif console_debug:
                print("-> Traitement autorisé car un répertoire de sortie spécifique est défini.")
            
        # Obtenir le chemin de sortie
        output_path = self.get_output_path(input_image_path, output_dir)
        
        # Créer une copie du fichier original
        if console_debug:
            print(f"-> Fichier d'entrée: {input_image_path}")
            print(f"-> Fichier de sortie: {output_path}")
            
        # Créer une copie du fichier original avec toutes ses propriétés
        shutil.copy2(input_image_path, output_path)
        
        if console_debug:
            print("-> Fichier copié avec succès")
            
        # Préparer les métadonnées
        try:
            import json
            metadata_dict = json.loads(metadata)
        except json.JSONDecodeError:
            metadata_dict = metadata
            
        # Créer une liste de tags à partir des métadonnées
        tags = []
        if isinstance(metadata_dict, dict):
            if "tags" in metadata_dict:
                if isinstance(metadata_dict["tags"], list):
                    tags = metadata_dict["tags"]
                elif isinstance(metadata_dict["tags"], str):
                    tags = [t.strip() for t in metadata_dict["tags"].split(",")]
        elif isinstance(metadata_dict, str):
            tags = [t.strip() for t in metadata_dict.split(",")]
            
        # Construire la commande ExifTool pour ajouter les métadonnées XMP
        cmd = [exiftool_path]
        for tag in tags:
            cmd.append(f"-XMP-dc:Subject+={tag}")
            
        if isinstance(metadata_dict, dict):
            for k, v in metadata_dict.items():
                if k != "tags" and not isinstance(v, (dict, list)):
                    cmd.append(f"-XMP-comfyui:{k}={v}")
                    
        cmd.append(output_path)
        cmd.append("-overwrite_original")
        
        if console_debug:
            print(f"-> Commande ExifTool: {' '.join(cmd)}")
            
        # Exécuter la commande pour ajouter les métadonnées
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            print(f"/!\\ Erreur lors de l'application des métadonnées: {result.stderr}")
            # On ne supprime pas le fichier de sortie, il peut toujours être utilisable
            return (f"Erreur: {result.stderr}",)
            
        # Préserver les dates après l'application des métadonnées
        # car exiftool peut modifier les dates lors de l'écriture des métadonnées
        try:
            # Obtenir les timestamps du fichier original
            original_stat = os.stat(input_image_path)
            
            # Appliquer les timestamps au fichier de sortie
            os.utime(output_path, (original_stat.st_atime, original_stat.st_mtime))
            
            if console_debug:
                print(f"-> Timestamps appliqués depuis le fichier original")
        except Exception as e:
            print(f"/!\\ Erreur lors de l'application des timestamps: {e}")
            
        if console_debug:
            # Vérifier que les dates ont bien été préservées
            try:
                orig_stat = os.stat(input_image_path)
                out_stat = os.stat(output_path)
                orig_time = datetime.datetime.fromtimestamp(orig_stat.st_mtime)
                out_time = datetime.datetime.fromtimestamp(out_stat.st_mtime)
                print(f"-> Date d'origine: {orig_time}")
                print(f"-> Date de sortie: {out_time}")
                print(f"-> Dates identiques: {abs(orig_stat.st_mtime - out_stat.st_mtime) < 1}")
            except Exception as e:
                print(f"/!\\ Erreur lors de la vérification des dates: {e}")
        
        print(f"[OK] Image avec métadonnées XMP écrite: {output_path}")
        
        return (output_path,)
