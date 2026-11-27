# 鬼（自分）と隊士（敵）のモデルを Blender で作って GLB に書き出す
import bpy, bmesh, math, sys
from mathutils import Vector, Matrix
OUT = sys.argv[-1]
def lin(c): return ((c + .055) / 1.055) ** 2.4 if c > .04045 else c / 12.92
def rgb(h): return (lin((h >> 16 & 255) / 255), lin((h >> 8 & 255) / 255), lin((h & 255) / 255), 1)
def P(x, y, z): return Vector((x, -z, y))          # ゲームの座標（x右・y上・z手前）→ Blender
def newobj(bm, name='o'):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    if len(me.color_attributes): me.color_attributes.active_color = me.color_attributes[0]; me.color_attributes.render_color_index = 0
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); return o
def ell(c, r, seg=20):                              # だ円の球
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=1)
    bmesh.ops.scale(bm, vec=Vector((r[0], r[2], r[1])), verts=bm.verts); bmesh.ops.translate(bm, vec=P(*c), verts=bm.verts); return newobj(bm)
def limb(a, b, r1, r2, seg=16):                     # 2点をつなぐ、太さの変わる棒（両はしは丸い）
    A, B = P(*a), P(*b); d = B - A; L = d.length; bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r1, radius2=r2, depth=L)
    for c, r in ((-L / 2, r1), (L / 2, r2)):
        s = bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=8, radius=r); bmesh.ops.translate(bm, vec=Vector((0, 0, c)), verts=s['verts'])
    q = Vector((0, 0, 1)).rotation_difference(d.normalized()); bmesh.ops.rotate(bm, cent=Vector(), matrix=q.to_matrix(), verts=bm.verts)
    bmesh.ops.translate(bm, vec=(A + B) / 2, verts=bm.verts); return newobj(bm)
def chain(pts, r1, r2, n=14):                       # 曲がった角・髪・爪（点の列を太さを変えながらつなぐ）
    out = []; m = len(pts) - 1
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        def at(t):
            f = t * m; k = min(m - 1, int(f)); u = f - k; a, b = Vector(pts[k]), Vector(pts[k + 1]); return a.lerp(b, u)
        out.append(limb(tuple(at(t0)), tuple(at(t1)), r1 + (r2 - r1) * t0, r1 + (r2 - r1) * t1, 10))
    return out
def box(c, s, rot=None):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1); bmesh.ops.scale(bm, vec=Vector((s[0], s[2], s[1])), verts=bm.verts)
    if rot: bmesh.ops.rotate(bm, cent=Vector(), matrix=Matrix.Rotation(rot[1], 3, P(*rot[0]).normalized()), verts=bm.verts)
    bmesh.ops.translate(bm, vec=P(*c), verts=bm.verts); return newobj(bm)
def join(objs, name='j'):
    bm = bmesh.new()
    for o in objs:
        t = bmesh.new(); t.from_mesh(o.data); me = bpy.data.meshes.new('t'); t.to_mesh(me); t.free(); bm.from_mesh(me); bpy.data.meshes.remove(me)
    for o in objs: bpy.data.objects.remove(o, do_unlink=True)
    return newobj(bm, name)
def mods(o, fn):                                    # モディファイアをかけて確定する
    fn(o); dg = bpy.context.evaluated_depsgraph_get(); me = bpy.data.meshes.new_from_object(o.evaluated_get(dg)); old = o.data; o.modifiers.clear(); o.data = me; bpy.data.meshes.remove(old); return o
DEC = 1
def blob(objs, col, voxel=.014, smooth=4, dec=.35, name='b'):
    dec = dec * DEC   # 形をとかして1つのなめらかな形にし、色をぬる
    o = join(objs, name)
    def f(o):
        m = o.modifiers.new('r', 'REMESH'); m.mode = 'VOXEL'; m.voxel_size = voxel; m.use_smooth_shade = True
        if smooth: s = o.modifiers.new('s', 'SMOOTH'); s.factor = .6; s.iterations = smooth
        if dec < 1: d = o.modifiers.new('d', 'DECIMATE'); d.ratio = dec
    mods(o, f); paint(o, col); return o
def hard(objs, col, name='h'):                      # とかさずに、そのままの形で色をぬる（布・紙・刃）
    o = join(objs, name); paint(o, col); return o
def paint(o, col):
    me = o.data; a = me.color_attributes.new('Color', 'FLOAT_COLOR', 'CORNER'); c = rgb(col)
    for d in a.data: d.color = c
    for p in me.polygons: p.use_smooth = True
