import os
import subprocess
import shutil
import datetime
import uuid
from .exiftool_manager import ExifToolManager

class WriteXMPMetadataLossless:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_image_path": ("STRING", {"default": ""}),
                "metadata": ("STRING", {"multiline": True, "default": "1girl, black hair"}),
                "metadata_type": (["Subject", "Description", "Custom XMP"],{"default": "Subject"}),
                "write_mode": (["Add to existing", "Replace all", "Delete specified"],{"default": "Add to existing"}),
            },
            "optional": {
                "custom_field": ("STRING", {"default": "", "multiline": False}),
                "output_directory": ("STRING", {"default": "./tagged"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_path",)
    FUNCTION = "write_xmp"
    CATEGORY = "too/xmp-metadata"
    OUTPUT_NODE = True

    def get_output_path(self, input_image_path, output_directory=""):
        """
        Génère un chemin de sortie pour l'image traitée, en préservant le nom du fichier original
        """
        # Obtenir le nom et l'extension du fichier original
        original_name = os.path.basename(input_image_path)
        filename_base, file_extension = os.path.splitext(original_name)
        
        # Déterminer le répertoire de sortie
        if output_directory and output_directory != "./tagged":
            # Si un répertoire de sortie est spécifié et différent du défaut, l'utiliser
            base_dir = output_directory.rstrip("\\/")
        else:
            # Sinon, utiliser le même répertoire que l'image d'origine
            # et créer un sous-répertoire 'tagged'
            original_dir = os.path.dirname(os.path.abspath(input_image_path))
            base_dir = os.path.join(original_dir, "tagged")
        
        os.makedirs(base_dir, exist_ok=True)
        
        # Créer un nom de fichier avec le même nom de base mais dans le répertoire de sortie
        return os.path.join(base_dir, f"{filename_base}{file_extension}")

    def parse_tags(self, metadata):
        """Parse les tags depuis différents formats (JSON, CSV, etc.)"""
        try:
            # Essayer de parser comme JSON
            import json
            try:
                metadata_dict = json.loads(metadata)
                if isinstance(metadata_dict, dict) and "tags" in metadata_dict:
                    if isinstance(metadata_dict["tags"], list):
                        return metadata_dict["tags"]
                    else:
                        return [t.strip() for t in str(metadata_dict["tags"]).split(",")]
                else:
                    return [t.strip() for t in metadata.split(",")]
            except json.JSONDecodeError:
                # Si ce n'est pas du JSON, traiter comme une liste séparée par des virgules
                return [t.strip() for t in metadata.split(",")]
        except:
            # En cas d'erreur, utiliser le texte brut
            return [t.strip() for t in metadata.split(",")]

    def write_xmp(self, input_image_path, metadata, metadata_type="Subject", write_mode="Add to existing", custom_field="", output_directory=""):
        """
        Ajoute des métadonnées XMP à une image existante, en préservant toutes les métadonnées d'origine
        """
        # Initialiser ExifToolManager et vérifier si ExifTool est disponible
        exiftool_manager = ExifToolManager()
        exiftool_path = exiftool_manager.exiftool_path
        
        if not exiftool_path:
            print("/!\\ ExifTool non trouvé. Installez-le pour utiliser les fonctionnalités XMP.")
            return ("Erreur: ExifTool non trouvé",)
            
        # Supprimer les guillemets autour du chemin s'ils sont présents
        if input_image_path.startswith('"') and input_image_path.endswith('"'):
            input_image_path = input_image_path[1:-1]
            
        # Vérifier si le fichier d'entrée existe
        if not input_image_path or not os.path.exists(input_image_path):
            print(f"/!\\ Fichier d'entrée non trouvé: {input_image_path}")
            return (f"Erreur: Fichier non trouvé - {input_image_path}",)
            
        # Vérifier si le fichier d'entrée est dans un dossier "tagged" pour éviter les boucles
        input_dir = os.path.dirname(os.path.abspath(input_image_path)).lower()
        if "tagged" in input_dir.split(os.path.sep):
            print(f"/!\\ Attention: Le fichier d'entrée est déjà dans un dossier 'tagged': {input_image_path}")
            if not output_directory or output_directory == "./tagged":  # Si aucun répertoire de sortie n'est spécifié, c'est risqué
                print("/!\\ Traitement annulé pour éviter une boucle de traitement.")
                return (f"Erreur: Fichier déjà dans un dossier 'tagged' - {input_image_path}",)
            
        # Obtenir le chemin de sortie
        output_path = self.get_output_path(input_image_path, output_directory)
        
        # Créer une copie du fichier original avec toutes ses propriétés
        shutil.copy2(input_image_path, output_path)
            
        # Construire la commande ExifTool basée sur le type de métadonnées
        cmd = [exiftool_path]
        
        if metadata_type == "Subject":
            # Gérer les tags Subject avec les différents modes
            new_tags = self.parse_tags(metadata)
            
            if write_mode == "Add to existing":
                # Simple : ajouter les nouveaux tags sans effacer
                for tag in new_tags:
                    if tag:
                        cmd.append(f"-XMP-dc:Subject+={tag}")
                        
            elif write_mode == "Replace all":
                # D'abord supprimer tous les Subject
                clear_cmd = [exiftool_path, "-XMP-dc:Subject=", output_path, "-overwrite_original"]
                result_clear = subprocess.run(clear_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                
                # Puis ajouter les nouveaux tags
                if new_tags:
                    for tag in new_tags:
                        if tag:
                            cmd.append(f"-XMP-dc:Subject+={tag}")
                # Si pas de nouveaux tags, on s'arrête là (Subject déjà effacé)
                        
            elif write_mode == "Delete specified":
                # Supprimer les tags spécifiés  
                for tag in new_tags:
                    if tag:
                        cmd.append(f"-XMP-dc:Subject-={tag}")
                    
        elif metadata_type == "Description":
            # Pour Description, utiliser le texte entier
            if write_mode == "Replace all" or write_mode == "Add to existing":
                cmd.append(f"-XMP-dc:Description={metadata}")
            elif write_mode == "Delete specified":
                cmd.append("-XMP-dc:Description=")
                
        elif metadata_type == "Custom XMP":
            # Pour Custom XMP, utiliser le champ personnalisé
            if custom_field:
                field_name = custom_field if ":" in custom_field else f"XMP-dc:{custom_field}"
                if write_mode == "Replace all" or write_mode == "Add to existing":
                    cmd.append(f"-{field_name}={metadata}")
                elif write_mode == "Delete specified":
                    cmd.append(f"-{field_name}=")
            else:
                print("/!\\ Aucun champ personnalisé spécifié pour le type Custom XMP")
                return ("Erreur: Champ personnalisé requis pour le type Custom XMP",)
                
        # Ajouter les paramètres communs
        cmd.append(output_path)
        cmd.append("-overwrite_original")
            
        # Exécuter la commande pour ajouter les métadonnées
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            print(f"/!\\ Erreur lors de l'application des métadonnées: {result.stderr}")
            return (f"Erreur: {result.stderr}",)
            
        # Préserver les dates après l'application des métadonnées
        try:
            # Obtenir les timestamps du fichier original
            original_stat = os.stat(input_image_path)
            
            # Appliquer les timestamps au fichier de sortie
            os.utime(output_path, (original_stat.st_atime, original_stat.st_mtime))
        except Exception as e:
            print(f"/!\\ Erreur lors de l'application des timestamps: {e}")
        
        print(f"[OK] Image avec métadonnées XMP écrite: {output_path}")
        
        return (output_path,)