import maya.cmds as cmds
import random
import re

#Global Variables
main_radius = 0.5
main_taper = 0.3
branch_density = 0.05
bumpiness = 0
offshoot_radius = 0.1
offshoot_taper = 0.2
chamber_size = 0.5
    

################################################################
## Modeling Functions
###############################################################

##
# Creates extruded surface, bezier curve is top down for main tunnel
##
def main_poly_from_curve(curveName, circlePos):
    curve_tangent = cmds.pointOnCurve( curveName, pr=0.01, t=True )
    circle_constr = cmds.circle(c=(circlePos[0], circlePos[1], circlePos[2]), nr= (curve_tangent[0], curve_tangent[1], curve_tangent[2]), sw=360, r=main_radius, d=3, s=8, ch=1)
    cmds.xform(cpc=True)
    surface_name = cmds.extrude(circle_constr[0], curveName, ch=True, rn=False, po=1, et=2, ucp=0, fpt=0, upn=1, ro=0, scale=main_taper, rsp=1)
    cmds.select(curveName, d=True)
    cmds.delete(circle_constr)
    return surface_name

##
# Creates extruded surface for offshoots
##
def offshoot_poly_from_curve(curveName, circlePos):
    curve_tangent = cmds.pointOnCurve( curveName, pr=0.01, t=True )
    circle_constr = cmds.circle(c=(circlePos[0], circlePos[1], circlePos[2]), nr= (curve_tangent[0], curve_tangent[1], curve_tangent[2]), sw=360, r=offshoot_radius, d=3, s=8, ch=1)
    cmds.xform(cpc=True)
    surface_name = cmds.extrude(circle_constr[0], curveName, ch=True, rn=False, po=1, et=2, ucp=0, fpt=0, upn=1, ro=0, scale=offshoot_taper, rsp=1)
    cmds.select(curveName, d=True)
    cmds.delete(circle_constr)
    return surface_name

##
# Selects random edge loops along surface and rotates them slightly
##
def deform_surface(surfaceName):
    cmds.select(cl=True)
    edgeRings = cmds.polySelect(surfaceName[0], edgeRing=1, ns=1)
    del(edgeRings[0], edgeRings[-1])
    i = 1
    for obj in edgeRings:
        cmds.polySelect(surfaceName[0], el=edgeRings[i], add=True)
        i+=3
        if i >= len(edgeRings):
            break
    cmds.rotate(bumpiness, 0, 0, relative=True, cs=True)
    return

##
# Creates curve pointing from selected face normal
##
def create_offshoot(manipPos): 
    selection = cmds.ls(selection=True)
    target = cmds.curve( p=[(-1, 0, 0), (-0.66, -0.1, 0.1), (-0.33, -0.3, -0.2), (0, -0.4, -0.1)] )
    cvpos = [cmds.getAttr(target+".controlPoints[0].xValue"), cmds.getAttr(target+".controlPoints[0].yValue"), cmds.getAttr(target+".controlPoints[0].zValue")]
    cvpos[0] += cmds.getAttr(target+".tx")
    cvpos[1] += cmds.getAttr(target+".ty")
    cvpos[2] += cmds.getAttr(target+".tz")
    cmds.xform(target, piv=cvpos, ws=True)
    cmds.move(manipPos[0], manipPos[1], manipPos[2], target, rpr=True, a=True)
    constr = cmds.normalConstraint(selection, target, aimVector = (1,0,0))
    cmds.delete(constr)
    #Extrudes geometry based on curve
    offshoot_poly_from_curve(target, manipPos)
    return target 
##
# Selects random faces along surface and extrude curves from it
##
def populate_offshoots(main_tunnel):
    faceList = cmds.ls(main_tunnel+".f[*]", fl=True)
    myRange = int(cmds.polyEvaluate(main_tunnel, f=True))
    weightList = ["A", "A", "A", "B"]
    createdCurves = []

    i = 0
    for obj in faceList:
        if i == int(myRange * branch_density):
            break
        i+=1
        selectedFace = cmds.select(clear=True)
        polyInfoY = 1
        random_number = 0

        while polyInfoY > 0.2:
            weightedList = random.choice(weightList)
            if (weightedList == "A"):
                random_number = random.randrange(0, (myRange / 4))
                selectedFace = cmds.select(faceList[random_number])
            else:
                random_number = random.randrange(0, myRange)
                selectedFace = cmds.select(faceList[random_number])
            vtxPos = cmds.polyInfo(faceList[random_number], fv=True)
            vertices = [int(j) for j in vtxPos[0].split() if j.isdigit()]
            polyInfo = cmds.polyInfo(faceNormals=True)
            polyInfoArray = re.findall(r"[\w.-]+", polyInfo[0])
            polyInfoY = float(polyInfoArray[3])
            cmds.select(main_tunnel+".vtx[" + str(vertices[2]) + "]")
        cmds.setToolTo("Move")
        pos = cmds.manipMoveContext('Move', query=True, position=True)
        createdCurves.append(create_offshoot(pos)) 
    return createdCurves

