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

# Required files in GTT and GIM
REQUIRED_GTT_FILES = [
    "textureTool.exe", "textureTool.xml"
]

REQUIRED_GIM_FILES = [
    "filltype_displacement.gim",
    "filltype_height.gim",
    "filltype_normal.gim",
    "filltype_distance_diffuse.gim",
    "filltype_diffuse.gim",  # <-- enable DDS conversion for base diffuse PNG
]

# Enforced output resolutions
RESOLUTIONS = {
    "distance": (256, 256),
    "displacement": (32, 32),
    "height": (512, 512),
    "normal": (1024, 1024)
}

# Base diffuse (pre-processing target)
BASE_DIFFUSE_SIZE = (1024, 1024)

tiles_per_side = 4
tile_size = RESOLUTIONS["distance"][0] // tiles_per_side  # 256/4 -> 64

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


def blend_all(diffuse_cv, height_cv, normal_emboss, target_size):
    """
    Combine channels and return an RGB image resized to target_size.
    """
    # Resize helpers to diffuse size first for consistent combination
    h, w = diffuse_cv.shape[:2]
    height_resized = cv2.resize(height_cv, (w, h), interpolation=cv2.INTER_LANCZOS4)
    normal_resized = cv2.resize(normal_emboss, (w, h), interpolation=cv2.INTER_LANCZOS4)

    r = normal_resized[:, :, 0].astype(np.float32)
    g = normal_resized[:, :, 1].astype(np.float32)
    b = height_resized.astype(np.float32)

    r = np.clip((r * 1.05), 0, 255)
    g = np.clip((g * 1.05), 0, 255)
    b = np.clip((b * 0.9), 64, 255)

    blended = np.stack([r, g, b], axis=-1).astype(np.uint8)
    blended = apply_pink_hue_filter(blended)

    # Ensure final normal size is exactly the enforced resolution
    final = cv2.resize(blended, target_size, interpolation=cv2.INTER_LANCZOS4)
    return final


def force_alpha_if_trivial_or_missing(img: Image.Image):
    """
    Ensure RGBA with a *real* alpha.
    - If no alpha, add alpha=214.
    - If alpha exists but is uniformly 255 (fully opaque), replace with 214.
    - If alpha varies (min < 255), keep as-is.
    Returns: (rgba_img, alpha_was_forced: bool)
    """
    rgba = img.convert("RGBA")
    r, g, b, a = rgba.split()

    had_alpha_channel = ('A' in img.getbands())
    a_np = np.array(a, dtype=np.uint8)
    uniform_255 = (a_np.min() == 255 and a_np.max() == 255)
    no_real_alpha = (not had_alpha_channel) or uniform_255

    if no_real_alpha:
        a = Image.new('L', rgba.size, 214)
        rgba = Image.merge('RGBA', (r, g, b, a))
        return rgba, True

    return rgba, False


def prepare_base_diffuse(input_path: str, out_dir: str, base_name: str):
    """
    Loads the input diffuse, ensures:
      - alpha channel is 'real' (adds/forces alpha=214 if missing or uniformly 255)
      - size is exactly 1024x1024
    If any change was made, saves <base>_diffuse.png.
    If no change, copies the original to the output folder (keeps original extension).
    Returns: (processed_pil_image, used_file_path, wrote_png: bool)
    """
    img = Image.open(input_path)
    changed = False

    # Ensure non-trivial alpha (force 214 if missing or uniformly 255)
    img, alpha_forced = force_alpha_if_trivial_or_missing(img)
    if alpha_forced:
        changed = True

    # Enforce 1024x1024
    if img.size != BASE_DIFFUSE_SIZE:
        img = img.resize(BASE_DIFFUSE_SIZE, Image.LANCZOS)
        changed = True

    if changed:
        out_path = os.path.join(out_dir, f"{base_name}_diffuse.png")
        img.save(out_path)
        print(f"Prepared and saved processed diffuse: {os.path.basename(out_path)}")
        return img, out_path, True  # wrote png
    else:
        # No change: copy original file into output (keep original extension)
        original_ext = os.path.splitext(os.path.basename(input_path))[1].lower()
        new_name = f"{base_name}_diffuse{original_ext}"
        dst_path = os.path.join(out_dir, new_name)
        shutil.copy(input_path, dst_path)
        print(f"No preprocessing needed; copied original diffuse: {new_name}")
        return img, dst_path, False


processed_folders = []

