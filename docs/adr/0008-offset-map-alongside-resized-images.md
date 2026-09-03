---
status: accepted
---

# Image tensors may be resized, but each carries an explicit byte-offset map

Grad-CAM attribution only means anything if a heatmap region can be traced back to a file
region, and resizing a variable-height byte matrix to a fixed input shape destroys that
correspondence unless it is recorded. Rather than forcing a fixed reshape — which would
truncate megabyte-scale files to their first 50KB or so and discard most of every sample — we
resize as needed and persist, alongside each cached image tensor, the map from image
coordinates to source byte offsets.

## Consequences

Attribution granularity is coarse for large files: one output pixel may average tens of bytes
across several source rows. That coarseness is stated when reporting FR6 rather than hidden
behind a confident-looking overlay. The map is part of the cache contract — a cached image
tensor without its offset map is invalid, and is regenerated rather than patched.
