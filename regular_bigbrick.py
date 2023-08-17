"""
regular_bigbrick.py -- Paul Cobbaut, 2023-06-01 - 2023-08-16
The goal is to make Duplo-compatible bricks for use in 3D printer
The script generates .stl files in a directory.
"""
# Dimensions for stud rings
# These are the studs on top of the Duplo-compatible bigbrick
studring_radius_mm	= 4.800		# Was 4.950 before 2023-08-10, Duplo official is 4.800
studring_height_mm	= 4.400		# Was 3.400 before 2023-08-10, Duplo official is 3.200
studring_wall_mm	= 1.200		# Was 2.000 before 2023-08-10
studring_center_spacing_mm	= 16.000

# Dimensions for bigbricks
bigplate_height_mm	= 9.600
bigbrick_height_mm	= 19.200	# bigplate_height_mm * 2
bigbrick_width_mm	= 15.800	# ???

# The gap that is added to the width/length for each extra stud
gap_mm 			= 0.200

# Wall thickness for bricks and plates
bigwall_thickness_mm	= 3.000
bigtop_thickness_mm     = 2.000		# the 'ceiling' of a brick is thinner than the sides

# Dimensions underside rings
# These are the cylinders center on the underside of bigbricks
ring_radius_outer_mm	= 6.700     # was 6.500 before 2023-08-10
ring_radius_inner_mm	= 5.400     # was 5.000 before 2023-08-10

# Dimensions for underside cones
# These enable 3D printing of the bigbrick 'ceiling' without supports
cone_smallradius_mm     = 6.000
cone_bigradius_mm       = 14.000
cone_height_mm          = 9.000

# Dictionary of bricks generated; name:(studs_x, studs_y, plate_z) --> (width, length, height)
bigbricks = {}

# Used to visually separate the bricks in FreeCAD GUI
offset = 0

# The directory to export the .stl files to
export_directory = "/home/paul/FreeCAD_generated/"

# font used for the text strings
font_file="/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"

import FreeCAD
from FreeCAD import Base, Vector
import Part
import Sketcher
import Mesh
import MeshPart
import Draft
import math

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
    mm = (studs * bigbrick_width_mm) + ((studs - 1) * gap_mm)
    return mm


# the studring template is created once then always copied
def make_studring_template(name):
    # outer cylinder
    outer = doc.addObject("Part::Cylinder", "outer_studring_template")
    outer.Radius = studring_radius_mm
    outer.Height = studring_height_mm
    # inner cylinder
    inner = doc.addObject("Part::Cylinder", "inner_studring_template")
    inner.Radius = studring_radius_mm - studring_wall_mm
    inner.Height = studring_height_mm
    # cut inner cylinder out of outer cylinder = ring
    studring = doc.addObject('Part::Cut', "studring")
    studring.Base = outer
    studring.Tool = inner
    # fillet the top edges
    fillet = doc.addObject("Part::Fillet",name)
    fillet.Base = studring
    edges = []
    edges.append((3,0.35,0.35))
    edges.append((5,0.35,0.35))
    fillet.Edges = edges
    ## Note that edges 3 and 5 were discoverd from GUI. There is little guarantee this will work in the future.
    doc.recompute()
    return fillet


def make_cone_template(name):
    # sketch for bottom circle
    Sketch_bc = doc.getObject('Body').newObject('Sketcher::SketchObject', 'Sketch_bc')
    Sketch_bc.Support = [(doc.getObject('XY_Plane'),'')]
    #Sketch_bc.Placement = FreeCAD.Placement(Vector(0,0,0),FreeCAD.Rotation(Vector(0,0,0),0))
    doc.getObject('Sketch_bc').addGeometry(Part.Circle(App.Vector(0,0,0),App.Vector(0,0,1),cone_smallradius_mm),False)
    # sketch for top circle
    Sketch_tc = doc.getObject('Body').newObject('Sketcher::SketchObject', 'Sketch_tc')
    Sketch_tc.Support = [(doc.getObject('XY_Plane'),'')]
    Sketch_tc.Placement = FreeCAD.Placement(Vector(0,0,cone_height_mm),FreeCAD.Rotation(Vector(0,0,0),0))
    doc.getObject('Sketch_tc').addGeometry(Part.Circle(App.Vector(0,0,0),App.Vector(0,0,1),cone_bigradius_mm),False)
    # loft both circles
    Loft = doc.getObject('Body').newObject('PartDesign::AdditiveLoft','Loft')
    Loft.Profile = doc.getObject('Sketch_bc')
    Loft.Sections = [ doc.getObject('Sketch_tc'),  ]
    doc.recompute()
    # simple copy
    obj = doc.addObject('Part::Feature',name)
    obj.Shape = Loft.Shape
    obj.Label = name
    return obj


