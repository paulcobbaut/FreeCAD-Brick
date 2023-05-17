"""
regular_brick.py -- Paul Cobbaut, 2023-05-17
The goal is to make Lego-compatible pieces for use in 3D printer
The script generates .stl files in a directory.
"""
# Dimensions for studs
stud_radius_mm		= 2.475		# Lego official is 2.400
stud_center_spacing_mm	= 8.000
stud_height_mm		= 1.700		# Lego official is 1.600

# Dimensions for plates
plate_height_mm		= 3.200
plate_width_mm		= 7.800

# The gap that is added to the width/length for each extra stud
gap_mm 			= 0.200

# Dimensions for bricks
brick_height_mm		= 9.600		# plate_height_mm * 3
brick_width_mm		= 7.800		# = plate_width_mm

# Wall thickness for bricks and plates
wall_thickness_mm	= 1.500		# 1.2 and 0.3 for new small beams or 1.5 for old bricks
top_thickness_mm	= 1.000		# the 'ceiling' of a brick is thinner than the sides

# Dimensions underside rings
ring_radius_outer_mm	= 3.250 	# was 3.220 on 1028, 3.226 on 20220929 (should be 3.2500)
ring_radius_inner_mm	= 2.500		# was 2.666 pm 1029, 2.456 on 20220930, 2.556 on 20221001 (should be 2.400)

# Dictionary of bricks generated; name:(studs_x, studs_y, plate_z) --> (width, length, height)
bricks = {}

# Used to visually separate the bricks in FreeCAD GUI
offset = 0

# The directory to export the .stl files to
export_directory = "/home/paul/FreeCAD/generated_bricks/"

import FreeCAD
from FreeCAD import Base, Vector
import Part
import Sketcher
import Mesh
import MeshPart

# create a FreeCAD document and Part Design body
doc = FreeCAD.newDocument("Lego brick generated")
obj = doc.addObject("PartDesign::Body", "Body")

# create a standard x, y, z box in FreeCAD
def make_box(name, x, y, z):
    obj = doc.addObject("Part::Box", name)
    obj.Length = x
    obj.Width  = y
    obj.Height = z
    return obj

# convert studs to mm for bricks and plates
# one stud on brick	= 1 * brick_width_mm
# two studs on brick	= 2 * brick_width_mm + 1 * gap_mm
# three studs on brick	= 3 * brick_width_mm + 2 * gap_mm
# plate_width_mm is identical to brick_width_mm
def convert_studs_to_mm(studs):
    mm = (studs * brick_width_mm) + ((studs - 1) * gap_mm)
    return mm

# the stud template is created once then always copied
def make_stud(name):
    obj = doc.addObject("Part::Cylinder", name)
    obj.Radius = stud_radius_mm
    obj.Height = stud_height_mm
    doc.recompute()
    return obj

# creating the template
stud_template = make_stud("stud_template")
stud_template.ViewObject.hide()

# name the brick
# add brick to bricks dictionary using name
def name_a_corner_brick(left_length, left_width, bottom_length, bottom_height, plate_z):
    left_name   = '_left_' + str(left_length) + 'x' + str(left_width)
    bottom_name = '_bottom_' + str(bottom_length) + 'x' + str(bottom_height)
    name         = 'cornerbrick_' + left_name + bottom_name
    bricks[name] = (left_length, left_width, bottom_length, bottom_height, plate_z)
    return name

