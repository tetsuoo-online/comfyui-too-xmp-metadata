import os
import subprocess
import shutil
import datetime
import numpy as np
import torch
from PIL import Image

class WriteXMPMetadataTensor:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "metadata": ("STRING", {"multiline": True, "default": "1girl, black hair"}),
                "format_mode": (["Preserve format", "Smart format", "Force PNG", "Force JPG"],),
            },
            "optional": {
                "input_image_path": ("STRING", {"default": ""}),  # Pour préserver le nom si disponible
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
        exiftool_local = os.path.join(module_path, "../exiftool.exe")
        if os.path.exists(exiftool_local):
            return os.path.abspath(exiftool_local)
        return None

    def get_output_path(self, output_dir="", output_format=".png", input_image_path=""):
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
        if output_dir:
            # Si un répertoire de sortie est spécifié, l'utiliser
            base_dir = output_dir.rstrip("\\/")
        elif input_image_path:
            # Si un chemin d'image est fourni, utiliser son répertoire
            original_dir = os.path.dirname(os.path.abspath(input_image_path))
            base_dir = os.path.join(original_dir, "tagged")
        else:
            # Sinon, utiliser le répertoire par défaut
            base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tagged")
        
        os.makedirs(base_dir, exist_ok=True)
        return os.path.join(base_dir, filename)

    def write_xmp(self, image, metadata, format_mode="Preserve format", input_image_path="", output_dir="", console_debug=False):
        """
        Écrit les métadonnées XMP sur une image, en choisissant le format selon le mode
        """
        # Vérifier si ExifTool est disponible
        exiftool_path = self.get_exiftool_path()
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
                if console_debug:
                    print(f"Format non supporté: {output_format}, utilisation de PNG par défaut")
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
                
            if console_debug:
                print(f"Format déterminé: {output_format} (Alpha: {has_alpha}, Photo-like: {is_photo_like})")
        else:
            # Par défaut ou si le chemin d'entrée n'est pas fourni
            output_format = ".png"
        
        # Obtenir le chemin de sortie
        output_path = self.get_output_path(output_dir, output_format, input_image_path)
        
        # Sauvegarder l'image dans le format approprié
        if console_debug:
            print(f"-> Sauvegarde de l'image au format {output_format}: {output_path}")
            
        if output_format.lower() in ['.jpg', '.jpeg']:
            img.save(output_path, format="JPEG", quality=95)
        elif output_format.lower() == '.webp':
            img.save(output_path, format="WEBP", quality=95)
        else:
            img.save(output_path, format="PNG")
            
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
            print(f"-> Commande ExifTool: {cmd}")
            
        # Exécuter la commande pour ajouter les métadonnées
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            print(f"/!\\ Erreur lors de l'application des métadonnées: {result.stderr}")
            # On ne supprime pas le fichier de sortie, il peut toujours être utilisable
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