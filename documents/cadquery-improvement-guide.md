# CadQuery Code Generation Guidelines

## Core Principles for 3D CAD Generation

1. **Precision in Geometry Positioning**
   - Use mathematical approaches (trigonometry, parametric equations) for positioning on curved surfaces
   - Convert between coordinate systems thoughtfully (Cartesian, cylindrical, etc.)
   - Ensure continuity and symmetry in patterns on curved surfaces

2. **Effective Boolean Operations**
   - Build complete base geometry before applying complex operations
   - Ensure cutting solids extend fully through target surfaces
   - Verify that all operations result in valid, manifold geometry

3. **Proper Workplane Management**
   - Position workplanes intentionally in 3D space to align with desired features
   - Use transformation matrices to maintain correct orientation on curved surfaces
   - Create local coordinate systems that follow the contours of complex surfaces

## Specific Techniques for Common Patterns

### Placing Features on Cylindrical Surfaces

1. **Projection Method (Preferred for Complex Shapes)**
   ```python
   # Create base shape on a flat workplane
   shape_wire = (cq.Workplane("XZ", origin=(0, radius, z_position))
                 .polygon(6, size)
                 .wires()
                 .val())
   
   # Project onto cylindrical surface
   projected_wire = shape_wire.projectToShape(
       targetObject=cylinder.val(), 
       center=(0, 0, z_position)
   )[0]
   
   # Rotate around cylinder axis for multiple instances
   rotated_wire = projected_wire.rotate((0, 0, 0), (0, 0, 1), angle)
   ```

2. **Direct Transformation Method (More Intuitive)**
   ```python
   for i in range(n_features):
       angle_deg = i * 360.0 / n_features
       angle_rad = math.radians(angle_deg)
       
       # Position on cylinder surface
       x = radius * math.cos(angle_rad)
       y = radius * math.sin(angle_rad)
       
       # Create a feature on a transformed workplane
       feature = (cq.Workplane("XY")
                  .transformed(offset=(x, y, z), rotate=(0, 90, angle_deg))
                  .polygon(6, size)
                  .extrude(depth, both=True))
   ```

### Creating Hollow Objects

1. **Shell Method (For Complex Shapes)**
   ```python
   # Create solid and then hollow it out
   solid = cq.Workplane("XY").box(10, 10, 10)
   hollow = solid.shell(-1)  # Negative value hollows inward
   ```

2. **Cut Method (For Simple Shapes)**
   ```python
   # Create outer shape then cut out inner shape
   outer = cq.Workplane("XY").circle(outer_radius).extrude(height)
   inner = cq.Workplane("XY").circle(inner_radius).extrude(height)
   hollow = outer.cut(inner)
   ```

3. **Face Thickening (For Surface-Based Models)**
   ```python
   # Extract a face and thicken it
   surface = cylinder.faces("not %Plane").val()
   shell = surface.thicken(thickness)
   ```

### Distributing Features on Surfaces

1. **Even Distribution Around Circumference**
   ```python
   for i in range(n_features):
       angle = i * 360.0 / n_features
       # Position feature at angle
   ```

2. **Grid Patterns on Curved Surfaces**
   ```python
   for row in range(n_rows):
       z = row * row_spacing
       for col in range(n_columns):
           angle = col * 360.0 / n_columns
           # Offset alternate rows for better distribution
           if row % 2 == 1:
               angle += 360.0 / (2 * n_columns)
   ```

3. **Maintaining Feature Orientation on Curved Surfaces**
   - Always orient workplanes to be normal (perpendicular) to the target surface
   - For cylindrical surfaces, rotate the workplane to match the angle around the cylinder
   - Use the `.transformed()` method with correct rotation parameters

## Common Errors and Solutions

1. **"No Pending Wires" Errors**
   - Ensure wire objects are properly created before operations
   - Use `.wires().val()` to extract wire objects from workplanes
   - Verify that operations on wires return valid wire objects

2. **Boolean Operation Failures**
   - Check that all objects involved in boolean operations are valid solids
   - Ensure cutting objects extend fully through the target object
   - Verify that there's actual intersection between objects

3. **Projection Failures**
   - Ensure the target shape is a valid solid or face
   - Position the source shape close to the target surface
   - Specify a valid center point for projection
   - Validate that projected shapes are returned correctly

4. **Object Orientation Issues**
   - Use the full rotation matrix in `.transformed()` calls
   - Remember rotation order matters (XYZ vs. ZYX)
   - Double-check rotation angles (degrees vs. radians)

## Performance Optimization

1. **Use Face Operations When Possible**
   - Operating on faces is more efficient than on solids
   - Extract specific faces using selectors: `.faces("not %Plane").val()`
   - Apply operations like `.makeHoles()` or `.thicken()` on faces

2. **Batch Similar Operations**
   - Create arrays of features and apply them in batches
   - Use list comprehensions for generating multiple objects
   - Combine multiple operations where possible

## Code Structure Best Practices

1. **Define All Parameters at the Top**
   - Include clear, descriptive variable names
   - Document units of measurement
   - Establish relationships between parameters

2. **Use Functions for Repeated Patterns**
   - Create helper functions for generating specific features
   - Parameterize functions to make them reusable
   - Return valid CadQuery objects from functions

3. **Include Validation Steps**
   - Check `.isValid()` on complex objects
   - Add assertions to verify expected dimensions or properties
   - Include debug visualization during development


## Sweep Operation Troubleshooting

### "NCollection_Sequence::ChangeValue" Error in Sweep Operations

