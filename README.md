## 📘 FS25 Fill Type Texture Maker Python – Beginner Setup & Usage Guide

This tool helps you make Entry Level Farming Simulator 25 fillType textures automatically (like distance, height, displacement, normal maps) using just your main diffuse, While they wont be the absolute best quality and will never be as good as a human artist can do this will help modders that are not artists and don't have access to expensive software or the time to learn and look for free alternatives a descent and free alternative. You will need to read this readme to understand how it works but once you have learned its in and outs it can create your textures in a matter of seconds to minutes.

I do not have a sign certificate so Windows will prompt you that it protected your PC: I have provided ALL code and files on here so you can look it over and see its safe to use, (minus the sub installers as github doesnt allow them to be uploaded) this exe was the easiest way for me to provide you to tools to install everything you needed rather then trying to walk new users through how to install python on their PCs and teach them commands through text. This being said it will install the files on c:/diffusemakerPython by default and then it will install Python3.11.8-amd64 this sub program is how the script works. It provides you with the ability to uninstall EVERYTHING that it installs from inside the folder it is in using the uninstaller (if you use add or remove programs it may leave python on your computer, while using the uninstaller if you dont like the program but you want to keep Python incase you had it installed prior to installing this it prompts you in cmd prompt if you would like to uninstall Python or not using the uninstaller in the folder.

## 📅 FIRST TIME SETUP (DO THIS ONCE)

1. 🔽 Download and unzip the whole folder
   Example: C:\Users\YourName\Documents\diffusemakerPython

2. ▶️ Run the installer
   Double-click:
   setup\_fs25\_texture\_tool.bat

   This will:

   * Install Python
   * Add Python to your PATH
   * Install needed tools (Pillow, NumPy, OpenCV)
   * Add texconv.exe to your system so python can use it ✅

## 3. 📦 Install the GIANTS Texture Tool (Required) EXTREAMLEY IMPORTANT

   * Go to: [https://gdn.giants-software.com/downloads.php](https://gdn.giants-software.com/downloads.php)
   * create an account and login
   * Scroll to "GIANTS Texture Tool" and download it
   * Extract ALL files into the folder inside the current directory:
     diffusemakerPython\giantsTextureTool

4. 📦 Run install_requirements.bat, This will install all addons needed for python for the tool to work. (Required)


   ⚠️ DO NOT delete any of the .cmd, .exe, .xml, or .gim files!


## 📁 WHAT FILES SHOULD BE IN THE FOLDER?

Your folder should look like this:

diffusemakerPython
├─ generate\_all\_texture\_types.py      ← The beast that makes it all happen
├─ launch\_texture\_tool.bat            ← Double-click this to start the tool
├─ README\_FS25\_Texture\_Tool.txt      ← This help file
├─ giantsTextureTool\                 ← Where to put your files from GIANTS Texture tool download
│   ├─ readme.txt                    ← Not Required
│   ├─ textureTool.exe               ← ⚠️***Required files from GIANTS download (⚠️not included⚠️)
│   ├─ textureTool.xml               ← ⚠️***Required files from GIANTS download (⚠️not included⚠️)
│   └─ textureTool\_log.txt          ← This will be generated each time you run the convert tool don't worry its not required
├─ gims\                              ← Contains template GIM files used during conversion
│   ├─ filltype\_diffuse.gim               ← Convert your main image to proper dds format
│   ├─ filltype\_displacement.gim          ← Convert your displacement image to proper dds format
│   ├─ filltype\_distance\_diffuse.gim     ← Convert your distance image to proper dds format
│   ├─ filltype\_height.gim                ← Convert your height image to proper dds format
│   └─ filltype\_normal.gim                ← Convert your normal image to proper dds format
├─ input\                             ← ❗❗❗❗Drop your \_diffuse textures here❗❗❗❗
│   └─                                ← ❗❗❗❗Drop your \_diffuse textures here❗❗❗❗
└─ output\                            ← ❗❗❗❗ Output folders will be created here❗❗❗❗

⚠️ DO NOT DELETE anything except the textures you drop in yourself or the folders within the output folder.

## 🖼️ HOW TO ADD YOUR TEXTURE

Put your texture into the "input" folder.

Your image should:

* Be named like:  example\_diffuse.png
* Must include "\_diffuse" at the end of the filename
* Can be a .png or .dds file

## 🚀 HOW TO RUN THE TOOL

1. Drop your texture into the input folder
2. Double-click: launch\_texture\_tool.bat
3. Follow the prompts:

   * Convert to DDS? → Y
   * Keep PNG files? → Y/N (your choice)
   * ❗ Delete original image? → Y = Recommended

## ⚠️ WHY THE LAST PROMPT MATTERS

ALWAYS say Y to delete the original \_diffuse image from the input folder.

If you don't:

* The tool will remake the same image again every time you run it.
* This causes duplicate folders and wasted processing.


## 🧹 UNINSTALLING THE TOOL (OPTIONAL)

To uninstall:

Open your Start Menu or go to Control Panel > Programs and Features

Look for "FS25 Texture Tool"

Click Uninstall

You will be asked:

If you'd like to remove the tool folder and its contents

🔴 ATTENTION: The installation process also installed Python if it was not already present on your PC. Would you like to uninstall that as well?

Saying "Yes" will remove Python and all related packages installed with the tool

Saying "No" will keep your current Python setup untouched

## 🖼️ SHORTCUTS & ICONS

A shortcut to the C:\diffusemakerPython folder will be placed on your Desktop (optional)

The folder shortcut will be assigned the icon:
diffusemakerPython\FS25FTTMP.ico

The installer .exe itself will also use this icon


## 🎉 THAT’S IT!

Keep adding new textures to input\ and double-click launch_texture_tool.bat to convert them.

All results go to the output\ folder.

Happy modding!



Happy modding!

DtapGaming
