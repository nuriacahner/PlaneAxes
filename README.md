# Plane Axes (PlaneAxes)

A Fusion add-in that gives a **construction plane its own X and Y axes**, from two points,
as a datum plane in 3-matic has them. The axes are ordinary Fusion construction axes, so you
can use them anywhere: as references, in measurements, or to build on.

## Why

In 3-matic, a datum plane has its own coordinate system. Measurement protocols use it:
"measure along the plane's X", "the plane's Y axis". In Fusion a construction plane has no
axes of its own, so each one has to be built by hand:
1. a sketch on the plane;
2. the points projected into it;
3. two perpendicular lines;
4. an axis on each line.

This add-in does all of that in one step, with the same ordinary features, so the result
stays parametric.

## Using it

**Solid → Construct → Plane Axes**

1. Open **Plane Axes**. A plane selected beforehand is picked up automatically.
2. Pick:
   - **Plane:** the construction plane;
   - **Point 1 (origin):** where the axes start;
   - **Point 2 (X direction):** X runs from point 1 towards this point.

   The points can be construction points, sketch points or vertices, and **they don't need
   to lie on the plane**: both are projected onto it. For example, use the tips of two bony
   landmarks above a bone's cross-section plane.
3. Optionally change the **Name**, which by default is the plane's name.
4. Press **Create axes**. You get:
   - **`<name> · Eje X`:** from point 1 towards point 2, projected onto the plane;
   - **`<name> · Eje Y`:** perpendicular to X, in the plane;
   - both kept in one timeline group, **`<name> · ejes`**.

There's no Z axis: it would be the plane's normal, which you usually have already (e.g. the
axis the plane was made perpendicular to).

To make axes again for a plane that already has them, delete its timeline group first.

## Install

1. Clone or copy this folder anywhere.
2. Run `powershell -File install.ps1`. It copies the add-in to
   `%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\PlaneAxes`.
3. In Fusion: **Utilities → ADD-INS → Scripts and Add-Ins → Add-Ins**, select
   **PlaneAxes**, keep *Run on Startup* ticked, and press **Run**.
4. The button appears in **Solid → Construct**.

No extra Python packages are needed.

## How it works

The add-in builds the same features you would make by hand:
1. a **sketch on the plane**, with point 1 and point 2 projected into it;
2. an **X line** from projected point 1 to projected point 2;
3. a **Y line** from point 1, held **perpendicular** to X by a sketch constraint;
4. a **construction axis on each line** (*Axis Through Edge*);
5. the sketch is hidden, and everything is grouped in the timeline.

The plane remembers its axes in an attribute, so the add-in can tell when a plane already
has them.

Because these are ordinary, parametric features, **the axes follow** when the plane moves or
tilts, or when either point moves. This was checked by moving point 2 and tilting the plane
after creating the axes.

The Y line is deliberately not constrained to the same length as X. With that constraint
the X line stopped following a moved point 2. Y's length doesn't matter for an axis.

## Repository layout

| Path | |
|---|---|
| `PlaneAxes.py` | add-in shell: lifecycle, toolbar button, events |
| `pa_core.py` | the dialog and building the axes; re-imported on every command |
| `install.ps1` | copies the add-in into Fusion's AddIns folder |
| `resources/PlaneAxes/` | toolbar icons |
| `tools/make_icons.py` | draws the icons |

## Tests

There are no offline tests: the add-in only uses Fusion's API. It was tested inside Fusion,
in a throwaway document:
- X along the projected point 1 → point 2;
- X perpendicular to Y, both in the plane;
- the same after moving point 2 and tilting the plane.

## Known limits

- **One set of axes per plane.** Delete the timeline group to make them again.
- **Points 1 and 2 must not project onto the same spot** of the plane. A point 2 straight
  above point 1 gives no direction, and the dialog says so.
- **Timeline groups need a parametric design** (with history). In a direct design the
  features are created without a group.
- **The axis names use Spanish** (*Eje X*, *Eje Y*, *ejes*). Rename them in the browser if
  you prefer.

## Licence

MIT. See `LICENSE`.
