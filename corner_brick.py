"""
corner_brick.py -- Paul Cobbaut, 2023-05-17
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
    height_name = '_height_' + str(plate_z)
    name         = 'cornerbrick' + left_name + bottom_name + height_name
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
    # fuse these two parts
    outer_corner = doc.addObject('Part::Fuse', brick_name + "_outer")
    outer_corner.Base = outer_left_prism
    outer_corner.Tool = outer_bottom_prism
    # create the inner cutout for both parts and fuse them
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


def add_corner_brick_studs(brick_name):
    # Add the studs on top
    # create the studs and append each one to a compound_list
    left_l   = bricks[brick_name][0]
    left_w   = bricks[brick_name][1]
    bottom_l = bricks[brick_name][2]
    bottom_h = bricks[brick_name][3]
    z        = bricks[brick_name][4]
    height   = z * plate_height_mm
    compound_list=[]
    for i in range(int(bottom_l + left_w)):
        for j in range(int(left_l)):
            if ((i < left_w) or (j < bottom_h)):
                stud = doc.addObject('Part::Feature','stud_template')
                stud.Shape = doc.stud_template.Shape
                stud.Label = "stud_" + brick_name + '_' + str(i) + '_' + str(j)
                xpos = ((i+1) * stud_center_spacing_mm) - (stud_center_spacing_mm / 2) - (gap_mm / 2)
                ypos = ((j+1) * stud_center_spacing_mm) - (stud_center_spacing_mm / 2) - (gap_mm / 2)
                stud.Placement = FreeCAD.Placement(Vector(xpos, ypos, height), FreeCAD.Rotation(0,0,0), Vector(0,0,0))
                compound_list.append(stud)
    return compound_list


def add_corner_brick_rings(brick_name):
    # Add the rings on the bottom of the brick
    compound_list = []
    left_l   = bricks[brick_name][0]
    left_w   = bricks[brick_name][1]
    bottom_l = bricks[brick_name][2]
    bottom_h = bricks[brick_name][3]
    z        = bricks[brick_name][4]
    height   = z * plate_height_mm
    # Create a template ring (all rings for a single brick are the same height)
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
    # create the rings and append each one to the compound_list
    for i in range(int(bottom_l + left_w - 1)):
        for j in range(int(left_l - 1)):
            if ((i < (left_w - 1)) or (j < (bottom_h - 1))):
                ring = doc.addObject('Part::Feature','ring_template') 
                ring.Shape = doc.ring_template.Shape 
                ring.Label = 'ring_' + brick_name + str(i) + '_' + str(j)
                xpos = (brick_width_mm + gap_mm) * (i + 1) - (gap_mm/2)
                ypos = (brick_width_mm + gap_mm) * (j + 1) - (gap_mm/2)
                ring.Placement = FreeCAD.Placement(Vector(xpos, ypos, 0), FreeCAD.Rotation(0,0,0), Vector(0,0,0))
                compound_list.append(ring)
    # clean up
    ring_template.ViewObject.hide()
    doc.removeObject("ring_template")
    doc.removeObject("outer_cylinder")
    doc.removeObject("inner_cylinder")
    return compound_list


def make_corner_brick(left_length, left_width, bottom_length, bottom_height, plate_z):
    # name the brick
    brick_name = name_a_corner_brick(left_length, left_width, bottom_length, bottom_height, plate_z)
    # compound list will contain: the hull, the studs, the rings
    compound_list = []
    compound_list.append(create_corner_hull(brick_name))
    compound_list += add_corner_brick_studs(brick_name)
    compound_list += add_corner_brick_rings(brick_name)
    # brick is finished, so create a compound object with the name of the brick
    obj = doc.addObject("Part::Compound", brick_name)
    obj.Links = compound_list
    # Put it next to the previous objects (instead of all at 0,0)
    global offset
    obj.Placement = FreeCAD.Placement(Vector((brick_width_mm * offset), 0, 0), FreeCAD.Rotation(0,0,0), Vector(0,0,0))
    offset += left_width + bottom_length + 1
    # create mesh from shape (compound)
    doc.recompute()
    mesh = doc.addObject("Mesh::Feature","Mesh")
    part = doc.getObject(brick_name)
    shape = Part.getShape(part,"")
    mesh.Mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.1, AngularDeflection=0.0174533, Relative=False)
    mesh.Label = 'Mesh_' + brick_name
    # upload .stl file
    export = []
    export.append(mesh)
    Mesh.export(export, export_directory + brick_name + ".stl")
    # return mesh    


# corner resembles L
# L has left part |
# L has bottom part _
# the corner is part of the left |
#make_corner_brick(length_left, width_left, length_bottom, height_bottom, plate_z)
make_corner_brick(9, 1, 4, 1, 1)
make_corner_brick(3, 1, 2, 2, 1)
make_corner_brick(10, 4, 4, 2, 3)
make_corner_brick(12, 2, 4, 4, 3)
make_corner_brick(8, 2, 6, 2, 6)


doc.removeObject("stud_template")
doc.recompute()
FreeCADGui.ActiveDocument.ActiveView.fitAll()

