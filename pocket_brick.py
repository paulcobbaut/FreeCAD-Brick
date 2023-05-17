"""
pocket_brick.py -- Paul Cobbaut, 2023-05-16
The goal is to make Lego-compatible open boxes (pockets) for use in 3D printer
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

# The directory to export the .stl files to
export_directory = "/home/paul/FreeCAD/generated_pockets/"
#export_directory = "C:\" for Windows, not tested.


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

def name_a_pocket(studs_x, studs_y, inner_height, floor_height, inner_studs):
    floor_name = '_floor_' + str(floor_height)
    inner_name = '_inner_' + str(inner_height)
    size_name  = '_size_'  + str(studs_x) + 'x' + str(studs_y)
    if inner_studs:
        inner_name += '_inner_studs_'
    name       = 'pocket_' + size_name + inner_name + floor_name 
    return name

def create_pocket_hull(pocket_tuple):
    # create the hull without studs and without rings
    pocket_name = pocket_tuple[0]
    x = pocket_tuple[1]
    y = pocket_tuple[2]
    inner_height = pocket_tuple[3] * plate_height_mm
    floor_height = pocket_tuple[4] * plate_height_mm
    outer_height = floor_height + inner_height
    # outer_prism = the pocket block completely full
    outer_width  = convert_studs_to_mm(x)
    outer_length = convert_studs_to_mm(y)
    outer_prism = make_box("outer_prism", outer_width, outer_length, outer_height)
    # inner_prism = the part that is substracted from outer_prism, thus hull has walls and ceiling
    inner_width  = convert_studs_to_mm(x - 2)
    inner_length = convert_studs_to_mm(y - 2)
    inner_prism  = make_box("inner_prism", inner_width, inner_length, inner_height)
    # place the inner_prism at x and y exactly one stud thickness
    pocket_wall_mm = brick_width_mm + gap_mm
    inner_prism.Placement = FreeCAD.Placement(Vector(pocket_wall_mm, pocket_wall_mm, floor_height), FreeCAD.Rotation(0,0,0), Vector(0,0,0))
    # now cut the inner part out of the outer part
    # hull = the pocket without studs and without rings
    hull = doc.addObject('Part::Cut', pocket_name + "_hull")
    hull.Base = outer_prism
    hull.Tool = inner_prism
    outer_prism.ViewObject.hide()
    inner_prism.ViewObject.hide()
    return hull
    

def add_pocket_top_studs(pocket_tuple):
    # Add the studs on top
    # create the studs and append each one to a compound_list
    compound_list=[]
    pocket_name = pocket_tuple[0]
    studs_x = pocket_tuple[1]
    studs_y = pocket_tuple[2]
    hole_x = studs_x - 2       # pocket wall is one stud
    hole_y = studs_y - 2
    z = pocket_tuple[3] + pocket_tuple[4]
    height = z * plate_height_mm
    for i in range(int(studs_x)):
        for j in range(int(studs_y)):
            if ( (i < 1) or (i > hole_x) ) or ( (j < 1) or (j > hole_y) ):
                stud = doc.addObject('Part::Feature','stud_template')
                stud.Shape = doc.stud_template.Shape
                stud.Label = "stud_" + pocket_name + '_' + str(i) + '_' + str(j)
                xpos = ((i+1) * stud_center_spacing_mm) - (stud_center_spacing_mm / 2) - (gap_mm / 2)
                ypos = ((j+1) * stud_center_spacing_mm) - (stud_center_spacing_mm / 2) - (gap_mm / 2)
                stud.Placement = FreeCAD.Placement(Vector(xpos, ypos, height), FreeCAD.Rotation(0,0,0), Vector(0,0,0))
                compound_list.append(stud)
    return compound_list

def add_pocket_floor_studs(pocket_tuple):
    # Add the studs on the inside floor of the pocket
    # create the studs and append each one to a compound_list
    compound_list=[]
    pocket_name = pocket_tuple[0]
    x = pocket_tuple[1] - 2
    y = pocket_tuple[2] - 2
    z = pocket_tuple[4]
    height = z * plate_height_mm
    for i in range(int(x)):
        for j in range(int(y)):
            stud = doc.addObject('Part::Feature','stud_template')
            stud.Shape = doc.stud_template.Shape
            stud.Label = "stud_" + pocket_name + '_' + str(i) + '_' + str(j)
            xpos = ((i+2) * stud_center_spacing_mm) - (stud_center_spacing_mm / 2) - (gap_mm / 2)
            ypos = ((j+2) * stud_center_spacing_mm) - (stud_center_spacing_mm / 2) - (gap_mm / 2)
            stud.Placement = FreeCAD.Placement(Vector(xpos, ypos, height), FreeCAD.Rotation(0,0,0), Vector(0,0,0))
            compound_list.append(stud)
    return compound_list


def create_pocket(studs_x, studs_y, inner_height, floor_height, inner_studs):
    # name the brick
    pocket_name = name_a_pocket(studs_x, studs_y, inner_height, floor_height, inner_studs)
    pocket_tuple = ( pocket_name, studs_x, studs_y, inner_height, floor_height )
    # compound list will contain: the hull, the studs
    compound_list = []
    compound_list.append(create_pocket_hull(pocket_tuple))
    compound_list += add_pocket_top_studs(pocket_tuple)
    if inner_studs:
        compound_list += add_pocket_floor_studs(pocket_tuple)
    # brick is finished, so create a compound object with the name of the brick
    obj = doc.addObject("Part::Compound", pocket_name)
    obj.Links = compound_list
    # create mesh from shape (compound)
    doc.recompute()
    mesh = doc.addObject("Mesh::Feature","Mesh")
    part = doc.getObject(pocket_name)
    shape = Part.getShape(part,"")
    mesh.Mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.1, AngularDeflection=0.0174533, Relative=False)
    mesh.Label = 'Mesh_' + pocket_name
    # upload .stl file
    export = []
    export.append(doc.getObject(pocket_name))
    Mesh.export(export, export_directory + pocket_name + ".stl")
    obj.ViewObject.hide()
    #return obj
    

# studs_x = width of the open box
# studs_y = length of the open box
# inner_height = inner height of the box in number of (Lego) plates
# floor_height = height of the floor in (Lego) plates
# inner_studs_boolean = False if inner studs, False if inner flat floor
#create_pocket(studs_x, studs_y, inner_height, floor_height, inner_studs_boolean)
#create_pocket(8, 16, 6, 3, False)
create_pocket(10, 16, 9, 3, True)
create_pocket(10, 5, 6, 3, False)


doc.removeObject("stud_template")
doc.recompute()
FreeCADGui.ActiveDocument.ActiveView.fitAll()