##
# Creates chamber based on curve
##
def create_chamber(chamberName):
    chamber_shape = cmds.bevelPlus(chamberName, ch=True, no=True, rn=False, polygon=1, ns=4,
                    js=True, width=0.75, depth=0.1, extrudeDepth=0.1, capSides=4,
                    bevelInside=0, outerStyle=2, innerStyle=2, polyOutMethod=2,
                    polyOutCount=200, polyOutExtrusionType=3, polyOutExtrusionSamples=2,
                    polyOutCurveType=3, polyOutCurveSamples=6, polyOutUseChordHeightRatio=0)
    cmds.xform(cpc=True)
    cmds.scale(chamber_size, chamber_size, chamber_size, chamber_shape[0])
    return chamber_shape[0]

##
# Duplicates given object and moves it to given positions
##
def dupl_move_chamber(toDupe, cvs):
    selection = cmds.ls(selection=True)
    for x in cvs:
        cvpos = cmds.pointPosition(x+".controlPoints[3]")
        chamber = cmds.duplicate(toDupe)
        cmds.move(cvpos[0], cvpos[1], cvpos[2], chamber, rpr=True, a=True)
        cmds.delete(x)
    return

##
# Creates a circle at origin facing in the y direction
##
def default_circle(_ignore):
    cmds.circle(nr=(0,1,0), c=(0,0,0))
    return

##
# Creates two sample curves that can be used to work the rest of the tool
##
def default_curves(_ignore):
    cmds.curve( p=[(-0.6, 42.7, 0), (-2.9, 32.4, 0), (-0.8, 30, 0), (1.2, 27.7, 0), (3, 16.4, 0), (-1.9, 10.6, 0), (-6.8, 4.8, 0), (-1.7, 0.6, 0)] )
    my_curve = cmds.curve(p=[(0, 0, -1.33), (0.75, 0, -0.89), (2.2, 0, 0), (0, 0, 1.65), (-1.5, 0, 0), (-0.5, 0, -0.88)])
    cmds.closeCurve(my_curve, ch=True, rpo=True, ps=False)
    return
################################################################

