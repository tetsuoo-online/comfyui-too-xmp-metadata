from .exiftool_manager import ExifToolManager

class ReadXMPMetadata:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("STRING", {"default": ""}),
                "metadata_type": (["Subject", "Description", "Create Date", "Modify Date", "Custom"],),
                "custom_metadata": ("STRING", {"default": ""}),
                "console_debug": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "read_metadata"
    CATEGORY = "too/xmp-metadata"

    def read_metadata(self, image, metadata_type, custom_metadata, console_debug):
        """
        Extrait une métadonnée spécifique d'une image.
        Cette méthode utilise ExifToolManager pour obtenir les métadonnées brutes,
        puis extrait la valeur spécifique demandée.
        """
        # Initialiser ExifToolManager pour lire les métadonnées
        exiftool = ExifToolManager(console_debug=console_debug)
        metadata_dict = exiftool.extract_metadata(image)
        
        if "error" in metadata_dict:
            return (f"Error: {metadata_dict['error']}",)

        # Extraire la métadonnée demandée
        if metadata_type == "Custom":
            output_value = metadata_dict.get(custom_metadata, f"No {custom_metadata} Found")
        else:
            lookup_map = {
                "Subject": "Subject",
                "Description": "Description",
                "Create Date": "Create Date",
                "Modify Date": "Modify Date"
            }
            output_value = metadata_dict.get(lookup_map[metadata_type], f"No {metadata_type} Found")

        return (output_value,)