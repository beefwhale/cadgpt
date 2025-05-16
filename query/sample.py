import cadquery as cq

height = 60.0
width = 80.0
thickness = 10.0
diameter = 3  # 3 inches
length = 5  # 5 inches
padding = 12.0

result = (
    cq.Workplane("XY")
    .box(height, width, length)
    .faces("Z")
    .workplane()
    .hole(diameter)
)