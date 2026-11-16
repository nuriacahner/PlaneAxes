"""PlaneAxes - the working code. RE-IMPORTED on every command (hot reload).

Nothing may live in a module global between events. A Fusion construction plane has no
axes of its own (a 3-matic datum plane does: IT011-V4 measures "along the plane's X / Y
/ Z" and uses "the plane's Y axis"). This gives a plane - still an ordinary Fusion
construction plane - its own X and Y, built from ordinary, parametric Fusion features:

  sketch on the plane: point 1 and point 2 projected, X line p1 -> p2, Y line from p1
                       perpendicular to it (constraint; NOT Equal - see build());
  Eje X / Eje Y:       Axis Through Edge on those sketch lines;
  both in one timeline group "<name> · ejes"; the plane gets an attribute naming them.

No Eje Z (v0.2, 2026-11-04): the plane's normal is the bone axis ("Eje Radio" / "Eje
Cúbito") on the perpendicular planes, so the user would never use it. v0.1 made it as the
line where two hidden Plane Along Path planes meet, if it is ever wanted.

Axis convention used for the forearm: X = radio-cubital, Y = dorso-palmar, Z =
longitudinal - pick point 1 -> point 2 accordingly (e.g. Estiloides Radial -> Estiloides
Cubital on a bone's perpendicular plane).

Verified 2026-11-04 in a throwaway document: X along the projected
p1 -> p2, X ⊥ Y, both in the plane, before and after moving p2 and tilting the plane;
all healthy.
API fact found on the way: ConstructionAxisInput.setByLine takes an InfiniteLine3D (not
parametric); setByEdge(sketchLine) is the parametric one.
"""

import adsk.core
import adsk.fusion

import datetime
import json

PANELS = ['ConstructionPanel']
ATTR_GROUP = 'PlaneAxes'
ATTR_NAME = 'axes'
POINT_FILTERS = ('ConstructionPoints', 'SketchPoints', 'Vertices')


# --------------------------------------------------------------------------- #
# toolbar
# --------------------------------------------------------------------------- #

def place_button(ui, cmd_def):
    """Add the button to PANELS (Solid > Construct). Returns the controls."""
    controls = []
    for pid in PANELS:
        panel = ui.allToolbarPanels.itemById(pid)
        if not panel:
            continue
        old = panel.controls.itemById(cmd_def.id)
        if old:
            old.deleteMe()
        ctrl = panel.controls.addCommand(cmd_def)
        ctrl.isPromotedByDefault = False
        controls.append(ctrl)
    return controls


def on_marking_menu(ui, args, cmd_def):
    """No right-click entry since v0.2 (it never showed, and the user prefers the
    Construct button). Kept so a v0.1 shell still running doesn't fail; can go."""
    return


# --------------------------------------------------------------------------- #
# building the axes
# --------------------------------------------------------------------------- #

def existing_axes(plane):
    """The axes a plane already has (attribute), if they still exist."""
    attr = plane.attributes.itemByName(ATTR_GROUP, ATTR_NAME)
    if not attr:
        return None
    rec = json.loads(attr.value)
    des = plane.component.parentDesign            # a construction plane has .component
    found = des.findEntityByToken(rec.get('x', '')) if rec.get('x') else []
    return rec if found else None


def _axis_on(root, line, name):
    ai = root.constructionAxes.createInput()
    ai.setByEdge(line)
    ax = root.constructionAxes.add(ai)
    ax.name = name
    return ax


def build(design, plane, p1, p2, name):
    """Create the axes of `plane` from point 1 (origin) to point 2 (X). Returns the
    {'x', 'y'} construction axes."""
    if existing_axes(plane):
        raise ValueError('"%s" already has axes (timeline group "%s"). Delete that group to '
                         'make new ones.' % (plane.name, existing_axes(plane).get('group')))
    root = design.rootComponent
    tl = design.timeline
    first = tl.markerPosition if design.designType == adsk.fusion.DesignTypes.ParametricDesignType else None

    sk = root.sketches.add(plane)
    sk.name = '%s · ejes (sketch)' % name
    pa = adsk.fusion.SketchPoint.cast(sk.project(p1).item(0))
    pb = adsk.fusion.SketchPoint.cast(sk.project(p2).item(0))
    ga, gb = pa.geometry, pb.geometry
    dx, dy = gb.x - ga.x, gb.y - ga.y
    if dx * dx + dy * dy < 1e-10:
        sk.deleteMe()
        raise ValueError('The two points fall on the same spot of the plane. Pick a point 2 '
                         'that lies away from point 1 along the plane.')
    lines = sk.sketchCurves.sketchLines
    xl = lines.addByTwoPoints(pa, pb)
    yl = lines.addByTwoPoints(pa, adsk.core.Point3D.create(ga.x - dy, ga.y + dx, 0))
    sk.geometricConstraints.addPerpendicular(xl, yl)
    # NO Equal constraint: with it, X stopped following a moved point 2 (the projected
    # point moved, the X line didn't; 68° off in the test). Y's length doesn't matter.

    ex = _axis_on(root, xl, '%s · Eje X' % name)
    ey = _axis_on(root, yl, '%s · Eje Y' % name)
    sk.isVisible = False

    group = '%s · ejes' % name
    if first is not None:
        try:
            g = tl.timelineGroups.add(sk.timelineObject.index, ey.timelineObject.index)
            g.name = group
        except Exception:
            group = None
    rec = {'x': ex.entityToken, 'y': ey.entityToken,
           'sketch': sk.name, 'group': group, 'name': name,
           'point1': getattr(p1, 'name', None), 'point2': getattr(p2, 'name', None),
           'created': datetime.datetime.now().isoformat(timespec='seconds')}
    attr = plane.attributes.itemByName(ATTR_GROUP, ATTR_NAME)
    if attr:
        attr.value = json.dumps(rec)
    else:
        plane.attributes.add(ATTR_GROUP, ATTR_NAME, json.dumps(rec))
    return {'x': ex, 'y': ey}


