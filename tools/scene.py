"""Route B: Blender 4.5, Cycles on the CPU, headless.
  blender -b -t 6 -P tools/scene.py -- out/leak.png [samples]
The daylight leak: a night meadow under stars; a round hole in the night sky shows daytime,
and a column of sunlight pours through it onto one patch of grass, where someone has set up
a beach umbrella and a towel."""
import bpy, math, sys
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "out/leak.png"
SAMPLES = int(argv[1]) if len(argv) > 1 else 96
SHAFT = float(argv[2]) if len(argv) > 2 else 0.0   # volume density of a visible sun shaft; 0 = none

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
sc.cycles.seed = 1
sc.render.threads_mode = "FIXED"
sc.render.threads = 6
sc.render.resolution_x = sc.render.resolution_y = 1024
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGB"
sc.view_settings.view_transform = "AgX"
try:
    sc.view_settings.look = "AgX - Punchy"
except Exception:
    pass


def mat(name, build):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    build(nt, out)
    return m


def principled(color, rough=0.8, emit=None, strength=0.0):
    def b(nt, out):
        p = nt.nodes.new("ShaderNodeBsdfPrincipled")
        p.inputs["Base Color"].default_value = (*color, 1)
        p.inputs["Roughness"].default_value = rough
        if emit:
            p.inputs["Emission Color"].default_value = (*emit, 1)
            p.inputs["Emission Strength"].default_value = strength
        nt.links.new(p.outputs[0], out.inputs[0])
    return b


def link_obj(obj):
    sc.collection.objects.link(obj)
    return obj


# ---------------- terrain: rolling meadow, computed heights ----------------
def height(x, y):
    h = 0.0
    h += 1.6 * math.sin(x * 0.045 + 0.6) * math.cos(y * 0.035)
    h += 0.7 * math.sin(x * 0.11 + y * 0.07)
    far = max(0.0, (y - 140) / 160)
    h += far * far * 22 * (0.6 + 0.4 * math.sin(x * 0.018 + 1.2))  # hills toward horizon
    return h


N = 260
SIZE_X, Y0, Y1 = 700.0, -40.0, 420.0
verts, faces = [], []
for j in range(N + 1):
    y = Y0 + (Y1 - Y0) * (j / N) ** 1.6
    for i in range(N + 1):
        x = -SIZE_X / 2 + SIZE_X * i / N
        verts.append((x, y, height(x, y)))
for j in range(N):
    for i in range(N):
        a = j * (N + 1) + i
        faces.append((a, a + 1, a + N + 2, a + N + 1))
me = bpy.data.meshes.new("meadow")
me.from_pydata(verts, [], faces)
me.update()
for p in me.polygons:
    p.use_smooth = True
ground = link_obj(bpy.data.objects.new("meadow", me))


def grass_mat(nt, out):
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    p.inputs["Roughness"].default_value = 0.95
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 0.35
    noise.inputs["Detail"].default_value = 8
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.04, 0.13, 0.025, 1)
    ramp.color_ramp.elements[1].color = (0.16, 0.40, 0.04, 1)
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], p.inputs["Base Color"])
    bump = nt.nodes.new("ShaderNodeBump")
    n2 = nt.nodes.new("ShaderNodeTexNoise")
    n2.inputs["Scale"].default_value = 9.0
    n2.inputs["Detail"].default_value = 4
    nt.links.new(tc.outputs["Object"], n2.inputs["Vector"])
    nt.links.new(n2.outputs["Fac"], bump.inputs["Height"])
    bump.inputs["Strength"].default_value = 0.6
    nt.links.new(bump.outputs["Normal"], p.inputs["Normal"])
    nt.links.new(p.outputs[0], out.inputs[0])


ground.data.materials.append(mat("grass", grass_mat))

# ---------------- camera ----------------
cam_d = bpy.data.cameras.new("cam")
cam_d.lens = 24
cam = link_obj(bpy.data.objects.new("cam", cam_d))
cam.location = (0, -18, 12.0)
target = Vector((0, 82, 17))
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
sc.camera = cam

# ---------------- the hole in the sky ----------------
SPOT = Vector((4.0, 30.0, height(4.0, 30.0)))       # where the sunlight lands
HOLE = Vector((-4.0, 100.0, 70.0))                   # centre of the hole in the night
R_HOLE = 16.0
axis = (SPOT - HOLE).normalized()


