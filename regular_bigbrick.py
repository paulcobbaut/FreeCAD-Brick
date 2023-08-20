"""
regular_bigbrick.py -- Paul Cobbaut, 2023-06-01 - 2023-08-18
The goal is Duplo-compatible bricks with text for use in 3D printer
The script generates .stl files in a directory.
"""
# Dimensions for stud rings
# These are the studs on top of the Duplo-compatible bigbrick
studring_radius_mm	    = 4.800
studring_height_mm	    = 4.400
studring_wall_mm	    = 1.200
studring_center_spacing_mm	= 16.000

# Dimensions for bigbricks
bigplate_height_mm	    = 9.600
bigbrick_height_mm	    = 19.200	# bigplate_height_mm * 2
bigbrick_width_mm	    = 15.800

# The gap that is added to the width/length for each extra stud
gap_mm 			        = 0.200

# Wall thickness for bricks and plates
bigwall_thickness_mm	= 3.000
bigtop_thickness_mm     = 2.000		# the 'ceiling' of a brick is thinner than the sides

# Dimensions underside rings
# These are the cylinders center on the underside of bigbricks
ring_radius_outer_mm	= 6.700
ring_radius_inner_mm	= 5.400

# Dimensions for underside cones
# These enable 3D printing of the bigbrick 'ceiling' without supports
cone_smallradius_mm     = 6.000
cone_bigradius_mm       = 14.000
cone_height_mm          = 9.000

# Dictionary of bricks generated; name:(studs_x, studs_y, plate_z) --> (width, length, height)
bigbricks = {}

# The directory to export the .stl files to
export_directory = "/home/paul/FreeCAD_generated/"

# font used for the text strings
# S does not chamfer in this FreeSansBold font
font_file="/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" 
#font_file="/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf"
#font_file="/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf"

# text to put on bigbrick
text_string = "ABC"

import FreeCAD
from FreeCAD import Base, Vector
import Part
import PartDesign
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
    sketch_bc = doc.getObject('Body').newObject('Sketcher::SketchObject', 'sketch_bc')
    sketch_bc.Support = [(doc.getObject('XY_Plane'),'')]
    doc.getObject('sketch_bc').addGeometry(Part.Circle(App.Vector(0,0,0),App.Vector(0,0,1),cone_smallradius_mm),False)
    # sketch for top circle
    sketch_tc = doc.getObject('Body').newObject('Sketcher::SketchObject', 'sketch_tc')
    sketch_tc.Support = [(doc.getObject('XY_Plane'),'')]
    sketch_tc.Placement = FreeCAD.Placement(Vector(0,0,cone_height_mm),FreeCAD.Rotation(Vector(0,0,0),0))
    doc.getObject('sketch_tc').addGeometry(Part.Circle(App.Vector(0,0,0),App.Vector(0,0,1),cone_bigradius_mm),False)
    # loft both circles
    loft = doc.getObject('Body').newObject('PartDesign::AdditiveLoft','loft')
    loft.Profile = doc.getObject('sketch_bc') 
    loft.Sections = [ doc.getObject('sketch_tc'),  ]
    doc.recompute()
    # simple copy
    cone = doc.addObject('Part::Feature',name)
    cone.Shape = loft.Shape
    cone.Label = name
    return cone


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


def create_mesh_and_export(string_text, compound_list):
    obj = doc.addObject("Part::Compound", "CompoundAll")
    obj.Links = compound_list
    doc.recompute()
    # create mesh from shape (compound)
    mesh = doc.addObject("Mesh::Feature","Mesh-" + string_text)
    part = doc.getObject("CompoundAll")
    shape = Part.getShape(part,"")
    mesh.Mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=1, AngularDeflection=0.1, Relative=False)
    mesh.Label = 'Mesh-' + string_text
    # upload .stl file
    export = []
    export.append(mesh)
    Mesh.export(export, export_directory + string_text + ".stl")
    #return obj


def create_brick_text(text_string):
    # create a shapestring of the received string
    newstring=Draft.make_shapestring(String=text_string, FontFile=font_file, Size=7.0, Tracking=0.0)
    plm=FreeCAD.Placement() 
    plm.Base=FreeCAD.Vector(0, 0, 0)
    plm.Rotation.Q=(0.5, -0.5, -0.5, 0.5)
    newstring.Placement=plm
    newstring.Support=None
    Draft.autogroup(newstring)
    # determine the bigbrick needed for this shapestring
    string_width = float(newstring.Shape.BoundBox.YLength)
    studs_needed = int(math.ceil((string_width-8)/16) + 1)
    # add bigbrick to global list
    bigbricks[text_string] = (2, studs_needed, 2)
    # position the string in front of a Duplo-compatible brick
    brick_width = convert_studs_to_mm(studs_needed)
    difference = brick_width - string_width
    string_offset_y = brick_width - difference/2 + 1.56418 # gap for this font&size
    plm=FreeCAD.Placement()
    plm.Base=FreeCAD.Vector(0, string_offset_y, 2.40)
    plm.Rotation.Q=(0.5, -0.5, -0.5, 0.5)
    newstring.Placement=plm
    # pad the shapestring
    Extrude = doc.addObject('Part::Extrusion','Extrude')
    f = doc.getObject('Extrude')
    f.Base = newstring
    f.DirMode = "Normal"
    f.DirLink = None
    f.LengthFwd = 0.30
    f.LengthRev = 0
    f.Solid = False
    f.Reversed = False
    f.Symmetric = False
    f.TaperAngle = 0
    f.TaperAngleRev = 0
    doc.recompute()
    # build list of edges to chamfer
    chamferlist = []
    i = 1
    for edge in doc.Extrude.Shape.Edges:
        p1 = edge.Vertexes[0]
        p2 = edge.Vertexes[1]
        if (p1.X == -0.3):
          chamferlist.append((i,0.29,0.29))
        i = i + 1
    # chamfer the letters
    Chamfer = doc.addObject("Part::Chamfer","Chamfer")
    Chamfer.Base = Extrude
    FreeCAD.ActiveDocument.Chamfer.Edges = chamferlist
    # hide objects
    Extrude.ViewObject.hide()
    newstring.ViewObject.hide()
    return Chamfer


#########
# Start #
#########

# create a FreeCAD document and Part Design body
doc                 = FreeCAD.newDocument("Bigbrick generated")
body                = doc.addObject("PartDesign::Body", "Body")
# creating the studring template and cone template
studring_template   = make_studring_template("studring_template")
cone_template       = make_cone_template("cone_template")
# create all parts of the bigbrick and add them to a list
compound_list = []
compound_list.append(create_brick_text(text_string))
compound_list.append(create_brick_hull(text_string))
compound_list += add_brick_studs(text_string)
compound_list += add_brick_cones(text_string)
compound_list += add_brick_rings(text_string)
create_mesh_and_export(text_string, compound_list)

# removing templates
doc.removeObject("studring_template")
doc.removeObject("studring")
doc.removeObject("outer_studring_template")
doc.removeObject("inner_studring_template")
doc.removeObject("cone_template")
doc.removeObject("loft")
doc.removeObject("sketch_bc")
doc.removeObject("sketch_tc")

# show in GUI
doc.recompute()
FreeCADGui.ActiveDocument.ActiveView.fitAll()
