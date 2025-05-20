from .py.read_xmp_metadata import ReadXMPMetadata
from .py.write_xmp_metadata import WriteXMPMetadataLossless
from .py.write_xmp_tensor import WriteXMPMetadataTensor

# Définition des mappings directement dans __init__.py
NODE_CLASS_MAPPINGS = {
    "ReadXMPMetadata": ReadXMPMetadata,
    "WriteXMPMetadataLossless": WriteXMPMetadataLossless,
    "WriteXMPMetadataTensor": WriteXMPMetadataTensor
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ReadXMPMetadata": "Read XMP Metadata",
    "WriteXMPMetadataLossless": "Write XMP Metadata (Lossless)",
    "WriteXMPMetadataTensor": "Write XMP Metadata"
}

# Define the web directory for ComfyUI to find our JavaScript files
WEB_DIRECTORY = "./web"

# Exporter les variables pour qu'elles soient accessibles
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]