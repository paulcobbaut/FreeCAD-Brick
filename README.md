## FreeCAD-Brick
Creating Lego compatible bricks using FreeCAD and Python
![cover_20230518_all](https://github.com/paulcobbaut/FreeCAD-Brick/assets/524195/c28b69c3-1377-44be-9013-bbd45a20d1ee)

### What kind of (Lego-compatible) bricks?
Thousands of different regular bricks (any width, any length, any height)
![regular_brick_cad](https://github.com/paulcobbaut/FreeCAD-Brick/assets/524195/6cf8559a-5529-4831-9c5a-1514c2a65902)

Thousands of different corner bricks
![corner_brick_cad](https://github.com/paulcobbaut/FreeCAD-Brick/assets/524195/7ad69420-8087-4e23-9f17-9076a849e52b)

Thousands of different bricks with a hole in the middle
![holed_brick_cad](https://github.com/paulcobbaut/FreeCAD-Brick/assets/524195/7019fb3c-a43c-4841-947e-270c355674a2)

Thousands of pockets (open boxes) with studs
![pocket_brick_cad](https://github.com/paulcobbaut/FreeCAD-Brick/assets/524195/d9561c51-8464-4193-b3df-b1214d6bd794)

Thousands of slopes
![slopes_brick_cad](https://github.com/paulcobbaut/FreeCAD-Brick/assets/524195/00b4c9dc-d9a1-400c-adf0-b1e069fc1aa6)

See also: https://www.printables.com/model/481897-different-bricks
Video: https://youtu.be/ygqz-4S8DuU

### How to use the Python scripts?
There are some sample .stl files attached here, but the main idea is to run one of the Python scripts to generate the exact .stl files that you want.

In short:
1. open the Python script in FreeCAD
2. change the directory (folder) to your preferred export path
3. run the script in FreeCAD
4. Open the directory(folder) and find the .stl files

### Export directory(folder)

**This is a must do or you get an error!!!**
**This is a must do or you get an error!!!**
**This is a must do or you get an error!!!**

Somewhere around line 37 to 41 in the scripts there are lines like this:

```
### The directory to export the .stl files to
export_directory = "/home/paul/FreeCAD/generated_bricks/"
````

This is the location where the .stl files are written on your computer. This directory (or folder) must already exist before running the script!

You probably need to change this, for example (MS Windows, Ubuntu, Mac):
export_directory = "C:"
export_directory = "/home/bob"
export_directory = "/Users/Alice"

Test that this works before changing the Python script.