def hole_mat(nt, out):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    sky = nt.nodes.new("ShaderNodeValToRGB")
    sky.color_ramp.elements[0].color = (0.30, 0.62, 0.95, 1)   # low: pale
    sky.color_ramp.elements[1].color = (0.03, 0.20, 0.70, 1)   # high: deep blue
    nt.links.new(sep.outputs["Y"], sky.inputs["Fac"])
    cl = nt.nodes.new("ShaderNodeTexNoise")
    cl.inputs["Scale"].default_value = 2.2
    cl.inputs["Detail"].default_value = 6
    cl.inputs["Roughness"].default_value = 0.55
    nt.links.new(tc.outputs["Generated"], cl.inputs["Vector"])
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].position = 0.52
    cr.color_ramp.elements[1].position = 0.66
    nt.links.new(cl.outputs["Fac"], cr.inputs["Fac"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    nt.links.new(cr.outputs["Color"], mix.inputs["Factor"])
    nt.links.new(sky.outputs["Color"], mix.inputs[6])
    mix.inputs[7].default_value = (1.0, 0.99, 0.96, 1)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 0.75
    nt.links.new(mix.outputs[2], em.inputs["Color"])
    nt.links.new(em.outputs[0], out.inputs[0])


bpy.ops.mesh.primitive_circle_add(vertices=256, radius=R_HOLE, fill_type="NGON", location=HOLE)
disc = bpy.context.active_object
to_cam = (cam.location - HOLE).normalized()
disc.rotation_euler = to_cam.to_track_quat("Z", "Y").to_euler()
disc.data.materials.append(mat("daysky", hole_mat))
disc.visible_shadow = False

# sunlight through the hole: area light, disk shaped, narrow spread -> a column
ld = bpy.data.lights.new("sunleak", "AREA")
ld.shape = "DISK"
ld.size = 2 * R_HOLE * 0.9
ld.energy = 0.9e4
ld.color = (1.0, 0.93, 0.80)
ld.spread = math.radians(1.2)
light = link_obj(bpy.data.objects.new("sunleak", ld))
light.location = HOLE + axis * 1.5
light.rotation_euler = (-axis).to_track_quat("Z", "Y").to_euler()

# visible shaft: a volume cylinder along the column
length = (SPOT - HOLE).length
bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=R_HOLE * 1.25, depth=length,
                                    location=(HOLE + SPOT) / 2)
shaft = bpy.context.active_object
shaft.rotation_euler = axis.to_track_quat("Z", "Y").to_euler()


def vol(nt, out):
    v = nt.nodes.new("ShaderNodeVolumePrincipled")
    v.inputs["Density"].default_value = SHAFT
    v.inputs["Color"].default_value = (1, 0.97, 0.9, 1)
    nt.links.new(v.outputs[0], out.inputs["Volume"])


shaft.data.materials.append(mat("haze", vol))
shaft.visible_shadow = False
if SHAFT <= 0:
    bpy.data.objects.remove(shaft)

# ---------------- night sky (world) ----------------
w = bpy.data.worlds.new("night")
sc.world = w
w.use_nodes = True
nt = w.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
wo = nt.nodes.new("ShaderNodeOutputWorld")
tc = nt.nodes.new("ShaderNodeTexCoord")
sep = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(tc.outputs["Generated"], sep.inputs[0])
grad = nt.nodes.new("ShaderNodeValToRGB")
grad.color_ramp.elements[0].position = 0.0
grad.color_ramp.elements[0].color = (0.020, 0.035, 0.085, 1)   # horizon
grad.color_ramp.elements[1].position = 0.45
grad.color_ramp.elements[1].color = (0.002, 0.004, 0.016, 1)   # zenith
nt.links.new(sep.outputs["Z"], grad.inputs["Fac"])
vor = nt.nodes.new("ShaderNodeTexVoronoi")
vor.inputs["Scale"].default_value = 260
nt.links.new(tc.outputs["Generated"], vor.inputs["Vector"])
st = nt.nodes.new("ShaderNodeMapRange")
st.inputs["From Min"].default_value = 0.0
st.inputs["From Max"].default_value = 0.03
st.inputs["To Min"].default_value = 30.0
st.inputs["To Max"].default_value = 0.0
nt.links.new(vor.outputs["Distance"], st.inputs["Value"])
star_col = nt.nodes.new("ShaderNodeMix")
star_col.data_type = "RGBA"
star_col.blend_type = "ADD"
star_col.inputs["Factor"].default_value = 1.0
nt.links.new(grad.outputs["Color"], star_col.inputs[6])
mult = nt.nodes.new("ShaderNodeMath")
mult.operation = "MULTIPLY"
nt.links.new(st.outputs[0], mult.inputs[0])
# only some cells are stars
thr = nt.nodes.new("ShaderNodeMath")
thr.operation = "GREATER_THAN"
thr.inputs[1].default_value = 0.72
nt.links.new(vor.outputs["Color"], thr.inputs[0])
nt.links.new(thr.outputs[0], mult.inputs[1])
comb = nt.nodes.new("ShaderNodeCombineXYZ")
for k in ("X", "Y", "Z"):
    nt.links.new(mult.outputs[0], comb.inputs[k])
nt.links.new(comb.outputs[0], star_col.inputs[7])
# a faint Milky Way: a noisy band along one great circle of the sky
band_n = nt.nodes.new("ShaderNodeVectorMath")
band_n.operation = "DOT_PRODUCT"
nv = Vector((0.75, 0.15, 0.62)).normalized()
band_n.inputs[1].default_value = tuple(nv)
nt.links.new(tc.outputs["Generated"], band_n.inputs[0])
band_abs = nt.nodes.new("ShaderNodeMath")
band_abs.operation = "ABSOLUTE"
nt.links.new(band_n.outputs["Value"], band_abs.inputs[0])
band_w = nt.nodes.new("ShaderNodeMapRange")
band_w.inputs["From Min"].default_value = 0.0
band_w.inputs["From Max"].default_value = 0.22
band_w.inputs["To Min"].default_value = 1.0
band_w.inputs["To Max"].default_value = 0.0
nt.links.new(band_abs.outputs[0], band_w.inputs["Value"])
band_noise = nt.nodes.new("ShaderNodeTexNoise")
band_noise.inputs["Scale"].default_value = 5.0
band_noise.inputs["Detail"].default_value = 12
band_noise.inputs["Roughness"].default_value = 0.62
nt.links.new(tc.outputs["Generated"], band_noise.inputs["Vector"])
band_m = nt.nodes.new("ShaderNodeMath")
band_m.operation = "MULTIPLY"
nt.links.new(band_w.outputs[0], band_m.inputs[0])
band_pow = nt.nodes.new("ShaderNodeMath")
band_pow.operation = "POWER"
band_pow.inputs[1].default_value = 3.0
nt.links.new(band_noise.outputs["Fac"], band_pow.inputs[0])
nt.links.new(band_pow.outputs[0], band_m.inputs[1])
band_col = nt.nodes.new("ShaderNodeMix")
band_col.data_type = "RGBA"
band_col.blend_type = "MULTIPLY"
band_col.inputs["Factor"].default_value = 1.0
nt.links.new(band_m.outputs[0], band_col.inputs[6])
band_col.inputs[7].default_value = (0.16, 0.17, 0.26, 1)
sky_sum = nt.nodes.new("ShaderNodeMix")
sky_sum.data_type = "RGBA"
sky_sum.blend_type = "ADD"
sky_sum.inputs["Factor"].default_value = 1.0
nt.links.new(star_col.outputs[2], sky_sum.inputs[6])
nt.links.new(band_col.outputs[2], sky_sum.inputs[7])
# denser faint stars inside the band
vor2 = nt.nodes.new("ShaderNodeTexVoronoi")
vor2.inputs["Scale"].default_value = 700
nt.links.new(tc.outputs["Generated"], vor2.inputs["Vector"])
st2 = nt.nodes.new("ShaderNodeMapRange")
st2.inputs["From Min"].default_value = 0.0
st2.inputs["From Max"].default_value = 0.03
st2.inputs["To Min"].default_value = 6.0
st2.inputs["To Max"].default_value = 0.0
nt.links.new(vor2.outputs["Distance"], st2.inputs["Value"])
st2m = nt.nodes.new("ShaderNodeMath")
st2m.operation = "MULTIPLY"
nt.links.new(st2.outputs[0], st2m.inputs[0])
nt.links.new(band_w.outputs[0], st2m.inputs[1])
sky_sum2 = nt.nodes.new("ShaderNodeMix")
sky_sum2.data_type = "RGBA"
sky_sum2.blend_type = "ADD"
sky_sum2.inputs["Factor"].default_value = 1.0
nt.links.new(sky_sum.outputs[2], sky_sum2.inputs[6])
comb2 = nt.nodes.new("ShaderNodeCombineXYZ")
for k in ("X", "Y", "Z"):
    nt.links.new(st2m.outputs[0], comb2.inputs[k])
nt.links.new(comb2.outputs[0], sky_sum2.inputs[7])

bg = nt.nodes.new("ShaderNodeBackground")
bg.inputs["Strength"].default_value = 1.0
nt.links.new(sky_sum2.outputs[2], bg.inputs["Color"])
nt.links.new(bg.outputs[0], wo.inputs["Surface"])

# faint moonlight so the night land is not pure black
md = bpy.data.lights.new("moon", "SUN")
md.energy = 1.4
md.color = (0.55, 0.65, 1.0)
md.angle = math.radians(2)
moon = link_obj(bpy.data.objects.new("moon", md))
moon.rotation_euler = (math.radians(60), 0, math.radians(-140))

# ---------------- the beach: umbrella, towel, sunbather ----------------
def add(obj_fn, **kw):
    obj_fn(**kw)
    return bpy.context.active_object


gz = SPOT.z
U = SPOT + Vector((-2.2, 1.0, 0))
U.z = height(U.x, U.y)
pole = add(bpy.ops.mesh.primitive_cylinder_add, vertices=16, radius=0.035, depth=2.3,
           location=(U.x, U.y, U.z + 1.15))
pole.rotation_euler = (0, math.radians(-8), 0)
pole.data.materials.append(mat("pole", principled((0.9, 0.9, 0.88), 0.4)))
canopy = add(bpy.ops.mesh.primitive_cone_add, vertices=16, radius1=1.6, radius2=0.05,
             depth=0.55, location=(U.x + 0.16, U.y, U.z + 2.25))
canopy.rotation_euler = (0, math.radians(-8), 0)


def stripes(nt, out):
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    p.inputs["Roughness"].default_value = 0.6
    tc = nt.nodes.new("ShaderNodeTexCoord")
    gr = nt.nodes.new("ShaderNodeTexGradient")
    gr.gradient_type = "RADIAL"
    nt.links.new(tc.outputs["Object"], gr.inputs["Vector"])
    mth = nt.nodes.new("ShaderNodeMath")
    mth.operation = "MULTIPLY"
    mth.inputs[1].default_value = 6.0
    nt.links.new(gr.outputs["Fac"], mth.inputs[0])
    fr = nt.nodes.new("ShaderNodeMath")
    fr.operation = "FRACT"
    nt.links.new(mth.outputs[0], fr.inputs[0])
    gt = nt.nodes.new("ShaderNodeMath")
    gt.operation = "GREATER_THAN"
    gt.inputs[1].default_value = 0.5
    nt.links.new(fr.outputs[0], gt.inputs[0])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    nt.links.new(gt.outputs[0], mix.inputs["Factor"])
    mix.inputs[6].default_value = (0.85, 0.06, 0.04, 1)
    mix.inputs[7].default_value = (0.95, 0.93, 0.88, 1)
    nt.links.new(mix.outputs[2], p.inputs["Base Color"])
    nt.links.new(p.outputs[0], out.inputs[0])


canopy.data.materials.append(mat("canopy", stripes))
T = SPOT + Vector((0.6, -0.4, 0))
T.z = height(T.x, T.y)
towel = add(bpy.ops.mesh.primitive_cube_add, size=1, location=(T.x, T.y, T.z + 0.03))
towel.scale = (0.9, 2.0, 0.03)
towel.rotation_euler = (0, 0, math.radians(18))
towel.data.materials.append(mat("towel", principled((0.95, 0.75, 0.10), 0.9)))
skin = mat("skin", principled((0.75, 0.45, 0.30), 0.6))
suit = mat("suit", principled((0.05, 0.25, 0.75), 0.6))
body = add(bpy.ops.mesh.primitive_cylinder_add, vertices=16, radius=0.17, depth=1.15,
           location=(T.x, T.y, T.z + 0.2))
body.rotation_euler = (math.radians(90), 0, math.radians(18))
body.data.materials.append(skin)
trunk = add(bpy.ops.mesh.primitive_cylinder_add, vertices=16, radius=0.19, depth=0.4,
            location=(T.x, T.y, T.z + 0.21))
trunk.rotation_euler = (math.radians(90), 0, math.radians(18))
trunk.data.materials.append(suit)
d = Vector((-math.sin(math.radians(18)), math.cos(math.radians(18)), 0))
head = add(bpy.ops.mesh.primitive_uv_sphere_add, segments=24, ring_count=12, radius=0.14,
           location=(T.x + d.x * 0.72, T.y + d.y * 0.72, T.z + 0.22))
head.data.materials.append(skin)

# scale the whole beach set about its spot (the meadow has no other scale cue)
BEACH_SCALE = 2.4
pivot = link_obj(bpy.data.objects.new("beach", None))
pivot.location = SPOT
bpy.context.view_layer.update()
for ob in (pole, canopy, towel, body, trunk, head):
    mw = ob.matrix_world.copy()
    ob.parent = pivot
    ob.matrix_parent_inverse = pivot.matrix_world.inverted()
    ob.matrix_world = mw
pivot.scale = (BEACH_SCALE,) * 3

bpy.ops.object.select_all(action="DESELECT")
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("WROTE", OUT)
