import os
import subprocess
import shutil
from .exiftool_manager import ExifToolManager

SCOPE_MAP = {
    "All metadata": "-all=",
    "XMP only":     "-XMP:all=",
    "EXIF only":    "-EXIF:all=",
    "IPTC only":    "-IPTC:all=",
}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}


class ClearImageMetadata:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_path": ("STRING", {"default": ""}),
                "mode": (["File", "Folder"], {"default": "File"}),
                "scope": (list(SCOPE_MAP.keys()), {"default": "All metadata"}),
            },
            "optional": {
                "output_directory": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("output_path", "processed_count")
    FUNCTION = "clear_metadata"
    CATEGORY = "too/xmp-metadata"
    OUTPUT_NODE = True

    def _resolve_output_dir(self, base_dir, output_directory):
        if output_directory:
            out = output_directory.rstrip("/\\")
        else:
            out = os.path.join(base_dir, "cleared")
        os.makedirs(out, exist_ok=True)
        return out

    def _process_file(self, exiftool_path, flag, input_file, output_dir):
        output_path = os.path.join(output_dir, os.path.basename(input_file))
        shutil.copy2(input_file, output_path)

        cmd = [exiftool_path, flag, output_path, "-overwrite_original"]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            raise Exception(f"ClearImageMetadata: Erreur exiftool sur {os.path.basename(input_file)}:\n{result.stderr.strip()}")

        try:
            original_stat = os.stat(input_file)
            os.utime(output_path, (original_stat.st_atime, original_stat.st_mtime))
        except Exception as e:
            print(f"/!\\ Erreur restauration timestamp ({os.path.basename(input_file)}): {e}")

        return output_path

    def clear_metadata(self, input_path, mode="File", scope="All metadata", output_directory=""):
        exiftool_manager = ExifToolManager()
        exiftool_path = exiftool_manager.exiftool_path
        if not exiftool_path:
            raise Exception("ClearImageMetadata: ExifTool non trouvé. Installez-le pour utiliser ce node.")

        input_path = input_path.strip().strip('"').rstrip("/\\")
        flag = SCOPE_MAP.get(scope, "-all=")

        if mode == "File":
            if not input_path:
                raise Exception("ClearImageMetadata: Aucun chemin fourni.")
            if not os.path.isfile(input_path):
                raise Exception(f"ClearImageMetadata: Fichier invalide ou introuvable:\n{input_path}")

            out_dir = self._resolve_output_dir(os.path.dirname(os.path.abspath(input_path)), output_directory)
            output_path = self._process_file(exiftool_path, flag, input_path, out_dir)
            print(f"[OK] Métadonnées effacées ({scope}): {output_path}")
            return (output_path, 1)

        else:  # Folder
            if not input_path:
                raise Exception("ClearImageMetadata: Aucun chemin de dossier fourni.")
            if not os.path.isdir(input_path):
                raise Exception(f"ClearImageMetadata: Dossier invalide ou introuvable:\n{input_path}")

            out_dir = self._resolve_output_dir(input_path, output_directory)
            files = sorted([
                f for f in os.listdir(input_path)
                if os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS
            ])

            if not files:
                raise Exception(f"ClearImageMetadata: Aucune image trouvée dans:\n{input_path}")

            count = 0
            for filename in files:
                src = os.path.join(input_path, filename)
                self._process_file(exiftool_path, flag, src, out_dir)
                count += 1

            print(f"[OK] {count} image(s) traitée(s) ({scope}) → {out_dir}")
            return (out_dir, count)


NODE_CLASS_MAPPINGS = {"ClearImageMetadata": ClearImageMetadata}
NODE_DISPLAY_NAME_MAPPINGS = {"ClearImageMetadata": "TOO Clear Image Metadata"}
