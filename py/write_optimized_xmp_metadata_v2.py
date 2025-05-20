import os
import subprocess
import shutil
import datetime
import numpy as np
import tempfile
from PIL import Image

from .exiftool_manager import ExifToolManager

class WriteOptimizedXMPMetadataV2:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "metadata": ("STRING", {"multiline": True, "default": "1girl, black hair"}),
                "preserve_format": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "original_filenames": ("STRING",),
                "output_dir": ("STRING", {"default": ""}),
                "console_debug": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "write_xmp_optimized"
    CATEGORY = "too/xmp-metadata"
    OUTPUT_NODE = True

    def get_output_path(self, output_dir="", original_filename=None, ext=".png"):
        base_dir = os.path.join(output_dir.rstrip("\\/"), "tagged") if output_dir else os.path.join(os.path.dirname(os.path.abspath(__file__)), "tagged")
        os.makedirs(base_dir, exist_ok=True)

        if original_filename:
            name, _ = os.path.splitext(os.path.basename(original_filename))
            return os.path.join(base_dir, name + ext)
        else:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            return os.path.join(base_dir, f"tagged_image_{timestamp}{ext}")

    def write_xmp_optimized(self, image, metadata, preserve_format=True, original_filenames=None, output_dir="", console_debug=False):
        # Conversion du tenseur vers une image PIL
        i = image[0].cpu().numpy() if len(image.shape) == 4 else image.cpu().numpy()
        i = np.clip(i * 255.0, 0, 255).astype(np.uint8)
        img = Image.fromarray(i)

        # Détection du format
        format_ext = ".png"
        if preserve_format:
            try:
                has_alpha = len(i.shape) > 2 and i.shape[2] == 4
                is_photo_like = self._is_photo_like(i)
                if has_alpha:
                    format_ext = ".png"
                elif is_photo_like:
                    format_ext = ".jpg"
                else:
                    format_ext = ".png"
                if console_debug:
                    print(f"Format détecté : {format_ext} (alpha: {has_alpha}, photo-like: {is_photo_like})")
            except Exception as e:
                if console_debug:
                    print(f"/!\\ Erreur détection format : {e}")

        # Chemin temporaire pour l'image
        with tempfile.NamedTemporaryFile(suffix=format_ext, delete=False) as temp_file:
            temp_path = temp_file.name
            if format_ext == ".jpg":
                img.convert("RGB").save(temp_path, format="JPEG", quality=95)
            else:
                img.save(temp_path, format="PNG")

        # Chemin final
        original_filename = None
        if original_filenames:
            try:
                import json
                filenames = json.loads(original_filenames)
                if isinstance(filenames, list) and len(filenames) > 0:
                    original_filename = filenames[0]
            except:
                original_filename = original_filenames
        output_path = self.get_output_path(output_dir, original_filename, format_ext)

        # Lire les métadonnées existantes
        exiftool = ExifToolManager(console_debug=console_debug)
        existing_meta = exiftool.read_metadata(temp_path)

        # Préparer les nouvelles métadonnées
        try:
            import json
            meta_dict = json.loads(metadata)
        except:
            meta_dict = {"tags": metadata}

        new_tags = []
        if isinstance(meta_dict, dict) and "tags" in meta_dict:
            if isinstance(meta_dict["tags"], list):
                new_tags = meta_dict["tags"]
            elif isinstance(meta_dict["tags"], str):
                new_tags = [t.strip() for t in meta_dict["tags"].split(",")]
        elif isinstance(meta_dict, str):
            new_tags = [t.strip() for t in meta_dict.split(",")]

        cmd = [exiftool.exiftool_path]
        for tag in new_tags:
            cmd.append(f"-XMP-dc:Subject+={tag}")
        if isinstance(meta_dict, dict):
            for k, v in meta_dict.items():
                if k != "tags" and not isinstance(v, (dict, list)):
                    cmd.append(f"-XMP-comfyui:{k}={v}")

        cmd.append(temp_path)
        cmd.append("-overwrite_original")

        if console_debug:
            print("--- Commande ExifTool ---")
            print(" ".join(cmd))
            print("-------------------------")

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if console_debug:
            print("--- Sortie d'ExifTool ---")
            for line in result.stdout.split("\n"):
                if line.strip():
                    print(line)
            if result.stderr.strip():
                print("--- Erreurs d'ExifTool ---")
                print(result.stderr)
            print("-------------------------")

        if result.returncode != 0:
            print(f"/!\\ Erreur lors de l'écriture des métadonnées : {result.stderr}")
            os.unlink(temp_path)
            return (f"Erreur: {result.stderr}",)

        # Déplacer le fichier final
        shutil.copy2(temp_path, output_path)
        os.utime(output_path, None)
        os.unlink(temp_path)

        print(f"[OK] Image avec XMP écrite : {output_path}")
        return (output_path,)

    def _is_photo_like(self, img_array):
        try:
            img = Image.fromarray(img_array)
            img_small = img.resize((100, 100))
            arr = np.array(img_small)

            if len(arr.shape) == 3:
                std_dev = np.std(arr)
                flat = arr.reshape(-1, arr.shape[2])
                unique_colors = np.unique(flat, axis=0).shape[0]
                unique_ratio = unique_colors / flat.shape[0]
                return std_dev > 40 and unique_ratio > 0.5
            return False
        except:
            return False