def name_a_bigbrick(studs_x, studs_y, plate_z):
    # TODO
    # Name a brick, plick or plate using the number of studs
    # thickness: 1 = plate, 2 = plick, 3 = brick
    # name plate/plick/brick is followed by
    # - number of studs X
    # - number of studs Y
    # - thickness in plates Z
    #
    if plate_z == 1:
    # plate
        name = 'plate_' + str(studs_x) + 'x' + str(studs_y) + 'x' + str(int(plate_z))
    elif plate_z == 2:
    # plick
        name = 'plick_' + str(studs_x) + 'x' + str(studs_y) + 'x' + str(int(plate_z))
    elif plate_z % 3 == 0:
    # brick (all multiples of 3 are bricks)
        if plate_z == 3:
            name = 'brick_' + str(studs_x) + 'x' + str(studs_y) + 'x' + str(int(plate_z))
        elif plate_z == 6:
            name = 'doublebrick_' + str(studs_x) + 'x' + str(studs_y) + 'x' + str(int(plate_z))
        elif plate_z == 9:
            name = 'triplebrick_' + str(studs_x) + 'x' + str(studs_y) + 'x' + str(int(plate_z))
        elif plate_z == 12:
            name = 'quadruplebrick_' + str(studs_x) + 'x' + str(studs_y) + 'x' + str(int(plate_z))
        else:
            name = 'xbrick_' + str(studs_x) + 'x' + str(studs_y) + 'x' + str(int(plate_z))
    else:
        name = 'xplate_' + str(studs_x) + 'x' + str(studs_y) + 'x' + str(plate_z)
    bigbricks[name] = (studs_x, studs_y, plate_z)
    return name


def create_brick_hull(brick_name):
    # create the hull without studs and without rings
    x = bigbricks[brick_name][0]
    y = bigbricks[brick_name][1]
    z = bigbricks[brick_name][2]
    # outer_prism = the brick block completely full
    outer_width  = convert_studs_to_mm(x)
    outer_length = convert_studs_to_mm(y)
    outer_height = z * bigplate_height_mm
    outer_prism = make_box("outer_prism", outer_width, outer_length, outer_height)
    # inner_prism = the part that is substracted from outer_prism, thus hull has walls and ceiling
    inner_width  = outer_width  - (2 * bigwall_thickness_mm)
    inner_length = outer_length - (2 * bigwall_thickness_mm)
    inner_height = outer_height - bigtop_thickness_mm		# because - wall_thickness_mm was too much
    inner_prism  = make_box("inner_prism", inner_width, inner_length, inner_height)
    # place the inner_prism at x and y exactly one wall thickness
    inner_prism.Placement = FreeCAD.Placement(Vector(bigwall_thickness_mm, bigwall_thickness_mm, 0), FreeCAD.Rotation(0,0,0), Vector(0,0,0))
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
    x = bigbricks[brick_name][0]
    y = bigbricks[brick_name][1]
    z = bigbricks[brick_name][2]
    height = z * bigplate_height_mm
    for i in range(int(x)):
        for j in range(int(y)):
            stud = doc.addObject('Part::Feature','studring_template')
            stud.Shape = doc.studring_template.Shape
            stud.Label = "stud_" + brick_name + '_' + str(i) + '_' + str(j)
            xpos = ((i+1) * studring_center_spacing_mm) - (studring_center_spacing_mm / 2) - (gap_mm / 2)
            ypos = ((j+1) * studring_center_spacing_mm) - (studring_center_spacing_mm / 2) - (gap_mm / 2)
            stud.Placement = FreeCAD.Placement(Vector(xpos, ypos, height), FreeCAD.Rotation(0,0,0), Vector(0,0,0))
            compound_list.append(stud)
    return compound_list


def add_brick_cones(brick_name):
    # Add the cones below the 'ceiling' of the bigbrick
    # the sole purpose of this is easier 3D printing
    # create the cones and append each one to a compound_list
    compound_list=[]
    x = bigbricks[brick_name][0]
    y = bigbricks[brick_name][1]
    z = bigbricks[brick_name][2]
    height = z * bigplate_height_mm - 9 - bigtop_thickness_mm
    for i in range(int(x - 1)):
        for j in range(int(y - 1)):
            stud = doc.addObject('Part::Feature','cone_template')
            stud.Shape = doc.cone_template.Shape
            stud.Label = "cone_" + brick_name + '_' + str(i) + '_' + str(j)
            xpos = (bigbrick_width_mm + gap_mm) * (i + 1) - (gap_mm/2)
            ypos = (bigbrick_width_mm + gap_mm) * (j + 1) - (gap_mm/2)
            stud.Placement = FreeCAD.Placement(Vector(xpos, ypos, height), FreeCAD.Rotation(0,0,0), Vector(0,0,0))
            compound_list.append(stud)
    return compound_list


