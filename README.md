<div align="center">
<H1 align="center">ComfyUI XMP Metadata Tools</H1>
</div>

![Image](https://github.com/user-attachments/assets/ae1f9455-4e22-4ba0-a182-c68a0b10dda5)
<H5>This image contains the workflow, you can drag'n drop it into Comfyui</H5>
<div align="center">

---
[**Getting Started**](#getting-started) | [**Nodes**](#nodes) | [**Credits**](#credits)
---

</div>

### This is the Comfyui version of a personal project I started last year (2024) with GPT/Claude, as a shell/commandline tool to add tags to ANY images on my computer.
<ins>Why you say ? READ THE WHOLE STORY</ins> (or not, your call)

  Because. I.Love.Images. Too much ! So the big idea was to add tags to images instead of yet another gigantic-painful-to-maintain database, that way you CAN'T LOSE THE TAG DATABASE ANYMORE IT'S INSIDE THE FILES !! This is genius. lol
Later on, to find any image that I can't clearly remember the name of, I can simply type a keyword in a pic viewer that supports XML tags, like for example <a href="https://www.xnview.com/">XnView MP</a>.<br>
  Or at least that's the theory of it.<br>
If you had similar needs but for AI generated images with prompts and stuff you would love to use as search tags, I can't recommend anything but the amazing <a href=https://github.com/RupertAvery/DiffusionToolkit>Diffusion Toolkit</a>, it's awesome, <b>TRY IT IT'S GREAT</b><br>
  Picasa was nice too to search from tags, back in the days... a bit limited. A bit dead too, long ago x) Sad. And Lightroom is... meh. Nah. <h1>_ANYWAY_</h1>


This is a few custom nodes for ComfyUI that allow you to READ and WRITE XMP METADATA to images. These tools are particularly useful for preserving and managing tags, descriptions, and other metadata in your images. A sidenote though, this is *not* designed for writing image generation workflows, there's already plenty of nodes for that.

<H3>🟡 Installation</H3>

1. Clone this repository into the `custom_nodes` folder of your ComfyUI installation:
   ```
   git clone https://github.com/tetsuoo-online/comfyui-too-xmp-metadata.git
   ```

2. Make sure ExifTool is installed:
   - Download it <a href=https://exiftool.org/>here</a>
   - rename the EXE (usually called "exiftool(-k).exe") to `exifTool.exe` then put it to the package root folder.

## Tiny node list

<h3>🟢 Read XMP Metadata</h3>
This node extracts XMP metadata from an image file.

- **Inputs**:
  - `image`: Path to the image file
  - `metadata_type`: Type of metadata to extract (Subject, Description, Create Date, Modify Date, or Custom)
  - `custom_metadata`: Custom metadata field to extract (when metadata_type is set to "Custom")
  - `console_debug`: Enable detailed debug messages

- **Outputs**:
  - The extracted metadata value as a string

<H3>🟢 Write XMP Metadata (Lossless)</H3>
This node adds XMP metadata to an existing image file without altering the image data, making the image practically the same size as the original (+ a few bits for the text) but also preserving the original format and timestamps.

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

<H3>🟢 Write XMP Metadata</H3>
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

🔴 IMPORTANT NOTE : For now, the Write XMP Metadata LOSSLESS node will overwrite existing XMP datas but other non-XMP metadata should remain (see image example below). The normal Wtrie XMP Metadata on ther hand re-format the image so if anything was in there will be PURGED before adding the new XMP metadata. So pay attention to that

## Usage Examples
![image](https://github.com/user-attachments/assets/6ad235e5-69f0-4e27-8768-7f2142fdcbee)
<H3>This is the result in XnView</H3>

### Adding tags to an existing image without modifying it

1. Use the "Write XMP Metadata (Lossless)" node
2. Enter the path to your image in `input_image_path`
3. Add your tags as comma-separated values in `metadata` (e.g., "landscape, sunset, ocean")
4. Run the node
5. The tagged image will be saved in a `"tagged"` subfolder in the same directory as the original, unless you specify a custom path

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

** TO DO **
- add tooltips
- add subfolders support maybe. It sounds dangerous, but I need it~

## License

[MIT License](LICENSE)
