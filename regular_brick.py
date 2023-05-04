"""
regular_brick.py -- Paul Cobbaut, 2022-09-30
updates 2023-05-04
The goal is to make Lego-compatible pieces for use in 3D printer
The script is able to generate .stl files directly.
"""
# Dimensions for studs
stud_radius_mm		= 2.475		# was 2.475 on 20221001
stud_center_spacing_mm	= 8.000
stud_height_mm		= 1.700		# official 1.600

# Dimensions for plates
plate_height_mm		= 3.200
plate_width_mm		= 7.800

# The gap that is added to the width/lenght for each extra stud
gap_mm 			= 0.200

# Dimensions for bricks
brick_height_mm		= 9.600		# plate_height_mm * 3
brick_width_mm		= 7.800		# = plate_width_mm

# Wall thickness for bricks and plates
wall_thickness_mm	= 1.500		# 1.2 and 0.3 for new small beams or 1.5 for old bricks
top_thickness_mm	= 1.000		# was 1.600 on 20220930

# Dimensions underside rings
ring_radius_outer_mm	= 3.250 	# was 3.220 on 1028, 3.226 on 20220929 (should be 3.25??)
ring_radius_inner_mm	= 2.500		# was 2.666 pm 1029, 2.456 on 20220930, 2.556 on 20221001 (should be 2.4???)

# Dictionary of bricks generated; name:(studs_x, studs_y, plate_z) --> (width, length, height)
bricks = {}

# Used to visually separate the bricks in FreeCAD GUI
offset = 0

import FreeCAD
from FreeCAD import Base, Vector
import Part
import Sketcher
import Mesh
import MeshPart

# FreeCAD document
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

# name a brick or plate
def name_a_brick(studs_x, studs_y, plate_z):
    #
    # Name a brick, plick or plate using the number of studs
    # thickness: 1 = plate, 2 = plick, 3 = brick
    #
    if plate_z == 1:
    # plate
        name = 'plate_' + str(studs_x) + 'x' + str(studs_y) + 'x' + str(int(plate_z))
    elif plate_z == 2:
    # plick
        name = 'plick_' + str(studs_x) + 'x' + str(studs_y) + 'x' + str(int(plate_z/2))
    elif plate_z % 3 == 0:
    # brick (all multiples of 3 are bricks)
        if plate_z == 3:
            name = 'brick_' + str(studs_x) + 'x' + str(studs_y) + 'x' + str(int(plate_z/3))
        elif plate_z == 6:
            name = 'doublebrick_' + str(studs_x) + 'x' + str(studs_y) + 'x' + str(int(plate_z/3))
        elif plate_z == 9:
            name = 'triplebrick_' + str(studs_x) + 'x' + str(studs_y) + 'x' + str(int(plate_z/3))
        elif plate_z == 12:
            name = 'quadruplebrick_' + str(studs_x) + 'x' + str(studs_y) + 'x' + str(int(plate_z/3))
        else:
            name = 'xbrick_' + str(studs_x) + 'x' + str(studs_y) + 'x' + str(int(plate_z/3))
    else:
        name = 'xplate_' + str(studs_x) + 'x' + str(studs_y) + 'x' + str(plate_z)
    bricks[name] = (studs_x, studs_y, plate_z)
    return name

def create_brick_hull(brick_name):
    # create the hull without studs and without rings
    x = bricks[brick_name][0]
    y = bricks[brick_name][1]
    z = bricks[brick_name][2]
    # outer_prism = the brick block completely full
    outer_width  = convert_studs_to_mm(x)
    outer_length = convert_studs_to_mm(y)
    outer_height = z * plate_height_mm
    outer_prism = make_box("outer_prism", outer_width, outer_length, outer_height)
    # inner_prism = the part that is substracted from outer_prism, thus hull has walls and ceiling
    inner_width  = outer_width  - (2 * wall_thickness_mm)
    inner_length = outer_length - (2 * wall_thickness_mm)
    inner_height = outer_height - top_thickness_mm		# because - wall_thickness_mm was too much
    inner_prism  = make_box("inner_prism", inner_width, inner_length, inner_height)
    # place the inner_prism at x and y exactly one wall thickness
    inner_prism.Placement = FreeCAD.Placement(Vector(wall_thickness_mm, wall_thickness_mm, 0), FreeCAD.Rotation(0,0,0), Vector(0,0,0))
    # now cut the inner part out of the outer part
    # hull = the brick/plate without studs and without rings
    hull = doc.addObject('Part::Cut', brick_name + "_hull")
    hull.Base = outer_prism
    hull.Tool = inner_prism
    outer_prism.ViewObject.hide()
    inner_prism.ViewObject.hide()
    return hull