def mirror(o):                                      # 左右を反転した写し
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.scale(bm, vec=Vector((-1, 1, 1)), verts=bm.verts); bmesh.ops.reverse_faces(bm, faces=bm.faces); n = newobj(bm, o.name + 'm'); bpy.data.objects.remove(o, do_unlink=True)
    return n
def copycol(dst, src): pass
def node(name, parts):                              # 色つきの部品を1つにまとめて、関節の名前をつける
    bm = bmesh.new()
    for o in parts:
        bm.from_mesh(o.data)
    for o in parts: bpy.data.objects.remove(o, do_unlink=True)
    o = newobj(bm, name); o.data.name = name
    for p in o.data.polygons: p.use_smooth = True
    return o
def wrap(o, target, off=.004):
    def f(o): m = o.modifiers.new('w', 'SHRINKWRAP'); m.target = target; m.wrap_method = 'NEAREST_SURFACEPOINT'; m.wrap_mode = 'ABOVE_SURFACE'; m.offset = off
    return mods(o, f)
def ribbon(pts, w, sub=10):                         # 面にはりつける細い帯（もよう）
    bm = bmesh.new(); m = len(pts) - 1; rows = []
    for i in range(sub + 1):
        f = i / sub * m; k = min(m - 1, int(f)); u = f - k; p = Vector(pts[k]).lerp(Vector(pts[k + 1]), u); q = Vector(pts[min(m, k + 1)]) - Vector(pts[k]); side = Vector((0, 0, 1)).cross(Vector(P(*q))).normalized()
        ww = w * math.sin(math.pi * (i + .6) / (sub + 1.2)); c = P(*p); rows.append((bm.verts.new(c - side * ww), bm.verts.new(c + side * ww)))
    for i in range(sub): bm.faces.new((rows[i][0], rows[i][1], rows[i + 1][1], rows[i + 1][0]))
    return newobj(bm)
def ring(c, R, n, r, col_objs, tilt=0, squash=1):   # 玉をならべた輪（しめ縄・数珠・腕輪）
    for i in range(n):
        a = i / n * math.tau; x, z = math.cos(a) * R, math.sin(a) * R * squash; col_objs.append(ell((c[0] + x, c[1] + math.sin(a) * tilt, c[2] + z), (r[0], r[1] * (1.15 if i % 2 else .9), r[2]), 10))
SKIN, SKIN2, HAK, ROPE, WHITE, BONE, HAIR, TIP, BEAD, GOLD, RED, WRAP = 0x8f8a9c, 0x6f6a80, 0x1c121a, 0xd8c8a0, 0xf2efe6, 0xefe6cc, 0x17121c, 0xa8101e, 0x6a0c18, 0xc9a14a, 0x8a0f1c, 0xcfc6b4

