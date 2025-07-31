import os
import subprocess
import shutil
from PIL import Image, ImageFilter, ImageOps, ImageEnhance
import numpy as np
import cv2

# Paths
INPUT_FOLDER = "input"
OUTPUT_FOLDER = "output"
GIM_TEMPLATE_FOLDER = "gims"
GTT_FOLDER = "giantsTextureTool"

REQUIRED_GTT_FILES = [
    "textureTool.exe", "textureTool.xml"
]

REQUIRED_GIM_FILES = [
    "filltype_displacement.gim", "filltype_height.gim",
    "filltype_normal.gim", "filltype_distance_diffuse.gim"
]

RESOLUTIONS = {
    "distance": (256, 256),
    "displacement": (32, 32),
    "height": (256, 256),
    "normal": (512, 512)
}

tiles_per_side = 4
tile_size = RESOLUTIONS["distance"][0] // tiles_per_side

valid_ext = [".dds", ".png"]
input_files = [
    f for f in os.listdir(INPUT_FOLDER)
    if "_diffuse" in f and os.path.splitext(f)[1].lower() in valid_ext
]

if not input_files:
    print("No _diffuse.dds or .png files found in /input")
    exit()

def limit_blacks(img, threshold=40):
    np_img = np.array(img)
    np_img = np.clip(np_img, threshold, 255)
    return Image.fromarray(np_img.astype(np.uint8))

def validate_environment():
    print("\nValidating Giants Texture Tool files...")
    missing = []
    for f in REQUIRED_GTT_FILES:
        if not os.path.isfile(os.path.join(GTT_FOLDER, f)):
            missing.append(f)
    if missing:
        print(f"Conversion of pngs not possible, Giants Texture Tool is not found in {os.path.abspath(GTT_FOLDER)}.")
        print("Please download the Tool from https://gdn.giants-software.com/downloads.php")
        print("and extract it into the folder above where readme should be visible.")
        return False
    else:
        print("Giants Texture Tool files verified.")

    print("\nValidating GIM template files...")
    for f in REQUIRED_GIM_FILES:
        if not os.path.isfile(os.path.join(GIM_TEMPLATE_FOLDER, f)):
            print(f"Missing GIM file: {f} in {GIM_TEMPLATE_FOLDER}.")
            return False
    print("GIM templates verified.")
    return True

def apply_pink_hue_filter(image):
    img_hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    img_hsv[..., 0] = (img_hsv[..., 0] + 140) % 180
    return cv2.cvtColor(img_hsv, cv2.COLOR_HSV2RGB)

def generate_emboss_normal_for_xy(pil_image):
    gray = ImageOps.grayscale(pil_image)
    emboss = gray.filter(ImageFilter.EMBOSS)
    emboss_np = np.array(emboss).astype(np.float32) / 255.0
    gx = cv2.Sobel(emboss_np, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(emboss_np, cv2.CV_32F, 0, 1, ksize=3)
    gz = np.ones_like(gx) * 0.5
    norm = np.sqrt(gx**2 + gy**2 + gz**2)
    nx = (gx / norm + 1) * 127.5
    ny = (gy / norm + 1) * 127.5
    nz = (gz / norm + 1) * 127.5
    return np.stack([nx, ny, nz], axis=-1).astype(np.uint8)

def blend_all(diffuse_cv, height_cv, normal_emboss):
    height_resized = cv2.resize(height_cv, (diffuse_cv.shape[1], diffuse_cv.shape[0]))
    normal_resized = cv2.resize(normal_emboss, (diffuse_cv.shape[1], diffuse_cv.shape[0]))
    r = normal_resized[:, :, 0].astype(np.float32)
    g = normal_resized[:, :, 1].astype(np.float32)
    b = height_resized.astype(np.float32)
    r = np.clip((r * 1.05), 0, 255)
    g = np.clip((g * 1.05), 0, 255)
    b = np.clip((b * 0.9), 64, 255)
    blended = np.stack([r, g, b], axis=-1).astype(np.uint8)
    return apply_pink_hue_filter(blended)

processed_folders = []

for file in input_files:
    name = os.path.splitext(file)[0]
    base_name = name.replace("_diffuse", "")
    input_path = os.path.join(INPUT_FOLDER, file)
    out_dir = os.path.join(OUTPUT_FOLDER, base_name)
    os.makedirs(out_dir, exist_ok=True)

    original_ext = os.path.splitext(file)[1].lower()
    print(f"Moving {file} into {out_dir}")
    new_name = f"{base_name}_diffuse{original_ext}"
    shutil.copy(input_path, os.path.join(out_dir, new_name))
    processed_folders.append((base_name, out_dir))

    img = Image.open(input_path).convert("RGBA")
    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGR)

    cluster = img.resize((tile_size, tile_size), Image.LANCZOS)
    distance_canvas = Image.new("RGBA", RESOLUTIONS["distance"], (0, 0, 0, 0))
    for row in range(tiles_per_side):
        for col in range(tiles_per_side):
            x = col * tile_size
            y = row * tile_size
            distance_canvas.paste(cluster, (x, y), cluster)
    r, g, b, a = distance_canvas.split()
    a = a.filter(ImageFilter.GaussianBlur(radius=1.2))
    distance_img = Image.merge("RGBA", (r, g, b, a))
    distance_img.save(os.path.join(out_dir, f"{base_name}Distance_diffuse.png"))
    print(f"{base_name}Distance_diffuse.png")

    disp = ImageOps.grayscale(img).resize(RESOLUTIONS["displacement"], Image.LANCZOS)
    disp = ImageOps.autocontrast(disp)
    disp = disp.filter(ImageFilter.GaussianBlur(radius=2.5))
    disp = disp.filter(ImageFilter.MedianFilter(size=3))
    disp = limit_blacks(disp, threshold=50)
    disp.save(os.path.join(out_dir, f"{base_name}_displacement.png"))
    print(f"{base_name}_displacement.png")

    height = ImageOps.grayscale(img).resize(RESOLUTIONS["height"], Image.LANCZOS)
    height = ImageOps.autocontrast(height)
    height = limit_blacks(height, threshold=60)
    height = height.filter(ImageFilter.GaussianBlur(radius=0.8))
    height = ImageEnhance.Contrast(height).enhance(1.5)
    height = height.filter(ImageFilter.UnsharpMask(radius=1.2, percent=180))
    height_name = os.path.join(out_dir, f"{base_name}_height.png")
    height.save(height_name)
    print(f"{base_name}_height.png")

    emboss_normal = generate_emboss_normal_for_xy(img)
    normal_final = blend_all(img_cv, np.array(height), emboss_normal)
    Image.fromarray(normal_final).save(os.path.join(out_dir, f"{base_name}_normal.png"))
    print(f"{base_name}_normal.png")

