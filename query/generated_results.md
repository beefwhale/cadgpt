###    produce me a simple gear
```
import cadquery as cq
from math import sin, cos, pi, floor
# define the generating function
def hypocycloid(t, r1, r2):
    return (
        (r1 - r2) * cos(t) + r2 * cos(r1 / r2 * t - t),
        (r1 - r2) * sin(t) + r2 * sin(-(r1 / r2 * t - t)),
    )
def epicycloid(t, r1, r2):
    return (
        (r1 + r2) * cos(t) - r2 * cos(r1 / r2 * t + t),
        (r1 + r2) * sin(t) - r2 * sin(r1 / r2 * t + t),
    )
def gear(t, r1=4, r2=1):
    if (-1) ** (1 + floor(t / 2 / pi * (r1 / r2))) < 0:
        return epicycloid(t, r1, r2)
    else:
        return hypocycloid(t, r1, r2)
# create the gear profile and extrude it
result = (
    cq.Workplane("XY")
    .parametricCurve(lambda t: gear(t * 2 * pi, 6, 1))
    .twistExtrude(15, 90)
)

display(result)
```
###    produce me a simple worm gear   
``` 
import cadquery as cq
from math import sin, cos, pi, floor

def hypocycloid(t, r1, r2):
  return (
    (r1 - r2) * cos(t) + r2 * cos(r1 / r2 * t - t),
    (r1 - r2) * sin(t) + r2 * sin(-(r1 / r2 * t - t)),
  )

def epicycloid(t, r1, r2):
  return (
    (r1 + r2) * cos(t) - r2 * cos(r1 / r2 * t + t),
    (r1 + r2) * sin(t) - r2 * sin(r1 / r2 * t + t),
  )

def gear(t, r1=4, r2=1):
  if (-1) ** (1 + floor(t / 2 / pi * (r1 / r2))) < 0:
    return epicycloid(t, r1, r2)
  else:
    return hypocycloid(t, r1, r2)

result = (
  cq.Workplane("XY")
  .parametricCurve(lambda t: gear(t * 2 * pi, 6, 1))
  .twistExtrude(15, 90)
  .faces(">Z")
  .workplane()
  .circle(2)
  .cutThruAll()
)

display(result)
```

##    produce me a simple hexagonal tube that is 5cm long and 5cm in radius. remove a hole in the middle, 2cm in radius through the tube.
```
import cadquery as cq
radius = 5
tube_length = 5
hole_radius = 2
result = cq.Workplane("XY").polygon(6, radius).extrude(tube_length)
result = result.faces(">Z").workplane().circle(hole_radius).cutThruAll()

display(result)
```

## produce me a simple hexagonal tube that is 2cm long and 5cm in radius. 
## remove a hole in the middle, 1cm in radius through the tube.
```
import cadquery as cq

radius = 5
length = 2
hole_radius = 1

result = cq.Workplane("XY").polygon(6, radius).extrude(length)
result = result.faces("<Z").workplane().circle(hole_radius).cutThruAll()

display(result)
```