def add_brick_rings(brick_name):
    # Add the rings on the bottom of the brick
    compound_list = []
    x = bigbricks[brick_name][0]
    y = bigbricks[brick_name][1]
    z = bigbricks[brick_name][2]
    # Create a template ring (all rings for a single brick are the same height)
    height = z * bigplate_height_mm
    outer_cylinder = doc.addObject("Part::Cylinder", "outer_cylinder")
    outer_cylinder.Radius = ring_radius_outer_mm
    outer_cylinder.Height = height - bigtop_thickness_mm
    inner_cylinder = doc.addObject("Part::Cylinder", "inner_cylinder")
    inner_cylinder.Radius = ring_radius_inner_mm
    inner_cylinder.Height = height - bigtop_thickness_mm
    ring_template = doc.addObject('Part::Cut', 'ring_template')
    ring_template.Base = outer_cylinder
    ring_template.Tool = inner_cylinder
    doc.recompute()
    #ring_template.ViewObject.hide()
    # create the rings and append each one to the compound_list
    for i in range(int(x - 1)):
        for j in range(int(y - 1)):
            ring = doc.addObject('Part::Feature','ring_template') 
            ring.Shape = doc.ring_template.Shape 
            ring.Label = 'ring_' + brick_name + str(i) + '_' + str(j)
            xpos = (bigbrick_width_mm + gap_mm) * (i + 1) - (gap_mm/2)
            ypos = (bigbrick_width_mm + gap_mm) * (j + 1) - (gap_mm/2)
            ring.Placement = FreeCAD.Placement(Vector(xpos, ypos, 0), FreeCAD.Rotation(0,0,0), Vector(0,0,0))
            compound_list.append(ring)
    # clean up
    doc.removeObject("ring_template")
    doc.removeObject("outer_cylinder")
    doc.removeObject("inner_cylinder")
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
def make_bigbrick(studs_x, studs_y, plate_z):
    # Exit if studs_y is smaller than studs_x
    if studs_y < studs_x:
        print('ERROR: make_brick(): studs_y (', studs_y, ') cannot be smaller than studs_x (', studs_x, ')')
        return
    # name the bigbrick
    brick_name = name_a_bigbrick(studs_x, studs_y, plate_z)
    # compound list will contain: the hull, the studs, the cones, the rings
    compound_list = []
    compound_list.append(create_brick_hull(brick_name))
    compound_list += add_brick_studs(brick_name)
    compound_list += add_brick_cones(brick_name)
    compound_list += add_brick_rings(brick_name)
    # bigbrick is finished, so create a compound object with the name of the bigbrick
    obj = doc.addObject("Part::Compound", brick_name)
    obj.Links = compound_list
    # Put it next to the previous objects (instead of all at 0,0)
    global offset
    obj.Placement = FreeCAD.Placement(Vector((bigbrick_width_mm * offset), 0, 0), FreeCAD.Rotation(0,0,0), Vector(0,0,0))
    offset += studs_x + 1
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


def make_string(stringtext):
  newstring=Draft.make_shapestring(String=stringtext, FontFile=font_file, Size=7.0, Tracking=0.0)
  plm=FreeCAD.Placement() 
  plm.Base=FreeCAD.Vector(0, 0, 0)
  plm.Rotation.Q=(0.5, -0.5, -0.5, 0.5)
  newstring.Placement=plm
  newstring.Support=None
  Draft.autogroup(newstring)
  return newstring


#########
# Start #
#########

# create a FreeCAD document and Part Design body
doc = FreeCAD.newDocument("Bigbrick generated")
obj = doc.addObject("PartDesign::Body", "Body")

# creating the studring template and cone template
studring_template = make_studring_template("studring_template")
cone_template = make_cone_template("cone_template")

### make_brick(width_in_studs, length_in_studs, height_in_plates)
#make_brick(2, 4, 3) # creates the common 2x4 brick

mystring = make_string("Test42")
string_width = float(mystring.Shape.BoundBox.YLength)
studs_needed = int(math.ceil((string_width-8)/16) + 1)
brick_width = convert_studs_to_mm(studs_needed)

difference = brick_width - string_width

print("string_width = " + str(string_width))
print("studs_needed = " + str(studs_needed))
print("brick_width  = " + str(brick_width))
print("Difference   = " + str(difference))

make_bigbrick(2, studs_needed, 2)

plm=FreeCAD.Placement()
plm.Base=FreeCAD.Vector(-2.0, brick_width - difference/2 + 1.56418, 2.40)
plm.Rotation.Q=(0.5, -0.5, -0.5, 0.5)
mystring.Placement=plm


# removing templates
doc.removeObject("studring_template")
doc.removeObject("studring")
doc.removeObject("outer_studring_template")
doc.removeObject("inner_studring_template")
doc.removeObject("cone_template")
doc.removeObject("Loft")
doc.removeObject("Sketch_bc")
doc.removeObject("Sketch_tc")

# show in GUI`
doc.recompute()
FreeCADGui.ActiveDocument.ActiveView.fitAll()