def create_corner_hull(brick_name):
    # create the hull without studs and without rings
    left_l   = bricks[brick_name][0]
    left_w   = bricks[brick_name][1]
    bottom_l = bricks[brick_name][2]
    bottom_h = bricks[brick_name][3]
    z        = bricks[brick_name][4]
    height   = z * plate_height_mm
    # create the left (outer) part, full
    # then create the bottom (outer) part, full
    outer_left_w = convert_studs_to_mm(left_w)
    outer_left_l = convert_studs_to_mm(left_l)
    outer_left_prism = make_box("outer_left_prism", outer_left_w, outer_left_l, height)
    outer_bottom_l = convert_studs_to_mm(bottom_l + left_w) # include corner
    outer_bottom_h = convert_studs_to_mm(bottom_h)
    outer_bottom_prism = make_box("outer_bottom_prism", outer_bottom_l, outer_bottom_h, height)
    # unite these two parts
    outer_corner = doc.addObject('Part::Fuse', brick_name + "_outer")
    outer_corner.Base = outer_left_prism
    outer_corner.Tool = outer_bottom_prism

    # create the inner cutout for both parts and unite them
    # cut the inner cutout from the outer one
    inner_height = height - top_thickness_mm
    inner_left_w = outer_left_w - (2 * wall_thickness_mm)
    inner_left_l = outer_left_l - (2 * wall_thickness_mm)
    inner_left_prism = make_box("inner_left_prism", inner_left_w, inner_left_l, inner_height)
    inner_bottom_l = outer_bottom_l - (2 * wall_thickness_mm)
    inner_bottom_h = outer_bottom_h - (2 * wall_thickness_mm)
    inner_bottom_prism = make_box("inner_bottom_prism", inner_bottom_l, inner_bottom_h, inner_height)
    # place the inner prisms at x and y exactly one wall thickness
    inner_left_prism.Placement = FreeCAD.Placement(Vector(wall_thickness_mm, wall_thickness_mm, 0), FreeCAD.Rotation(0,0,0), Vector(0,0,0))
    inner_bottom_prism.Placement = FreeCAD.Placement(Vector(wall_thickness_mm, wall_thickness_mm, 0), FreeCAD.Rotation(0,0,0), Vector(0,0,0))
    # unite these two parts
    inner_corner = doc.addObject('Part::Fuse', brick_name + "_inner")
    inner_corner.Base = inner_left_prism
    inner_corner.Tool = inner_bottom_prism
    # now cut the inner part out of the outer part
    # hull = the cornerbrick without studs and without rings
    hull = doc.addObject('Part::Cut', brick_name + "_hull")
    hull.Base = outer_corner
    hull.Tool = inner_corner
    outer_left_prism.ViewObject.hide()
    outer_bottom_prism.ViewObject.hide()
    outer_corner.ViewObject.hide()
    inner_left_prism.ViewObject.hide()
    inner_bottom_prism.ViewObject.hide()
    inner_corner.ViewObject.hide()
    return hull



def make_corner_brick(left_length, left_width, bottom_lenght, bottom_height, plate_z):
    # name the brick
    brick_name = name_a_corner_brick(left_length, left_width, bottom_lenght, bottom_height, plate_z)
    # compound list will contain: the hull, the studs, the rings
    compound_list = []
    compound_list.append(create_corner_hull(brick_name))
    return
    compound_list += add_rectangular_brick_studs(brick_name)
    compound_list += add_rectangular_brick_rings(brick_name)
    # brick is finished, so create a compound object with the name of the brick
    obj = doc.addObject("Part::Compound", brick_name)
    obj.Links = compound_list
    # Put it next to the previous objects (instead of all at 0,0)
    global offset
    obj.Placement = FreeCAD.Placement(Vector((brick_width_mm * offset), 0, 0), FreeCAD.Rotation(0,0,0), Vector(0,0,0))
    offset += side_x + side_x + hole_x + 1
    #
    # clean up
    doc.removeObject("ring_template")
    doc.removeObject("outer_cylinder")
    doc.removeObject("inner_cylinder")
    # create mesh from shape (compound)
    doc.recompute()
    mesh = doc.addObject("Mesh::Feature","Mesh")
    part = doc.getObject(brick_name)
    shape = Part.getShape(part,"")
    mesh.Mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.1, AngularDeflection=0.0174533, Relative=False)
    mesh.Label = 'Mesh_' + brick_name
    # upload .stl file
    export = []
    export.append(doc.getObject(brick_name))
    Mesh.export(export, export_directory + brick_name + ".stl")
    

# corner resembles L
# L has left part |
# L has bottom part _
# the corner is shared by both parts
#make_corner_brick(length_left, width_left, length_bottom, height_bottom, plate_z)
make_corner_brick(6, 2, 3, 1, 3)

### Example: to create single bricks
### make_brick(width_in_studs, length_in_studs, height_in_plates)
#make_brick(2, 4, 3) # creates the common 2x4 brick
#make_brick(2, 6, 1) # creates a 2x6 plate
#make_brick(4, 4, 2) # creates a 4x4 plick

### Example: to create a series of bricks
### make_brick_series(width_in_studs, max_length_in_studs, heigth_in_plates)
### length starts at width
#make_brick_series(7, 9, 3) # create a 7x7, a 7x8, and a 7x9 brick
#make_brick_series(4, 8, 1) # creates five plates
#make_brick_series(12, 42, 3) # takes some time to compute so be patient or use smaller numbers

### Example: to create rectangle bricks
### Minimal size = 3 x 3 (a 1x1 hole with 1 stud on all sides)
### make_rectangle_brick(hole_x, hole_y, studs_x, studs_y, plate_z)
#make_rectangle_brick(1,1,1,1,1) # this is the smallest possible
#make_rectangle_brick(1,1,0,0,1) # seems to work, kinda pointless imho

doc.removeObject("stud_template")
doc.recompute()
FreeCADGui.ActiveDocument.ActiveView.fitAll()