This error typically occurs during complex sweep operations, especially when creating curved features like mug handles. It indicates that the OpenCascade geometry engine (which underlies CadQuery) couldn't properly create the intended shape.

#### Common Causes and Solutions:

1. **Path and Profile Incompatibility**
   - **Problem**: Workplane orientations for the profile and path are incompatible
   - **Solution**: Ensure the profile's workplane is perpendicular to the start of the path
   ```python
   # Correct alignment of profile and path planes
   handle_profile = cq.Workplane("YZ").circle(radius)
   handle_path = cq.Workplane("XZ").threePointArc(...)
   ```

2. **Complex Path Geometry**
   - **Problem**: Path contains complex curves that are difficult to sweep along
   - **Solution**: Simplify the path or use an alternative construction method
   ```python
   # Alternative approach using revolve instead of sweep for curved handles
   handle = (
       cq.Workplane("YZ", origin=(center_x, 0, center_z))
          .circle(radius)
          .revolve(angle, (0, 0, 0), (0, 1, 0))
   )
   ```

3. **Improper Arc Construction**
   - **Problem**: The arc's control point doesn't create a valid, smooth curve
   - **Solution**: Calculate control points more precisely for arcs
   ```python
   # For a semicircular arc with radius R
   midpoint = (start_x - radius, (start_y + end_y) / 2)
   ```

4. **Coordinate System Issues**
   - **Problem**: Using mixed coordinate systems between the profile and path
   - **Solution**: Maintain consistent coordinate systems or explicitly transform between them
   ```python
   # Ensure consistent coordinate representation by working in the same principal planes
   # Use XZ for vertical arcs, XY for horizontal arcs, etc.
   ```

#### Best Practices for Reliable Sweep Operations:

1. Use simpler construction methods (revolve, loft) when appropriate
2. Test sweep operations with basic profiles before attempting complex ones
3. Ensure path and profile are properly oriented relative to each other
4. Verify that the path is a valid wire object before sweeping
5. Break complex shapes into multiple simpler sweep operations

#### Example: Robust Handle Creation

```python
# More robust approach to creating a curved handle
def create_handle(body_radius, attachment_height, handle_radius=0.5):
    # Calculate handle geometry
    center_offset = 1.5  # Distance of handle center from body
    handle_center = (-body_radius - center_offset, 0)
    
    # Create handle using revolve (more stable than sweep)
    handle = (
        cq.Workplane("YZ", origin=(handle_center[0], 0, attachment_height))
           .circle(handle_radius)
           .revolve(180, (0, 0, 0), (0, 1, 0))  # 180° around Y axis
    )
    
    # If a sweep is necessary, ensure proper workplane alignment
    # handle_profile = cq.Workplane("YZ").circle(handle_radius)
    # handle_path = cq.Workplane("XZ").threePointArc(...)
    # handle = handle_profile.sweep(handle_path)
    
    return handle
```

## Generating Handles and Curved Surfaces Attached to Other Bodies

### 1. Ensuring Proper Attachment to the Main Body
- The handle's **endpoints** should be placed **precisely on the curved surface** of the main body.
- Use **parametric calculations** to determine attachment coordinates, ensuring **smooth continuity**.
- The **handle profile** should start in a **workplane perpendicular** to the main body at the correct position.

### 2. Creating a Handle with a Curved Sweep
#### **Basic Approach (Sweep)**

```python
# Define attachment points along the outer surface of a cylindrical mug
outer_radius = 3.5  # Example mug outer radius
attachment_height_top = 5.0
attachment_height_bottom = 2.0

# Define the arc midpoint for a semicircular bend
arc_midpoint = (outer_radius + 1.5, 0, (attachment_height_top + attachment_height_bottom) / 2.0)

# Create a curved path using three-point arc in the XZ plane
handle_path = (
    cq.Workplane("XZ")
    .moveTo(outer_radius, attachment_height_top)
    .threePointArc(arc_midpoint, (outer_radius, attachment_height_bottom))
    .val()
)

# Create the circular handle profile at the start of the arc
handle_profile = cq.Workplane("XY", origin=(outer_radius, 0, attachment_height_top)).circle(0.5)

# Sweep the profile along the arc to create the handle
handle = handle_profile.sweep(handle_path)
```
Advantages: Uses a smooth arc to create a flush and continuous handle connection.

Common Issues:
   - Improper workplane orientation: The profile must be created on a workplane perpendicular to the sweep path.
   - Failed sweep operations: Ensure the arc is correctly defined and the path is a valid wire before sweeping.

### 3. Alternative Approach (Revolve for Stability)

If the sweep operation fails due to path complexity, an alternative is to use revolve:
```
def create_handle(body_radius, attachment_height, handle_radius=0.5):
    center_offset = 1.5  # Distance from body to handle's arc center
    handle_center = (-body_radius - center_offset, 0)

    # Revolve a circular profile to create a curved handle
    handle = (
        cq.Workplane("YZ", origin=(handle_center[0], 0, attachment_height))
           .circle(handle_radius)
           .revolve(180, (0, 0, 0), (0, 1, 0))  # Revolve 180° around Y-axis
    )
    
    return handle
```

Advantages:
- More stable than a sweep for handles with exact semicircular shapes.
- Avoids NCollection_Sequence errors caused by complex path sweeps.

### 4. Validating the Handle Attachment
After creating the handle, merge it with the main body:
```
mug = mug_body.union(handle)
```
- Verify the handle is properly attached:
- Check alignment using .translate() or workplane().transformed()
- Rotate if necessary to adjust the angle of attachment.
- Ensure endpoints sit flush on the body surface by aligning their positions.