def make_oni():
    global DEC; DEC = .42
    bpy.ops.wm.read_factory_settings(use_empty=True); N = []
    # --- 腰：袴の上・しめ縄・紙垂・前後のたれ布
    cloth = blob([ell((0, -.02, 0), (.21, .16, .17))], HAK, .016, 3, .3)
    rp = []; ring((0, .1, 0), .215, 18, (.05, .04, .045), rp, 0, .82); rp += [ell((0, .1, .2), (.07, .06, .06))] + chain([(-.05, .08, .22), (-.07, -.1, .25), (-.06, -.3, .24)], .028, .04, 6) + chain([(.05, .08, .22), (.08, -.12, .25), (.07, -.34, .25)], .028, .04, 6)
    rope = blob(rp, ROPE, .012, 2, .4)
    sh = []
    for sx in (-.15, .15):
        for k in range(3): sh.append(box((sx + (.03 if k % 2 else -.03) * (1 if sx > 0 else -1), .02 - k * .09, .16 + abs(sx) * .2), (.07, .1, .012), ((0, 0, 1), .5 if k % 2 else -.5)))
    paper = hard(sh, WHITE)
    fl = [box((0, -.26, -.16), (.2, .46, .02)), box((-.06, -.52, -.16), (.07, .1, .02), ((0, 0, 1), .5)), box((.05, -.5, -.16), (.08, .12, .02), ((0, 0, 1), -.4)), box((0, -.24, .18), (.24, .42, .02)), box((-.07, -.48, .18), (.09, .12, .02), ((0, 0, 1), -.5)), box((.06, -.5, .18), (.1, .14, .02), ((0, 0, 1), .45))]
    flap = hard(fl, RED)
    N.append(node('hips', [cloth, rope, paper, flap]))
    # --- 太もも：やぶれた袴
    def thigh():
        ps = [limb((0, .02, 0), (0, -.36, 0), .135, .17)]
        for i in range(7): a = i / 7 * math.tau; ps.append(limb((math.cos(a) * .13, -.36, math.sin(a) * .13), (math.cos(a) * .16, -.36 - (.07 + .05 * (i % 3)), math.sin(a) * .16), .05, .008, 8))
        return blob(ps, HAK, .014, 2, .3)
    N.append(node('thighR', [thigh()])); N.append(node('thighL', [mirror(thigh())]))
    # --- すね：筋肉のついた裸足・足首の縄・爪
    def shin():
        sk = blob([limb((0, -.02, 0), (0, -.38, 0), .08, .058), ell((0, -.15, .035), (.088, .14, .095)), ell((0, -.43, -.06), (.07, .05, .14)), ell((0, -.41, .03), (.055, .05, .06))], SKIN, .011, 3, .35)
        rp = []; ring((0, -.34, 0), .068, 9, (.022, .02, .022), rp); rope = blob(rp, ROPE, .008, 1, .4)
        cl = []
        for dx in (-.04, 0, .04): cl += chain([(dx, -.445, -.17), (dx * 1.3, -.45, -.24), (dx * 1.4, -.47, -.29)], .02, .003, 4)
        claw = blob(cl, BONE, .006, 1, .5); return [sk, rope, claw]
    N.append(node('shinR', shin())); N.append(node('shinL', [mirror(o) for o in shin()]))
    # --- 胴：筋肉の背中・胸、背中のもよう、数珠
    ps = [ell((0, .08, 0), (.165, .15, .12)), ell((0, .27, -.01), (.235, .19, .15)), ell((0, .5, .02), (.085, .1, .085))]
    for s in (-1, 1): ps += [ell((s * .175, .22, .05), (.1, .18, .095)), ell((s * .11, .44, .045), (.13, .075, .095)), ell((s * .275, .41, 0), (.12, .105, .115)), ell((s * .1, .3, -.125), (.115, .085, .06)), ell((s * .05, .22, .125), (.042, .21, .04)), ell((s * .125, .33, .12), (.085, .095, .04)), ell((s * .07, .1, -.105), (.055, .05, .03)), ell((s * .07, .0, -.1), (.05, .045, .028))]
    body = blob(ps, SKIN, .011, 4, .32, 'torsoB')
    mk = []
    for s in (-1, 1):
        for i in range(3): mk.append(ribbon([(s * .03, .12 + i * .1, .2), (s * .1, .15 + i * .1, .2), (s * .2, .26 + i * .1, .2)], .016 - i * .002))
        mk.append(ribbon([(s * .3, .5, .0), (s * .33, .4, .03), (s * .3, .3, .05)], .014))
    mark = join(mk, 'mk'); wrap(mark, body, .0035); paint(mark, 0xff2a3a)
    bd = []; ring((0, .475, .0), .15, 16, (.03, .03, .03), bd, .045, .85); bead = blob(bd, BEAD, .008, 1, .45)
    N.append(node('torso', [body, bead])); mark.name = 'torso_glow'; mark.data.name = 'torso_glow'; N.append(mark)
    # --- 頭：角・とがった耳・たてがみ
    hd = blob([ell((0, .1, 0), (.16, .18, .17)), ell((0, .02, -.04), (.12, .1, .125)), ell((0, -.06, .01), (.075, .1, .075)), ell((0, .09, -.15), (.04, .05, .05))] + chain([(.15, .1, 0), (.21, .13, .03), (.26, .17, .05)], .045, .006, 5) + chain([(-.15, .1, 0), (-.21, .13, .03), (-.26, .17, .05)], .045, .006, 5), SKIN, .011, 3, .35)
    hn = []
    for s in (-1, 1): hn += chain([(s * .085, .22, -.06), (s * .15, .34, -.1), (s * .2, .47, -.06), (s * .19, .58, .04), (s * .15, .64, .13)], .052, .006, 16)
    hn += chain([(0, .24, -.13), (0, .31, -.19), (0, .37, -.21)], .028, .004, 5)
    horn = blob(hn, BONE, .008, 2, .4)
    hr = [ell((0, .15, .06), (.175, .17, .16)), ell((0, .05, .12), (.15, .14, .1))]; tips = []
    import random; random.seed(7)
    for i in range(15):
        a = (i / 14 - .5) * 2.5; x0 = math.sin(a) * .15; ln = .14 + random.random() * .2; sw = (random.random() - .5) * .12
        p0 = (x0, .16 - abs(a) * .04, .12 + math.cos(a) * .06); p1 = (x0 * 1.5 + sw, -.02, .2 + math.cos(a) * .08); p2 = (x0 * 1.7 + sw * 2, -.02 - ln * .7, .24 + math.cos(a) * .06); p3 = (x0 * 1.6 + sw * 2.6, -.02 - ln, .2 + math.cos(a) * .1)
        hr += chain([p0, p1, p2], .06, .034, 7); tips += chain([p2, p3], .034, .004, 5)
    for i in range(7):
        a = (i / 6 - .5) * 2.2; hr += chain([(math.sin(a) * .13, .26, -.02 + (1 - abs(a)) * .0), (math.sin(a) * .2, .36 + (i % 2) * .05, .06), (math.sin(a) * .23, .42 + (i % 2) * .06, .16)], .05, .006, 6)
    hair = blob(hr, HAIR, .011, 2, .32); tip = blob(tips, TIP, .008, 1, .4)
    N.append(node('head', [hd, horn, hair, tip]))
    ey = hard([ell((.062, .115, -.15), (.034, .014, .02), 10), ell((-.062, .115, -.15), (.034, .014, .02), 10)], 0xff2030); ey.name = 'head_glow'; ey.data.name = 'head_glow'; N.append(ey)
    # --- 上腕：太い腕・金の腕輪
    def upper():
        sk = blob([limb((0, 0, 0), (0, -.27, 0), .085, .068), ell((0, -.12, -.025), (.088, .12, .088)), ell((0, -.1, .035), (.075, .12, .07))], SKIN, .011, 3, .35)
        g = []; ring((0, -.21, 0), .082, 10, (.026, .02, .026), g); gold = blob(g, GOLD, .008, 1, .45); return [sk, gold]
    N.append(node('upperR', upper())); N.append(node('upperL', [mirror(o) for o in upper()]))
    # --- 前腕と手：太い前腕・布の巻き・大きな爪の手
    def fore():
        sk = [limb((0, 0, 0), (0, -.24, 0), .074, .052), ell((0, -.07, 0), (.08, .1, .08)), ell((0, -.29, 0), (.062, .062, .042))]; cl = []
        for i, dx in enumerate((-.045, -.015, .015, .045)):
            sk += chain([(dx, -.32, 0), (dx * 1.1, -.38, -.015), (dx * 1.15, -.43, -.04)], .019, .015, 4); cl += chain([(dx * 1.15, -.43, -.04), (dx * 1.2, -.5, -.075), (dx * 1.2, -.56, -.13)], .016, .002, 6)
        sk += chain([(.06, -.28, -.01), (.09, -.33, -.03), (.1, -.37, -.06)], .02, .015, 3); cl += chain([(.1, -.37, -.06), (.11, -.42, -.1)], .015, .002, 4)
        skin = blob(sk, SKIN, .009, 2, .4); claw = blob(cl, BONE, .006, 1, .5)
        w = []; ring((0, -.2, 0), .054, 8, (.03, .022, .03), w); ring((0, -.16, 0), .058, 8, (.03, .022, .03), w); wr = blob(w, WRAP, .008, 1, .4); return [skin, claw, wr]
    N.append(node('foreR', fore())); N.append(node('foreL', [mirror(o) for o in fore()]))
    export(OUT + '/oni.glb'); print('oni tris', sum(len(o.data.polygons) for o in N))

