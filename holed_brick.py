"""
holed_brick.py -- Paul Cobbaut, 2023-05-17
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

# Dictionary of holed bricks generated; name:(side_x, side_y, hole_x, hole_y, plate_z)
holed_bricks = {}

# Used to visually separate the bricks in FreeCAD GUI
offset = 0

# The directory to export the .stl files to
export_directory = "/home/paul/FreeCAD/generated_bricks/"
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

# name a holed brick or plate
def name_a_holed_brick(side_x, side_y, hole_x, hole_y, plate_z):
    #
    # Name a holed brick, plick or plate using the number of studs
    # thickness: 1 = plate, 2 = plick, 3 = brick
    # name plate/plick/brick is followed by
    # - number of side studs X
    # - number of side studs Y
    # - hole_x
    # - hole_y
    # - thickness in plates Z
    #
    side_name = str(side_x) + 'x' + str(side_y)
    hole_name = '__hole_' + str(hole_x) + 'x' + str(hole_y)
    height_name = '__height_' + str(int(plate_z))
    if plate_z == 1:
    # plate
        name = 'holedplate_' + side_name + hole_name + height_name 
    elif plate_z == 2:
    # plick
        name = 'holedplick_' + side_name + hole_name + height_name 
    elif plate_z % 3 == 0:
    # brick (all multiples of 3 are bricks)
        if plate_z == 3:
            name = 'holedbrick_' + side_name + hole_name + height_name 
        elif plate_z == 6:
            name = 'holeddoublebrick_' + side_name + hole_name + height_name 
        elif plate_z == 9:
            name = 'holedtriplebrick_' + side_name + hole_name + height_name 
        elif plate_z == 12:
            name = 'holedquadruplebrick_' + side_name + hole_name + height_name 
        else:
            name = 'holedxbrick_' + side_name + hole_name + height_name 
    else:
        name = 'holedxplate_' + side_name + hole_name + height_name 
    holed_bricks[name] = (side_x, side_y, hole_x, hole_y, plate_z)
    return name


def create_holed_brick_hull(brick_name):
    # create the hull without studs and without rings
    # outer_prism = the completely filled block
    # inner_prism = makes hull (walls + ceiling) when subtracted outer_prism
    # outer_hole = the hole PLUS the walls around the hole
    # inner_hole = the hole (without the walls) ans subtracted from outer_hole
    side_x = holed_bricks[brick_name][0]
    side_y = holed_bricks[brick_name][1]
    hole_x = holed_bricks[brick_name][2]
    hole_y = holed_bricks[brick_name][3]
    z = holed_bricks[brick_name][4]
    studs_x = hole_x + (side_x * 2)
    studs_y = hole_y + (side_y * 2)
    # outer_prism = the brick block completely full
    outer_width  = convert_studs_to_mm(studs_x)
    outer_length = convert_studs_to_mm(studs_y)
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
    # solid = the solid part
    solid = doc.addObject('Part::Cut', brick_name + "_solid")
    solid.Base = outer_prism
    solid.Tool = inner_prism
    #outer_prism.ViewObject.hide()
    #inner_prism.ViewObject.hide()

    # outer_hole
    outer_hole_width  = convert_studs_to_mm(hole_x)
    outer_hole_length = convert_studs_to_mm(hole_y)
    outer_hole = make_box("outer_hole", outer_hole_width, outer_hole_length, outer_height)
    # place hole
    offset_x = convert_studs_to_mm(side_x) + gap_mm
    offset_y = convert_studs_to_mm(side_y) + gap_mm
    outer_hole.Placement = FreeCAD.Placement(Vector(offset_x, offset_y, 0), FreeCAD.Rotation(0,0,0), Vector(0,0,0))
    # cut hole out of solid
    holed_solid = doc.addObject('Part::Cut', brick_name + "_holed_solid")
    holed_solid.Base = solid
    holed_solid.Tool = outer_hole

    # inner_hole
    inner_hole_width  = outer_hole_width  - (2 * wall_thickness_mm)
    inner_hole_length = outer_hole_length - (2 * wall_thickness_mm)
    inner_hole  = make_box("inner_hole", inner_hole_width, inner_hole_length, outer_height) # no roof in hole
    # place the inner_prism at x and y exactly one wall thickness
    inner_hole_position = Vector(offset_x + wall_thickness_mm + gap_mm, offset_y + wall_thickness_mm + gap_mm, 0)
    inner_hole.Placement = FreeCAD.Placement(inner_hole_position, FreeCAD.Rotation(0,0,0), Vector(0,0,0))
    # now cut the inner hole out of the outer hole
    # hole_walls = the hole walls
    hole_walls = doc.addObject('Part::Cut', brick_name + "_holewalls")
    hole_walls.Base = outer_hole
    hole_walls.Tool = inner_hole
    #outer_hole.ViewObject.hide()
    #inner_hole.ViewObject.hide()

    # add hole_walls to solid
    hull = doc.addObject('Part::Fuse', brick_name + "_hull")
    hull.Base = holed_solid
    hull.Tool = hole_walls
    return hull


def add_holed_brick_studs(brick_name):
    # Add the studs on top
    # create the studs and append each one to a compound_list
    compound_list=[]
    # dimensions
    side_x = holed_bricks[brick_name][0]
    side_y = holed_bricks[brick_name][1]
    hole_x = holed_bricks[brick_name][2]
    hole_y = holed_bricks[brick_name][3]
    z = holed_bricks[brick_name][4]
    studs_x = hole_x + (side_x * 2)
    studs_y = hole_y + (side_y * 2)
    height = z * plate_height_mm
    for i in range(int(studs_x)):
        for j in range(int(studs_y)):
            if ( (i < side_x) or (i >= (side_x + hole_x)) ) or ( (j < side_y) or (j >= (side_y + hole_y)) ):
                stud = doc.addObject('Part::Feature','stud_template')
                stud.Shape = doc.stud_template.Shape
                stud.Label = "stud_" + brick_name + '_' + str(i) + '_' + str(j)
                xpos = ((i+1) * stud_center_spacing_mm) - (stud_center_spacing_mm / 2) - (gap_mm / 2)
                ypos = ((j+1) * stud_center_spacing_mm) - (stud_center_spacing_mm / 2) - (gap_mm / 2)
                stud.Placement = FreeCAD.Placement(Vector(xpos, ypos, height), FreeCAD.Rotation(0,0,0), Vector(0,0,0))
                compound_list.append(stud)
    return compound_list


def add_holed_brick_rings(brick_name):
    # Add the rings on the bottom of the brick
    compound_list = []
    side_x = holed_bricks[brick_name][0]
    side_y = holed_bricks[brick_name][1]
    hole_x = holed_bricks[brick_name][2]
    hole_y = holed_bricks[brick_name][3]
    z = holed_bricks[brick_name][4]
    studs_x = hole_x + (side_x * 2)
    studs_y = hole_y + (side_y * 2)
    height = z * plate_height_mm
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
    #ring_template.ViewObject.hide()
    # create the rings and append each one to the compound_list
    for i in range(int(studs_x - 1)):
        for j in range(int(studs_y - 1)):
            if ( (i < (side_x - 1)) or (i >= (side_x + hole_x)) ) or ( (j < (side_y - 1)) or (j >= (side_y + hole_y)) ):
                ring = doc.addObject('Part::Feature','ring_template') 
                ring.Shape = doc.ring_template.Shape 
                ring.Label = 'ring_' + brick_name + str(i) + '_' + str(j)
                xpos = (brick_width_mm + gap_mm) * (i + 1) - (gap_mm/2)
                ypos = (brick_width_mm + gap_mm) * (j + 1) - (gap_mm/2)
                ring.Placement = FreeCAD.Placement(Vector(xpos, ypos, 0), FreeCAD.Rotation(0,0,0), Vector(0,0,0))
                compound_list.append(ring)
    return compound_list


###
# Make a holed brick:
# hole_x	--> width of hole in studs
# hole_y	--> length of hole in studs
# side_x 	--> width of solid side in studs
# side_y 	--> length of solid side in studs
# plate_z 	--> height is in number of standard plate heights
#
# Examples:
# a 4x6 holed brick with a 2x2 hole has
# (hole_x = 2, hole_y = 2, side_x = 1, side_y = 3, plate_z = 3)
# studs_x is hole_x plus twice side_x
# studs_y is hole_y plus twice side_y
#
###
def make_holed_brick(hole_x, hole_y, side_x, side_y, plate_z):
    # name the brick
    brick_name = name_a_holed_brick(side_x, side_y, hole_x, hole_y, plate_z)
    # compound list will contain: the hull, the studs, the rings
    compound_list = []
    compound_list.append(create_holed_brick_hull(brick_name))
    compound_list += add_holed_brick_studs(brick_name)
    compound_list += add_holed_brick_rings(brick_name)
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
    export.append(mesh)
    Mesh.export(export, export_directory + brick_name + ".stl")
    #return obj

### Example: to create holed bricks
### Minimal size = 3 x 3 (a 1x1 hole with 1 stud on all sides)
### make_holed_brick(hole_x, hole_y, studs_x, studs_y, plate_z)
#make_holed_brick(1,1,1,1,1) # this is the smallest possible
#make_holed_brick(1,1,0,0,1) # seems to work, kinda pointless imho
#make_holed_brick(3,4,4,2,3) # total width = 3+2+2 (studs_x on both sides)
make_holed_brick(3,3,1,1,3)
make_holed_brick(4,3,2,2,1)
make_holed_brick(5,5,1,1,1)
make_holed_brick(1,6,2,2,3)
make_holed_brick(2,3,2,3,13)


doc.removeObject("stud_template")
doc.recompute()
FreeCADGui.ActiveDocument.ActiveView.fitAll()