for file in input_files:
    name = os.path.splitext(file)[0]
    base_name = name.replace("_diffuse", "")
    input_path = os.path.join(INPUT_FOLDER, file)
    out_dir = os.path.join(OUTPUT_FOLDER, base_name)
    os.makedirs(out_dir, exist_ok=True)

    # === Base diffuse preprocessing ===
    img_rgba, diffuse_path_in_outdir, diffuse_was_changed = prepare_base_diffuse(
        input_path, out_dir, base_name
    )
    processed_folders.append((base_name, out_dir))

    # Use processed RGBA as the source for subsequent maps
    img = img_rgba
    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGR)

    # === Distance (always 256x256), force alpha=52 everywhere ===
    cluster = img.resize((tile_size, tile_size), Image.LANCZOS)
    distance_rgb = Image.new("RGB", RESOLUTIONS["distance"], (0, 0, 0))
    for row in range(tiles_per_side):
        for col in range(tiles_per_side):
            x = col * tile_size
            y = row * tile_size
            distance_rgb.paste(cluster.convert("RGB"), (x, y))
    r, g, b = distance_rgb.split()
    alpha_52 = Image.new('L', RESOLUTIONS["distance"], 52)
    distance_rgba = Image.merge("RGBA", (r, g, b, alpha_52))
    distance_rgba.save(os.path.join(out_dir, f"{base_name}Distance_diffuse.png"))
    print(f"{base_name}Distance_diffuse.png")

    # === Displacement (always 32x32) ===
    disp = ImageOps.grayscale(img).resize(RESOLUTIONS["displacement"], Image.LANCZOS)
    disp = ImageOps.autocontrast(disp)
    disp = disp.filter(ImageFilter.GaussianBlur(radius=2.5))
    disp = disp.filter(ImageFilter.MedianFilter(size=3))
    disp = limit_blacks(disp, threshold=50)
    disp.save(os.path.join(out_dir, f"{base_name}_displacement.png"))
    print(f"{base_name}_displacement.png")

    # === Height (always 512x512) ===
    height = ImageOps.grayscale(img).resize(RESOLUTIONS["height"], Image.LANCZOS)
    height = ImageOps.autocontrast(height)
    height = limit_blacks(height, threshold=60)
    height = height.filter(ImageFilter.GaussianBlur(radius=0.8))
    height = ImageEnhance.Contrast(height).enhance(1.5)
    height = height.filter(ImageFilter.UnsharpMask(radius=1.2, percent=180))
    height_name = os.path.join(out_dir, f"{base_name}_height.png")
    height.save(height_name)
    print(f"{base_name}_height.png")

    # === Normal (always 1024x1024) ===
    emboss_normal = generate_emboss_normal_for_xy(img)
    normal_final = blend_all(img_cv, np.array(height), emboss_normal, RESOLUTIONS["normal"])
    Image.fromarray(normal_final).save(os.path.join(out_dir, f"{base_name}_normal.png"))
    print(f"{base_name}_normal.png")

print("\nAll texture PNGs generated inside organized /output/<folder>/ folders.")

# --- Conversion phase (GTT) ---
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
            lower = gim_template.lower()

            # Map the naming for the distance diffuse during conversion
            if "distance_diffuse" in lower:
                png_name = f"{base_name}_distance_diffuse.png"   # temp working name for GTT
                pretty_name = f"{base_name}Distance_diffuse.png"  # what we actually saved earlier
                old_path = os.path.join(out_dir, pretty_name)
                temp_path = os.path.join(out_dir, png_name)
                if os.path.exists(old_path):
                    os.rename(old_path, temp_path)
                suffix = "distance_diffuse"

            elif "diffuse.gim" in lower:
                # Base diffuse conversion only if we have PNG (i.e., alpha was forced/resized)
                png_name = f"{base_name}_diffuse.png"
                suffix = "diffuse"

            else:
                suffix = gim_template.replace("filltype_", "").replace(".gim", "")
                png_name = f"{base_name}_{suffix}.png"

            png_path = os.path.join(out_dir, png_name)
            if not os.path.isfile(png_path):
                # If this is the distance temp name, try to restore the pretty name back just in case
                if "distance_diffuse" in lower:
                    pretty = os.path.join(out_dir, f"{base_name}Distance_diffuse.png")
                    if os.path.exists(pretty):
                        # nothing to do; we didn't rename if missing
                        pass
                print(f"Skipping {png_name}, PNG not found.")
                continue

            gim_template_path = os.path.join(GIM_TEMPLATE_FOLDER, gim_template)
            gim_dest_path = os.path.join(out_dir, os.path.splitext(png_name)[0] + ".gim")

            shutil.copy(gim_template_path, gim_dest_path)
            texture_tool_path = os.path.join(GTT_FOLDER, "textureTool.exe")

            try:
                subprocess.run([texture_tool_path, gim_dest_path], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error converting {os.path.basename(gim_dest_path)} with textureTool.exe: {e}")
                # Attempt to restore distance file name if we renamed it
                if "distance_diffuse" in lower:
                    tmp = os.path.join(out_dir, f"{base_name}_distance_diffuse.png")
                    original = os.path.join(out_dir, f"{base_name}Distance_diffuse.png")
                    if os.path.exists(tmp):
                        os.rename(tmp, original)
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

                # Restore pretty name for distance diffuse DDS if needed
                if "distance_diffuse" in lower:
                    corrected_dds = os.path.join(out_dir, f"{base_name}Distance_diffuse.dds")
                    if os.path.exists(dds_path):
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