#UI
class BurrowUI(object):
    # UI Layouts
    def curve_button_layout(self, mainWidth):
        rowWidth = [mainWidth * 0.33, mainWidth * 0.33, mainWidth * 0.33]
        cmds.rowLayout(nc=3, cl3=("center", "center", "center"), ct3=("both", "both", "both"), cw3=rowWidth)
        createBezierButton = cmds.button(l = "Create Bezier (Tunnel)", c=cmds.CreateBezierCurveTool)
        createCircleButton = cmds.button(l = "Create Circle (Chamber)", c=default_circle)
        createSampleButton = cmds.button(l = "Create Sample Curves", c=default_curves)
        cmds.setParent("..")
        return

    def curve_icon_layout(self, mainWidth):
        rowWidth = [mainWidth * 0.33, mainWidth * 0.33, mainWidth * 0.33]
        rowOffset = [(mainWidth * 0.166) - 16, (mainWidth * 0.166) - 16, (mainWidth * 0.166) - 16]
        cmds.rowLayout(nc=3, cl3=("center", "center", "center"), ct3=("left", "left", "left"), co3=(rowOffset), cw3=rowWidth)
        createBezierIcon = cmds.image(image=":/curveBezier.png")
        createCircleIcon = cmds.image(image=":/circle.png")
        createSampleIcon = cmds.image(image=":/crvOffset.png")
        cmds.setParent("..")
        return
    
    def nurbs_to_poly_layout(self):
        cmds.frameLayout(l="NURBS to Poly Settings", cl=True, cll=True)
        cmds.scrollField(tx = "Access NURBS to Poly Options\nUsed in generating Main Tunnel and Offshoots\nAdjust based on user preference", ed=False, nl=3, h=60)
        cmds.separator(h=10)
        createConvertButton = cmds.button(l = "Show NURBS to Polygons Options", c=cmds.NURBSToPolygonsOptions)
        return
    # Main UI
    def __init__(self):
        winName = "myWindow"
        winWidth = 500
        surface_name = []

        if cmds.window(winName, exists=True):
            cmds.deleteUI(winName)

        cmds.window(winName, title="Ant Colony Creator", mm=True, width=winWidth)
        baseLayout = cmds.columnLayout(adjustableColumn=True)

        cmds.separator(h=10)
        cmds.scrollField(tx = "Create custom curves as guidelines for the plugin,\nor create sample curves for quick use", ed=False, nl=4, h=50)
        cmds.separator(h=10)

        self.curve_icon_layout(winWidth)
        self.curve_button_layout(winWidth)
        cmds.separator(h=20)

        cmds.scrollField(tx = "This plugin generates the structrue of an ant colony in two parts. \nSelect a curve to become the main tunnel,\nthen hit the Create Tunnel button after adjusting settings.", ed=False, nl=4, h=60)
        cmds.separator(h=10)
        self.mtrSlider = cmds.floatSliderGrp(l = "Main Tunnel Radius", min=0, max=1, field=True, s=0.01, fmx=100, v=0.5)
        self.mttSlider = cmds.floatSliderGrp(l = "Main Tunnel Taper", min=0, max=1, field=True, s=0.01, fmx=2, v=0.3)
        self.bumpSlider = cmds.intSliderGrp(l = "Bumpiness", min = 0, max = 100, field = True, v=10)
        cmds.separator(h=10)
        createTunnelButton = cmds.button(l = "Create Tunnel", command=self.create_main_tunnel)
        cmds.separator(h=20)

        cmds.scrollField(tx = "Select curve to serve as base for chambers,\nthen add chambers by hitting the Create Chambers button\nafter adjusting settings", ed=False, nl=3, h=60)
        cmds.separator(h=10)
        self.cSizeSlider = cmds.floatSliderGrp(l = "Chamber Size", min = 0, max = 10, field = True, fmx = 100, s=0.1, v=0.5)
        self.densitySlider = cmds.floatSliderGrp(l = "Branch Density", min = 0, max = 100, field = True, s=0.01, v=5)
        self.orSlider = cmds.floatSliderGrp(l = "Offshoot Radius", min=0, max=1, field=True, s=0.01, fmx=10, v=0.1)
        self.otSlider = cmds.floatSliderGrp(l = "Offshoot Taper", min=0, max=1, field=True, s=0.01, fmx=2, v=0.3)

        cmds.separator(h=10)
        createChamberButton = cmds.button(l = "Create Chambers", command = self.create_offshoots_chambers)
        cmds.separator(h=10)
        
        self.nurbs_to_poly_layout();

        cmds.showWindow(winName)
    
    ###### UI Calling Functions ######

    ##
    # Update Variables: Radius, Taper, Bumpiness, Input Curve, Extrude Start
    # Calls functions that create main tunnel
    ##
    def create_main_tunnel(self, _ignore):
        
        global main_radius
        global main_taper
        global bumpiness

        main_radius = cmds.floatSliderGrp(self.mtrSlider, q=True, v=True)
        main_taper = cmds.floatSliderGrp(self.mttSlider, q=True, v=True)
        bumpiness = cmds.intSliderGrp(self.bumpSlider, q=True, v=True)
        curveName = cmds.ls(sl=True)
        if (bool(curveName) == False):
            cmds.warning("No Curve selected")
            return
        myPoint = cmds.pointPosition("{}.cv[0]".format(curveName[0]))

        self.surface_name = main_poly_from_curve(curveName, myPoint)
        deform_surface(self.surface_name)
        return

    ##
    # Update Variables: Branch Density, Branch Radius, Branch Taper, and Chamber Size
    # Calls function that populate the main tunnel with branches and chambers
    ##
    def create_offshoots_chambers(self,  _ignore):
        
        global branch_density
        global chamber_size
        global offshoot_radius
        global offshoot_taper

        offshoot_taper = cmds.floatSliderGrp(self.otSlider, q=True, v=True)
        offshoot_radius = cmds.floatSliderGrp(self.orSlider, q=True, v=True)
        branch_density = (cmds.floatSliderGrp(self.densitySlider, q=True, v=True) / 100)
        chamber_size = cmds.floatSliderGrp(self.cSizeSlider, q=True, v=True)
        curveName = cmds.ls(sl=True)
        if (bool(curveName) == False):
            cmds.warning("No Curve selected")
            return

        cvList = populate_offshoots(self.surface_name[0])
        created_chamber = create_chamber(curveName)
        dupl_move_chamber(created_chamber, cvList)
        return
myScript = BurrowUI()