UNI, HSK, BELT, KYA, HH, STEEL, TSUKA = 0x1b1b26, 0xf0c8a4, 0xf2f0ea, 0xd9d2bf, 0x2a1d18, 0xd4dbe6, 0x2a1d16
def make_kishi():
    global DEC; DEC = .16
    bpy.ops.wm.read_factory_settings(use_empty=True); N = []
    # 走りこんでくる隊士（正面はz手前）。左足を前、右手の刀をふりかぶる
    uni = [ell((0, .92, 0), (.17, .13, .135)), ell((0, 1.2, .03), (.19, .21, .14)), limb((-.1, .9, 0), (-.12, .52, .2), .1, .085), limb((.1, .9, 0), (.1, .54, -.1), .1, .085),
           limb((.21, 1.37, .03), (.34, 1.5, .12), .07, .06), limb((.34, 1.5, .12), (.3, 1.66, .2), .06, .05), limb((-.21, 1.37, .03), (-.3, 1.18, .2), .07, .06), limb((-.3, 1.18, .2), (-.2, 1.2, .36), .06, .05),
           ell((-.1, .08, .18), (.06, .05, .12)), ell((.1, .16, -.42), (.06, .05, .12))]
    u = blob(uni, UNI, .014, 3, .3)
    ky = blob([limb((-.12, .5, .2), (-.1, .13, .12), .074, .055), limb((.1, .52, -.1), (.1, .21, -.36), .074, .055)], KYA, .012, 2, .35)
    bl = []; ring((0, 1.03, .005), .175, 14, (.045, .03, .04), bl, 0, .78); belt = blob(bl, BELT, .01, 1, .4)
    sk = blob([ell((0, 1.56, .06), (.15, .165, .15)), ell((0, 1.42, .04), (.06, .07, .06)), ell((.3, 1.69, .21), (.05, .05, .05)), ell((-.19, 1.2, .38), (.05, .05, .05)), ell((.15, 1.56, .05), (.03, .045, .03)), ell((-.15, 1.56, .05), (.03, .045, .03))], HSK, .011, 3, .35)
    hr = [ell((0, 1.62, .03), (.165, .14, .16))]
    for i in range(9): a = (i / 8 - .5) * 2.4; hr += chain([(math.sin(a) * .13, 1.68, .13), (math.sin(a) * .15, 1.62 - (i % 2) * .02, .19), (math.sin(a) * .15, 1.55 + (i % 3) * .015, .2)], .05, .008, 5)
    for i in range(6): a = (i / 5 - .5) * 2.0; hr += chain([(math.sin(a) * .12, 1.7, -.06), (math.sin(a) * .18, 1.74, -.14), (math.sin(a) * .2, 1.7, -.22)], .05, .008, 5)
    hair = blob(hr, HH, .011, 2, .32)
    face = hard([ell((.055, 1.565, .195), (.03, .024, .012), 10), ell((-.055, 1.565, .195), (.03, .024, .012), 10)], 0xffffff)
    f2 = hard([ell((.055, 1.562, .204), (.014, .017, .008), 8), ell((-.055, 1.562, .204), (.014, .017, .008), 8), box((.055, 1.61, .2), (.07, .016, .012), ((0, 0, 1), .35)), box((-.055, 1.61, .2), (.07, .016, .012), ((0, 0, 1), -.35)), ell((0, 1.49, .19), (.04, .028, .012), 8)], 0x1a1014)
    N.append(node('body', [u, ky, belt, sk, hair, face, f2]))
    # 羽織（色は1体ごとに変える）：肩からの上着・広い袖・後ろへなびく裾
    ha = [ell((.1, 1.2, .02), (.14, .25, .17)), ell((-.1, 1.2, .02), (.14, .25, .17)), limb((.21, 1.38, .03), (.33, 1.49, .11), .1, .12), limb((-.21, 1.38, .03), (-.29, 1.2, .18), .1, .12)]
    for sx in (-.1, .1): ha += [box((sx, .95, -.2), (.2, .5, .03), ((1, 0, 0), .7)), box((sx * 1.2, .82, -.36), (.18, .3, .03), ((1, 0, 0), 1.05))]
    h = blob(ha, 0xffffff, .014, 3, .3); cut = h
    hn = node('haori', [h]); N.append(hn)
    # 刀（右手に持つ。斬りはらわれたら、これだけ飛ぶ）。原点は右手
    kt = [box((0, .52, 0), (.012, .96, .05)), box((0, 1.03, 0), (.012, .08, .03), ((1, 0, 0), .0))]; blade = hard(kt, STEEL)
    ts = hard([box((0, 0, 0), (.035, .26, .035))], TSUKA); tb = hard([box((0, .14, 0), (.03, .02, .11)), box((0, .14, 0), (.11, .02, .03))], GOLD)
    k = node('katana', [blade, ts, tb]); k.matrix_world = Matrix.Translation(P(.3, 1.69, .21)) @ Matrix.Rotation(-.55, 4, 'X') @ Matrix.Rotation(.25, 4, 'Y'); N.append(k)
    export(OUT + '/kishi.glb'); print('kishi tris', sum(len(o.data.polygons) for o in N))

def export(path):
    for o in bpy.context.scene.objects: o.select_set(True)
    kw = dict(filepath=path, export_format='GLB', export_apply=True, export_yup=True, export_normals=True, export_materials='NONE', export_animations=False)
    props = bpy.ops.export_scene.gltf.get_rna_type().properties.keys()
    if 'export_vertex_color' in props: kw['export_vertex_color'] = 'ACTIVE'
    if 'export_active_vertex_color_when_no_material' in props: kw['export_active_vertex_color_when_no_material'] = True
    if 'export_all_vertex_colors' in props: kw['export_all_vertex_colors'] = False
    bpy.ops.export_scene.gltf(**kw)
make_oni(); make_kishi()