print("\nAll texture PNGs generated inside organized /output/<folder>/ folders.")

while not validate_environment():
    retry = input("Have you extracted the files into the correct folder? (Y/N): ").strip().upper()
    if retry == "Y":
        continue
    skip = input("Would you like to skip converting the files? (Y/N): ").strip().upper()
    if skip == "Y":
        print("Conversion skipped by user. Exiting.")
        exit()

convert = input("All files are present for conversion. Convert images to DDS? (Y/N): ").strip().upper()
if convert != "Y":
    print("Conversion skipped by user.")
else:
    keep_pngs = input("Would you like to keep the PNG files? (Y/N): ").strip().upper() == "Y"
    print("Ready for DDS conversion step...")

    for base_name, out_dir in processed_folders:
        print(f"Converting images in: {out_dir}")
        for gim_template in REQUIRED_GIM_FILES:
            if "distance_diffuse" in gim_template.lower():
                suffix = "Distance_diffuse"
                png_name = f"{base_name}_distance_diffuse.png"
                target_name = f"{base_name}Distance_diffuse.png"
                old_path = os.path.join(out_dir, target_name)
                temp_path = os.path.join(out_dir, png_name)
                if os.path.exists(old_path):
                    os.rename(old_path, temp_path)
            else:
                suffix = gim_template.replace("filltype_", "").replace(".gim", "")
                png_name = f"{base_name}_{suffix}.png"

            gim_name = os.path.splitext(png_name)[0] + ".gim"
            png_path = os.path.join(out_dir, png_name)
            gim_template_path = os.path.join(GIM_TEMPLATE_FOLDER, gim_template)
            gim_dest_path = os.path.join(out_dir, gim_name)

            if not os.path.isfile(png_path):
                print(f"Skipping {png_name}, PNG not found.")
                continue

            shutil.copy(gim_template_path, gim_dest_path)
            texture_tool_path = os.path.join(GTT_FOLDER, "textureTool.exe")

            try:
                subprocess.run([texture_tool_path, gim_dest_path], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error converting {gim_name} with textureTool.exe: {e}")
                continue

            dds_path = os.path.splitext(png_path)[0] + ".dds"
            if os.path.isfile(dds_path):
                if keep_pngs:
                    png_subfolder = os.path.join(out_dir, "PNGs")
                    os.makedirs(png_subfolder, exist_ok=True)
                    shutil.move(png_path, os.path.join(png_subfolder, os.path.basename(png_path)))
                else:
                    os.remove(png_path)

                os.remove(gim_dest_path)
                print(f"{os.path.basename(dds_path)} created and PNG processed.")

                if "distance_diffuse" in png_name.lower():
                    corrected_dds = os.path.join(out_dir, f"{base_name}Distance_diffuse.dds")
                    os.rename(dds_path, corrected_dds)
            else:
                print(f"DDS file not found for {png_name}. PNG not deleted.")

# ✅ Always ask this LAST
delete_originals = input("Would you like to delete the original texture from the input folder? (Y/N): ").strip().upper() == "Y"
if delete_originals:
    for file in input_files:
        input_path = os.path.join(INPUT_FOLDER, file)
        if os.path.isfile(input_path):
            os.remove(input_path)
            print(f"Deleted original: {file}")
