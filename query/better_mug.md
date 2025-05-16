###
##    Write a Python script using CadQuery to create a cylinder with another cylinder twisted to a semicircle and attached to the first cylinder to resemble a parametric mug. The script should:
##        - Create a base cylinder of diameter 6 inches and height of 6 inches
##        - Ensure that the cylinder is a tube with a wall thickness of 0.3 inches and hollow in the center
##        - Generate a base plate of 1/2 inch thickness and of same diameter as the cylinder should be attached to the base of the cylinder
##        - Generate a another cylinder of diameter 1 inch and a length of 3 inches.
##        - Ensure that the cyclinder is bent from start to end with a bend radius of 1.5 inches creating a open semicircle
##        - Ensure that the both ends of the bent cylinder is connected to the cylinder's curved exterior surface smoothly at two points aligning with one above another, and centered vertically along the first cylinder's height.
##        - Include proper imports and documentation
##        - Use proper methods available in documentation and do not make your own.
##        - Ensure the final object is a valid solid
##        - Ensure that the output is displayed with display(item) instead of show_object(item), "item" being the variable name of the final object
##
##    
import cadquery as cq
import math

# Parameters (all dimensions in inches)
outer_diam = 6.0          # overall cylinder diameter
mug_height = 6.0          # mug body height
wall_thickness = 0.3      # mug wall thickness
base_thickness = 0.5      # thickness of the base plate
handle_diam = 1.0         # handle cross‐section diameter
handle_radius = 1.5       # bending (arc) radius for the handle

# Create the mug body as a hollow tube
outer_cyl = cq.Workplane("XY").circle(outer_diam / 2.0).extrude(mug_height)
inner_cyl = cq.Workplane("XY").circle(outer_diam / 2.0 - wall_thickness).extrude(mug_height)
tube = outer_cyl.cut(inner_cyl)

# Create the base plate; position it so that it attaches to the bottom of the tube
base_plate = cq.Workplane("XY", origin=(0, 0, -base_thickness)).circle(outer_diam / 2.0).extrude(base_thickness)

mug_body = tube.union(base_plate)

# Create a semicircular handle that attaches to the mug's exterior.
# The two attachment points are chosen on the mug's side at x = outer_diam/2 (i.e. 3 inches)
# and centered vertically: one at z = mug_height/2 + handle_radius and the other at z = mug_height/2 - handle_radius.
attach_x = outer_diam / 2.0           # x = 3.0
attach_z_top = mug_height / 2.0 + handle_radius   # 3 + 1.5 = 4.5
attach_z_bot = mug_height / 2.0 - handle_radius   # 3 - 1.5 = 1.5
attach_mid_z = (attach_z_top + attach_z_bot) / 2.0  # = 3.0

# To create a semicircular arc that bulges outward,
# we set a local workplane whose origin is at the midpoint between attachment points.
# In that local XZ-plane, the attachment points become (0, 1.5) and (0, -1.5)
# and the arc will bulge in the positive X direction.
handle_path = (
    cq.Workplane("XZ", origin=(attach_x, 0, attach_mid_z))
      .moveTo(0, attach_z_top - attach_mid_z)        # start point relative: (0, +1.5)
      .threePointArc((handle_radius, 0), (0, attach_z_bot - attach_mid_z))  # endpoint relative: (0, -1.5)
      .val()
)

# Create the handle profile: a circle of radius handle_diam/2.
# Place it at the start of the handle path.
# For proper sweep, the profile workplane must be perpendicular to the tangent of the path at its start.
# At the start point (global (attach_x, 0, attach_z_top)), the tangent of the arc is approximately (-1, 0, 0)
# so we choose the YZ plane (which has normal along X) as the profile workplane.
handle_profile = cq.Workplane("YZ", origin=(attach_x, 0, attach_z_top))
handle = handle_profile.circle(handle_diam / 2.0).sweep(handle_path, multisection=False)

# Combine the mug body and handle
final_obj = mug_body.union(handle)


display(final_obj)