import os
import subprocess
import shutil
import datetime
import numpy as np
import torch
from PIL import Image
from .exiftool_manager import ExifToolManager

class WriteXMPMetadataTensor:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "metadata": ("STRING", {"multiline": True, "default": "1girl, black hair"}),
                "format_mode": (["Preserve format", "Smart format", "Force PNG", "Force JPG"],),
                "metadata_type": (["Subject", "Description", "Custom XMP"],{"default": "Subject"}),
                "write_mode": (["Add to existing", "Replace all", "Delete specified"],{"default": "Add to existing"}),
            },
            "optional": {
                "custom_metadata": ("STRING", {"default": "", "multiline": False}),
                "input_image_path": ("STRING", {"default": ""}),  # Pour préserver le nom si disponible
                "output_directory": ("STRING", {"default": "./tagged"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_path",)
    FUNCTION = "write_xmp"
    CATEGORY = "too/xmp-metadata"
    OUTPUT_NODE = True

    def get_output_path(self, output_directory="", output_format=".png", input_image_path=""):
        """
        Génère un chemin de sortie pour l'image traitée, en préservant le nom du fichier
        original si disponible
        """
        # Déterminer le nom du fichier
        if input_image_path:
            # Supprimer les guillemets autour du chemin s'ils sont présents
            if input_image_path.startswith('"') and input_image_path.endswith('"'):
                input_image_path = input_image_path[1:-1]
                
            # Préserver le nom du fichier original sans son extension
            original_name = os.path.basename(input_image_path)
            filename_no_ext, _ = os.path.splitext(original_name)
            filename = f"{filename_no_ext}{output_format}"
        else:
            # Sinon, générer un nom basé sur le timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tagged_image_{timestamp}{output_format}"
        
        # Déterminer le répertoire de sortie
        if output_directory and output_directory != "./tagged":
            # Si un répertoire de sortie est spécifié et différent du défaut, l'utiliser
            base_dir = output_directory.rstrip("\\/")
        elif input_image_path:
            # Si un chemin d'image est fourni, utiliser son répertoire
            original_dir = os.path.dirname(os.path.abspath(input_image_path))
            base_dir = os.path.join(original_dir, "tagged")
        else:
            # Sinon, utiliser le répertoire par défaut
            module_path = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(module_path)  # Remonter au répertoire parent
            base_dir = os.path.join(parent_dir, "tagged")
        
        os.makedirs(base_dir, exist_ok=True)
        return os.path.join(base_dir, filename)

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

    def write_xmp(self, image, metadata, format_mode="Preserve format", metadata_type="Subject", write_mode="Add to existing", custom_metadata="", input_image_path="", output_directory=""):
        """
        Écrit les métadonnées XMP sur une image, en choisissant le format selon le mode
        """
        # Initialiser ExifToolManager et vérifier si ExifTool est disponible
        exiftool_manager = ExifToolManager()
        exiftool_path = exiftool_manager.exiftool_path
        
        if not exiftool_path:
            print("/!\\ ExifTool non trouvé. Installez-le pour utiliser les fonctionnalités XMP.")
            return ("Erreur: ExifTool non trouvé",)

        # Convertir le tenseur en image PIL
        if len(image.shape) == 4:
            i = image[0].cpu().numpy()
        else:
            i = image.cpu().numpy()
        i = np.clip(i * 255.0, 0, 255).astype(np.uint8)
        img = Image.fromarray(i)
        
        # Déterminer le format de sortie selon le mode sélectionné
        if format_mode == "Force PNG":
            output_format = ".png"
        elif format_mode == "Force JPG":
            output_format = ".jpg"
        elif format_mode == "Preserve format" and input_image_path:
            # Supprimer les guillemets autour du chemin s'ils sont présents
            if input_image_path.startswith('"') and input_image_path.endswith('"'):
                input_image_path = input_image_path[1:-1]
                
            # Utiliser l'extension du fichier d'entrée si disponible
            output_format = os.path.splitext(input_image_path)[1].lower()
            # Vérifier que le format est supporté
            if output_format not in ['.jpg', '.jpeg', '.png', '.webp']:
                output_format = ".png"
        elif format_mode == "Smart format":
            # Détection intelligente du format optimal
            has_alpha = len(i.shape) > 2 and i.shape[2] == 4
            is_photo_like = self._is_photo_like(i)
            
            if has_alpha:
                output_format = ".png"  # Garder PNG pour les images avec canal alpha
            elif is_photo_like:
                output_format = ".jpg"  # Utiliser JPEG pour les photos
            else:
                output_format = ".png"  # PNG par défaut pour les illustrations
        else:
            # Par défaut ou si le chemin d'entrée n'est pas fourni
            output_format = ".png"
        
        # Obtenir le chemin de sortie
        output_path = self.get_output_path(output_directory, output_format, input_image_path)
        
        # IMPORTANT: Lire TOUTES les métadonnées AVANT de sauvegarder l'image
        # car une fois sauvegardée, TOUTES les métadonnées originales sont perdues
        existing_tags = []
        existing_metadata_to_preserve = {}
        
        if input_image_path and os.path.exists(input_image_path.strip('"')):
            clean_input_path = input_image_path.strip('"')
            all_existing_metadata = exiftool_manager.extract_metadata(clean_input_path)
            
            # Extraire les Subject pour la logique write_mode si on modifie Subject
            if metadata_type == "Subject" and write_mode in ["Add to existing", "Delete specified"] and "Subject" in all_existing_metadata:
                existing_subject = all_existing_metadata["Subject"]
                if ";" in existing_subject:
                    existing_tags = [t.strip() for t in existing_subject.split(";")]
                else:
                    existing_tags = [t.strip() for t in existing_subject.split(",")]
            
            # Préserver TOUTES les métadonnées pour les réécrire après (sauf celle qu'on modifie)
            for key, value in all_existing_metadata.items():
                existing_metadata_to_preserve[key] = value
        
        # Sauvegarder l'image dans le format approprié
        if output_format.lower() in ['.jpg', '.jpeg']:
            img.save(output_path, format="JPEG", quality=95)
        elif output_format.lower() == '.webp':
            img.save(output_path, format="WEBP", quality=95)
        else:
            img.save(output_path, format="PNG")
            
        # Construire la commande ExifTool basée sur le type de métadonnées
        cmd = [exiftool_path]
        
        if metadata_type == "Subject":
            # Gérer les tags Subject avec les différents modes
            new_tags = self.parse_tags(metadata)
            
            if write_mode == "Add to existing":
                # Combiner avec les tags existants lus AVANT la sauvegarde
                combined_tags = existing_tags.copy()
                for tag in new_tags:
                    if tag and tag not in combined_tags:
                        combined_tags.append(tag)
                
                # Ajouter tous les tags (existants + nouveaux)
                for tag in combined_tags:
                    if tag:
                        cmd.append(f"-XMP-dc:Subject+={tag}")
                        
            elif write_mode == "Replace all":
                # Remplacer par les nouveaux tags seulement
                if new_tags:
                    for tag in new_tags:
                        if tag:
                            cmd.append(f"-XMP-dc:Subject+={tag}")
                        
            elif write_mode == "Delete specified":
                # Supprimer les tags spécifiés des tags existants
                remaining_tags = [tag for tag in existing_tags if tag not in new_tags]
                
                # Ajouter seulement les tags restants
                for tag in remaining_tags:
                    if tag:
                        cmd.append(f"-XMP-dc:Subject+={tag}")
                    
        elif metadata_type == "Description":
            # Pour Description, appliquer write_mode
            existing_desc = existing_metadata_to_preserve.get("Description", "")
            
            if write_mode == "Add to existing":
                if existing_desc:
                    combined_desc = f"{existing_desc} {metadata}"
                    cmd.append(f"-XMP-dc:Description={combined_desc}")
                else:
                    cmd.append(f"-XMP-dc:Description={metadata}")
            elif write_mode == "Replace all":
                cmd.append(f"-XMP-dc:Description={metadata}")
            elif write_mode == "Delete specified":
                # Ne pas ajouter de commande Description = elle sera absente
                pass
                
        elif metadata_type == "Custom XMP":
            # Pour Custom XMP, appliquer write_mode
            if custom_metadata:
                field_name = custom_metadata if ":" in custom_metadata else f"XMP-dc:{custom_metadata}"
                existing_value = existing_metadata_to_preserve.get(custom_metadata, "")
                
                if write_mode == "Add to existing":
                    if existing_value:
                        combined_value = f"{existing_value} {metadata}"
                        cmd.append(f"-{field_name}={combined_value}")
                    else:
                        cmd.append(f"-{field_name}={metadata}")
                elif write_mode == "Replace all":
                    cmd.append(f"-{field_name}={metadata}")
                elif write_mode == "Delete specified":
                    # Ne pas ajouter de commande = ce champ sera absent
                    pass
            else:
                print("/!\\ Aucun champ personnalisé spécifié pour le type Custom XMP")
                return ("Erreur: Champ personnalisé requis pour le type Custom XMP",)
        
        # Réécrire toutes les autres métadonnées existantes qui ont été perdues lors de la sauvegarde PIL
        for key, value in existing_metadata_to_preserve.items():
            # Ne pas réécrire la métadonnée qu'on vient de modifier
            if key == "Subject" and metadata_type == "Subject":
                continue  # Subject géré par la logique write_mode ci-dessus
            elif key == "Description" and metadata_type == "Description":
                continue  # Description gérée par la logique write_mode ci-dessus
            elif metadata_type == "Custom XMP" and key == custom_metadata:
                continue  # Champ custom géré par la logique write_mode ci-dessus
            
            # Réécriture spéciale pour Subject (un tag par commande)
            if key == "Subject":
                if ";" in value:
                    subject_tags = [t.strip() for t in value.split(";")]
                else:
                    subject_tags = [t.strip() for t in value.split(",")]
                for tag in subject_tags:
                    if tag:
                        cmd.append(f"-XMP-dc:Subject+={tag}")
            # Réécrire les autres métadonnées normalement
            elif key in ["Description"]:
                cmd.append(f"-XMP-dc:{key}={value}")
            elif key in ["Create Date", "Modify Date"]:
                cmd.append(f"-XMP-xmp:{key.replace(' ', '')}={value}")
            else:
                # Pour les autres champs, essayer tel quel
                cmd.append(f"-{key}={value}")
            
        # Ajouter les paramètres communs
        cmd.append(output_path)
        cmd.append("-overwrite_original")
            
        # Exécuter la commande pour ajouter les métadonnées
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            print(f"/!\\ Erreur lors de l'application des métadonnées: {result.stderr}")
            return (f"Erreur: {result.stderr}",)
            
        print(f"[OK] Image avec métadonnées XMP écrite: {output_path}")
        
        return (output_path,)
        
    def _is_photo_like(self, img_array):
        """
        Détecte si une image ressemble plus à une photo qu'à une illustration
        en analysant sa distribution de couleurs et sa complexité.
        """
        try:
            # Réduire la taille pour l'analyse
            from PIL import Image
            img = Image.fromarray(img_array)
            img_small = img.resize((100, 100))
            img_array_small = np.array(img_small)
            
            # Analyser la variance des couleurs (les photos ont souvent une plus grande variance)
            if len(img_array_small.shape) == 3:
                std_dev = np.std(img_array_small)
                
                # Calculer le nombre de couleurs uniques (normalisé par la taille)
                flat = img_array_small.reshape(-1, img_array_small.shape[2])
                unique_colors = np.unique(flat, axis=0).shape[0]
                unique_ratio = unique_colors / flat.shape[0]
                
                # Les photos ont souvent une grande variance et beaucoup de couleurs uniques
                return std_dev > 40 and unique_ratio > 0.5
            return False
        except Exception:
            # En cas d'erreur, considérer comme non-photo par défaut
            return False