# --------------------------------------------------------------------------- #
# command handlers (called by the shell)
# --------------------------------------------------------------------------- #

def _picked(inputs, iid):
    sel = inputs.itemById(iid)
    return sel.selection(0).entity if sel.selectionCount else None


def _point_name(e):
    if e is None:
        return '—'
    try:
        return e.name
    except Exception:
        pass
    sp = adsk.fusion.SketchPoint.cast(e)
    if sp:
        return 'a point of sketch «%s»' % sp.parentSketch.name
    v = adsk.fusion.BRepVertex.cast(e)
    if v:
        return 'a vertex of %s' % v.body.name
    return e.objectType.split('::')[-1]


def _report(inputs):
    plane, p1, p2 = _picked(inputs, 'plane'), _picked(inputs, 'p1'), _picked(inputs, 'p2')
    if plane is None:
        return 'Pick the construction plane.'
    pl = adsk.fusion.ConstructionPlane.cast(plane)
    if pl and existing_axes(pl):
        return '<b>%s</b> already has axes (group "%s"). Delete that group to make new ones.' % (
            pl.name, existing_axes(pl).get('group'))
    if p1 is None:
        return 'Pick <b>point 1</b>: the origin. X starts here.'
    if p2 is None:
        return 'Pick <b>point 2</b>: X points from point 1 towards it.'
    name = inputs.itemById('name').value.strip() or pl.name
    return ('<b>%s · Eje X</b>: %s → %s, projected onto the plane<br>'
            '<b>%s · Eje Y</b>: perpendicular to X, in the plane<br>'
            'Both in the timeline group "%s · ejes"; they follow the plane and the points.'
            % (name, _point_name(p1), _point_name(p2), name, name))


def on_created(app, cmd):
    inputs = cmd.commandInputs
    sel = inputs.addSelectionInput('plane', 'Plane', 'The construction plane to give X and Y axes to.')
    sel.addSelectionFilter('ConstructionPlanes')
    sel.setSelectionLimits(0, 1)
    for iid, label, tip in (('p1', 'Point 1 (origin)', 'Where the axes start. X starts here.'),
                            ('p2', 'Point 2 (X direction)', 'X points from point 1 towards this '
                             'point. Both are projected onto the plane, so they can be off it '
                             '(e.g. the styloid tips).')):
        s = inputs.addSelectionInput(iid, label, tip)
        for f in POINT_FILTERS:
            s.addSelectionFilter(f)
        s.setSelectionLimits(0, 1)
    inputs.addStringValueInput('name', 'Name', '')
    inputs.addTextBoxCommandInput('report', '', '', 5, True)
    cmd.okButtonText = 'Create axes'
    cmd.setDialogMinimumSize(380, 260)
    # a plane selected before the command (browser / canvas) is the one
    sels = app.userInterface.activeSelections
    for i in range(sels.count):
        pl = adsk.fusion.ConstructionPlane.cast(sels.item(i).entity)
        if pl:
            if sel.selectionCount == 0:
                sel.addSelection(pl)
            inputs.itemById('name').value = pl.name
            inputs.itemById('p1').hasFocus = True
            break
    inputs.itemById('report').formattedText = _report(inputs)


def on_input_changed(app, inputs, input_id):
    if input_id == 'plane':
        pl = adsk.fusion.ConstructionPlane.cast(_picked(inputs, 'plane'))
        if pl:
            name = inputs.itemById('name')
            if not name.value.strip():
                name.value = pl.name
            inputs.itemById('p1').hasFocus = True
    elif input_id == 'p1' and _picked(inputs, 'p1') and not _picked(inputs, 'p2'):
        inputs.itemById('p2').hasFocus = True       # like Fusion's own tools
    inputs.itemById('report').formattedText = _report(inputs)


def on_validate(inputs):
    pl = adsk.fusion.ConstructionPlane.cast(_picked(inputs, 'plane'))
    p1, p2 = _picked(inputs, 'p1'), _picked(inputs, 'p2')
    if not (pl and p1 and p2) or existing_axes(pl):
        return False
    return p1 != p2


def on_execute(app, cmd):
    inputs = cmd.commandInputs
    des = adsk.fusion.Design.cast(app.activeProduct)
    pl = adsk.fusion.ConstructionPlane.cast(_picked(inputs, 'plane'))
    name = inputs.itemById('name').value.strip() or pl.name
    build(des, pl, _picked(inputs, 'p1'), _picked(inputs, 'p2'), name)
