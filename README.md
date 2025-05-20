![Image](https://github.com/user-attachments/assets/ae1f9455-4e22-4ba0-a182-c68a0b10dda5)

# ComfyUI XMP Metadata Tools

### This is the Comfyui version of a very personal project I started last year (2024) with GPT/Claude, as a shell/commandline tool to add tags to ANY images on my computer.
Why you say ? Whole unecessary story down below
<details>
  <summary>Click to expand</summary>
  Because. I.Love.Images. Too much ! So the big idea was to add tags to images instead of yet another gigantic-painful-to-maintain database, that way you CAN'T LOSE THE TAGS ANYMORE IT'S INSIDE THE FILES ALREADY !! This is genius. lol
Later on, to find any image that I can't clearly remember the name of, I can simply type a keyword in a pic viewer that supports XML tags, like for example [XnView MP](https://www.xnview.com/).
Picasa was nice too, a bit limited. A bit dead too, long ago x) Sad.
  ANYWAY</details>

This a few custom nodes for ComfyUI that allow you to READ and WRITE XMP METADATA to images. These tools are particularly useful for preserving and managing tags, descriptions, and other metadata in your images. A sidenote though, this is *not* designed for writing image generation workflows, there's already plenty of nodes for that.


## Features

### Read XMP Metadata
This node extracts XMP metadata from an image file.

- **Inputs**:
  - `image`: Path to the image file
  - `metadata_type`: Type of metadata to extract (Subject, Description, Create Date, Modify Date, or Custom)
  - `custom_metadata`: Custom metadata field to extract (when metadata_type is set to "Custom")
  - `console_debug`: Enable detailed debug messages

- **Outputs**:
  - The extracted metadata value as a string

### Write XMP Metadata (Lossless)
This node adds XMP metadata to an existing image file without altering the image data, preserving the original format and timestamps.

- **Inputs**:
  - `input_image_path`: Path to the original image file
  - `metadata`: Metadata to add (string or JSON)
  - `output_dir`: (Optional) Custom output directory
  - `console_debug`: (Optional) Enable detailed debug messages

- **Outputs**:
  - Path to the output image file

- **Features**:
  - **Lossless operation**: Preserves the original image without recompression
  - **Format preservation**: Keeps the original file format (PNG, JPG, WEBP, etc.)
  - **Date preservation**: Maintains the original creation and modification dates
  - **Safe operation**: Avoids processing loops by detecting files in "tagged" folders

### Write XMP Metadata
This node adds XMP metadata to an image tensor, with options for choosing the output format.

- **Inputs**:
  - `image`: Image tensor
  - `metadata`: Metadata to add (string or JSON)
  - `format_mode`: Format selection (Preserve format, Smart format, Force PNG, Force JPG)
  - `input_image_path`: (Optional) Path to the original image for name and format reference
  - `output_dir`: (Optional) Custom output directory
  - `console_debug`: (Optional) Enable detailed debug messages

- **Outputs**:
  - Path to the output image file

- **Features**:
  - **Smart format detection**: Can automatically select the best format based on image content
  - **Format options**: Can force specific formats or try to preserve the original format
  - **Integration with ComfyUI workflow**: Works directly with image tensors from other nodes

## Installation

1. Clone this repository into the `custom_nodes` folder of your ComfyUI installation:
   ```
   cd ComfyUI/custom_nodes
   git clone https://github.com/yourusername/comfyui-too-xmp-metadata.git
   ```

2. Make sure ExifTool is installed:
   - Windows: The extension includes ExifTool.exe
   - Linux/Mac: Install ExifTool via your package manager

3. Restart ComfyUI

## Usage Examples

### Adding tags to an existing image without modifying it

1. Use the "Write XMP Metadata (Lossless)" node
2. Enter the path to your image in `input_image_path`
3. Add your tags as comma-separated values in `metadata` (e.g., "landscape, sunset, ocean")
4. Run the node
5. The tagged image will be saved in a "tagged" subfolder in the same directory as the original

### Adding metadata to a generated image

1. Connect your image generation output to the "Write XMP Metadata" node
2. Add your metadata in the `metadata` field
3. Choose a format mode (Smart format is recommended)
4. Run the node
5. The image with metadata will be saved in the output directory

### Reading tags from an image

1. Use the "Read XMP Metadata" node
2. Enter the path to your image in `image`
3. Set `metadata_type` to "Subject" to extract tags
4. Run the node
5. The tags will be returned as a string

## Metadata Format

The `metadata` input can be either:

1. A simple string with comma-separated values (e.g., "landscape, sunset, ocean")
2. A JSON object with a "tags" key and other custom fields:
   ```json
   {
     "tags": ["landscape", "sunset", "ocean"],
     "author": "John Doe",
     "description": "Beautiful sunset at the beach"
   }
   ```

## Requirements

- ComfyUI
- ExifTool
- PIL/Pillow
- NumPy

## License

[MIT License](LICENSE)
