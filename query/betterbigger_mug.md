###
##    Write a Python script using CadQuery to create a cylinder with another cylinder twisted to a semicircle and attached to the first cylinder to resemble a parametric mug. The script should:
##        - Create a base cylinder of diameter 7 inches and height of 7 inches
##        - Ensure that the cylinder is a tube with a wall thickness of 0.3 inches and hollow in the center
##        - Generate a base plate of 1/2 inch thickness and of same diameter as the cylinder should be attached to the base of the cylinder
##        - Generate a another cylinder of diameter 1 inch and a length of 3 inches.
##        - Ensure that the cyclinder is bent from start to end with a bend radius of 1.5 inches creating a open semicircle
##        - Ensure that the both ends of the bent cylinder is connected to the cylinder's curved exterior surface sitting flush and smoothly at two points aligning with one above another, and centered vertically along the first cylinder's height.
##        - Include proper imports and documentation
##        - Use proper methods available in documentation and do not make your own.
##        - Ensure the final object is a valid solid
##        - Ensure that the output is displayed with display(item) instead of show_object(item), "item" being the variable name of the final object
##
##    
import cadquery as cq
import math

# Parameters (in inches)
mug_diam = 7.0
mug_height = 7.0
wall_thickness = 0.3
base_thickness = 0.5
handle_diam = 1.0
handle_radius = handle_diam / 2.0
handle_bend_radius = 1.5

mug_outer_radius = mug_diam / 2.0

# For the handle attachment on the mug’s curved exterior,
# we choose the two end points to lie at the mid‐height of the mug.
# We want the handle’s wire to lie in the vertical (XZ) plane at y = 0.
# The endpoints will be at (mug_outer_radius, 0, attach_z_low) and (mug_outer_radius, 0, attach_z_high)
# with attach_z_low and attach_z_high symmetric about mug_height/2.
attach_span = 3.0     # vertical chord length of the handle attachment
attach_z_mid = mug_height / 2.0
attach_z_low = attach_z_mid - attach_span / 2.0  # = 2.0
attach_z_high = attach_z_mid + attach_span / 2.0 # = 5.0

# -----------------------------------------------------
# Create the mug tube:
# Build the outer solid by extruding a circle in the XY plane.
outer_cyl = cq.Workplane("XY").circle(mug_outer_radius).extrude(mug_height)
# Create the inner hollow by extruding a smaller circle.
inner_cyl = cq.Workplane("XY").circle(mug_outer_radius - wall_thickness).extrude(mug_height)
# Subtract the inner from the outer to yield a hollow tube.
mug_tube = outer_cyl.cut(inner_cyl)

# -----------------------------------------------------
# Create the base plate:
# This plate has the same diameter as the mug and is 1/2 inch thick.
# It will sit beneath the mug tube.
base_plate = (cq.Workplane("XY")
              .circle(mug_outer_radius)
              .extrude(base_thickness)
              .translate((0, 0, -base_thickness)))

# -----------------------------------------------------
# Create the handle:
# We design the handle as a swept solid.
# Its centerline is defined by a circular arc in the XZ (vertical) plane (with y = 0).
# The bottom attachment point is A = (mug_outer_radius, 0, attach_z_low)
# The top attachment point is B = (mug_outer_radius, 0, attach_z_high)
# To obtain a semicircular arc with a bending radius of 1.5 inches,
# we choose an intermediate point that pushes the arc outward.
# Here we use C = (mug_outer_radius + handle_bend_radius, 0, attach_z_mid)
handle_path = (cq.Workplane("XZ")
               .moveTo(mug_outer_radius, attach_z_low)
               .threePointArc((mug_outer_radius + handle_bend_radius, attach_z_mid),
                              (mug_outer_radius, attach_z_high))
               .val())

# Define the circular cross‐section for the handle.
# We create it on a workplane that is positioned at the start of the arc.
handle_profile = (cq.Workplane("YZ", origin=(mug_outer_radius, 0, attach_z_low))
                  .circle(handle_radius))

# Sweep the profile along the arc to produce the handle solid.
handle_solid = handle_profile.sweep(handle_path)

# -----------------------------------------------------
# Combine all parts into the final mug object.
final_obj = mug_tube.union(base_plate).union(handle_solid)

# Validate the final object.
assert final_obj.val().isValid(), "The final solid is not valid!"

# Display the final object.
display(final_obj)
