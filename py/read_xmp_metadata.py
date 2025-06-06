from .exiftool_manager import ExifToolManager

class ReadXMPMetadata:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("STRING", {"default": ""}),
                "metadata_type": (["Subject", "Description", "Create Date", "Modify Date", "Custom", "ALL"],),
                "custom_metadata": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "read_metadata"
    CATEGORY = "too/xmp-metadata"

    def read_metadata(self, image, metadata_type, custom_metadata):
        """
        Extrait une métadonnée spécifique d'une image ou toutes les métadonnées XMP.
        Cette méthode utilise ExifToolManager pour obtenir les métadonnées brutes,
        puis extrait la valeur spécifique demandée ou toutes les métadonnées.
        """
        # Déterminer si on veut toutes les métadonnées
        get_all_metadata = (metadata_type == "ALL" or 
                           (metadata_type == "Custom" and custom_metadata.strip() in ["*", "ALL", "all"]))
        
        # Initialiser ExifToolManager pour lire les métadonnées
        exiftool = ExifToolManager(console_debug=True)  # Debug temporairement activé
        
        if get_all_metadata:
            metadata_dict = exiftool.extract_all_xmp_metadata(image)
        else:
            metadata_dict = exiftool.extract_metadata(image)
        
        if "error" in metadata_dict:
            return (f"Error: {metadata_dict['error']}",)

        # Traitement selon le type de métadonnée demandé
        if get_all_metadata:
            # Formatter toutes les métadonnées XMP de manière lisible
            if not metadata_dict:
                return ("No XMP metadata found",)
            
            formatted_output = []
            formatted_output.append("=== XMP Metadata ===")
            
            # Trier les clés pour un affichage cohérent
            sorted_keys = sorted(metadata_dict.keys())
            
            for key in sorted_keys:
                value = metadata_dict[key]
                # Nettoyer et formatter l'affichage
                clean_key = key.replace("XMP-", "").replace(":", " > ")
                formatted_output.append(f"{clean_key}: {value}")
            
            formatted_output.append("====================")
            return ("\n".join(formatted_output),)
            
        elif metadata_type == "Custom":
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