def add_brick_studs(brick_name):
    # Add the studs on top
    # create the studs and append each one to a compound_list
    compound_list=[]
    x = bricks[brick_name][0]
    y = bricks[brick_name][1]
    z = bricks[brick_name][2]
    height = z * plate_height_mm
    for i in range(int(x)):
        for j in range(int(y)):
            stud = doc.addObject('Part::Feature','stud_template')
            stud.Shape = doc.stud_template.Shape
            stud.Label = "stud_" + brick_name + '_' + str(i) + '_' + str(j)
            xpos = ((i+1) * stud_center_spacing_mm) - (stud_center_spacing_mm / 2) - 0.1 # wth is -0.1?
            ypos = ((j+1) * stud_center_spacing_mm) - (stud_center_spacing_mm / 2) - 0.1
            stud.Placement = FreeCAD.Placement(Vector(xpos, ypos, height), FreeCAD.Rotation(0,0,0), Vector(0,0,0))
            compound_list.append(stud)
    return compound_list

def add_brick_rings(brick_name):
    # Add the rings on the bottom of the brick
    compound_list = []
    x = bricks[brick_name][0]
    y = bricks[brick_name][1]
    z = bricks[brick_name][2]
    # Create a template ring
    height = z * plate_height_mm
    outer_cylinder = doc.addObject("Part::Cylinder", "outer_cylinder")
    outer_cylinder.Radius = ring_radius_outer_mm
    outer_cylinder.Height = height - top_thickness_mm
    inner_cylinder = doc.addObject("Part::Cylinder", "inner_cylinder")
    inner_cylinder.Radius = ring_radius_inner_mm
    inner_cylinder.Height = height - top_thickness_mm
    ring_template = doc.addObject('Part::Cut', 'ring_template')
    ring_template.Base = outer_cylinder
    ring_template.Tool = inner_cylinder
    doc.recompute()
    ring_template.ViewObject.hide()
    # create the rings and append each one to the compound_list
    for j in range(int(x - 1)):		### TODO only place outer ring when using holes??
        for i in range(int(y - 1)):
            ring = doc.addObject('Part::Feature','ring_template') 
            ring.Shape = doc.ring_template.Shape 
            ring.Label = 'ring_' + brick_name + str(i) + '_' + str(j)
            xpos = (brick_width_mm + gap_mm) * (j + 1) - (gap_mm/2)
            ypos = (brick_width_mm + gap_mm) * (i + 1) - (gap_mm/2)
            ring.Placement = FreeCAD.Placement(Vector(xpos, ypos, 0), FreeCAD.Rotation(0,0,0), Vector(0,0,0))
            compound_list.append(ring)
    return compound_list

###
# Make a brick:
# studs_x 	--> width is in number of studs
# studs_y 	--> length is in number of studs
# plate_z 	--> height is in number of standard plate heights
#
# Examples:
# a standard 2x4 plate has (2, 4, 1) as parameters
# a standard 2x4 brick has (2 ,4, 3) as parameters
# a very long 1x16 plate has (1, 16, 1) as parameters
# a very wide 8x12 plick has (8, 12, 2) as parameters
#
# Important note:
# studs_y >= studs_x 
# a 4x2 brick does not exist!
# always put the smallest digit first!
###
def make_brick(studs_x, studs_y, plate_z):
    # Exit if studs_y is smaller than studs_x
    if studs_y < studs_x:
        print('ERROR: make_brick(): studs_y (', studs_y, ') cannot be smaller than studs_x (', studs_x, ')')
        return
    # name the brick
    brick_name = name_a_brick(studs_x, studs_y, plate_z)
    # compound list will contain: the hull, the studs, the rings
    compound_list = []
    compound_list.append(create_brick_hull(brick_name))
    compound_list += add_brick_studs(brick_name)
    compound_list += add_brick_rings(brick_name)
    # brick is finished, so create a compound object with the name of the brick
    obj = doc.addObject("Part::Compound", brick_name)
    obj.Links = compound_list
    # Put it next to the previous objects (instead of all at 0,0)
    global offset
    obj.Placement = FreeCAD.Placement(Vector((brick_width_mm * offset), 0, 0), FreeCAD.Rotation(0,0,0), Vector(0,0,0))
    offset += studs_x + 1
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
    Mesh.export(export, u"/home/paul/FreeCAD/generated_bricks/" + brick_name + ".stl")
    #return obj

def make_brick_series(studs_x, studs_y_max, plate_z):
    offset = 0
    for i in range(int(studs_x), int(studs_y_max) + 1):
        brick = make_brick(studs_x, i, plate_z)
        offset = offset + int(studs_x) + 1

### Example: to create single bricks
#make_brick(2, 4, 1)
#make_brick(2, 4, 2)

### Example: to create a series of bricks
make_brick_series(2, 10, 3)
#make_brick_series(4, 6, 1)

doc.removeObject("stud_template")
doc.recompute()
FreeCADGui.ActiveDocument.ActiveView.fitAll()
