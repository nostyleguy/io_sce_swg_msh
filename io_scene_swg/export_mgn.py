# MIT License
#
# Copyright (c) 2022 Nick Rafalski
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import bpy, collections, array, base64, time, datetime, bmesh
from bpy.props import *
from . import swg_types
from . import data_types

oznfulllist = ['face','neck','skull','sideburn_l','sideburn_r','chest','torso_f','torso_b','waist_f','waist_b','r_thigh','r_shin','r_foot','l_thigh','l_shin','l_foot','r_arm','r_forearm','r_hand','l_arm','l_forearm','l_hand']
        
def mesh_triangulate(me):
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()

def export_mgn(context, 
               filepath, 
               *,
               do_tangents = True):    
    starttime = time.time()

    current_obj = None
    objects = context.selected_objects

    if not (len(objects) == 1):
        return {'ERROR'}

    for ob_main in objects:
        obs = [(ob_main, ob_main.matrix_world)]
        for ob, ob_mat in obs:
            if ob.type != 'MESH':
                return False
            else:
                current_obj = ob
                
    bm = current_obj.to_mesh() 
    mesh_triangulate(bm)
    
    bm.calc_normals_split()

    t_ln = array.array(data_types.ARRAY_FLOAT64, (0.0,)) * len(bm.loops) * 3
    bm.loops.foreach_get("normal", t_ln)
    normals = list(map(list, zip(*[iter(t_ln)]*3)))    
    
    if do_tangents:
        t_ln = array.array(data_types.ARRAY_FLOAT64, [0.0,]) * len(bm.loops) * 3
        uv_names = [uvlayer.name for uvlayer in bm.uv_layers]
        for name in uv_names:
            print(f"Did tangents for UV map: {name}")
            bm.calc_tangents(uvmap=name)

    mgn = swg_types.SWGMgn(filepath)

    i = 0
    for key in current_obj.keys():
        if key.startswith("SKTM_"):
            mgn.skeletons.append(current_obj[key])
        elif key == "OCC_LAYER":
            mgn.occlusion_layer = current_obj[key]
        elif key == "HPTS":
            hpts_bytes = base64.b64decode(current_obj["HPTS"])
            mgn.binary_hardpoints = hpts_bytes
        elif key == "TRTS":
            trts_bytes = base64.b64decode(current_obj["TRTS"])
            mgn.binary_trts = trts_bytes
        else:
            mgn.occlusions.append([key, i, current_obj[key]])
            i += 1

    for vert in bm.vertices:
        mgn.positions.append([-vert.co[0],vert.co[2],-vert.co[1]])

    for normal in normals:
        mgn.normals.append([-normal[0], normal[2], -normal[1]])

    if do_tangents:
        mgn.dot3=[]
        for i, loop in enumerate(bm.loops):
            tang = loop.tangent
            mgn.dot3.append([ -tang[0], tang[2], -tang[1], loop.bitangent_sign])

    twhd = []
    twdt = []
    for keys in bpy.data.shape_keys:
        if keys == bm.shape_keys:
            for key in keys.key_blocks[1:]:

                blt = swg_types.SWGBLendShape()
                blt.name = key.name
                blt.dot3 = []
                basis = keys.key_blocks[0].data
                for j, kv in enumerate(key.data):
                    delta = kv.co - basis[j].co
                    #if delta[0] != 0 and delta[1] != 0 and delta[2] != 0:
                    blt.positions.append([j, [-delta[0], delta[2], -delta[1]]])
                    blt.normals.append([j, [0,0,0]])
                    if do_tangents:
                        blt.dot3.append([j, [0,0,0]])
                mgn.blends.append(blt)
            
    face_index_pairs = [(face, index) for index, face in enumerate(bm.polygons)]
    faces_by_material = {}
    for f, f_index in face_index_pairs:
        if not f.material_index in faces_by_material:
            faces_by_material[f.material_index] = []   
        faces_by_material[f.material_index].append(f)

    uv_layer = bm.uv_layers.active.data[:]
    for material_index in faces_by_material:
        last_tri_index = None
        running_tri_index = 0
        faces = faces_by_material[material_index]
        psdt = swg_types.SWGPerShaderData()
        psdt.name = current_obj.material_slots[material_index].material.name
        mgn.psdts.append(psdt)

        reverse_position_lookup={}
        pidx_id = 0
        psdt.prims.append([])
        psdt.uvs.append([])
        psdt.dot3 = []
        
        for f in faces:
            t1=None
            t2=None
            t3=None
            for uv_index, l_index in enumerate(f.loop_indices):
                master_vert_id = f.vertices[uv_index]

                if not master_vert_id in reverse_position_lookup:
                    reverse_position_lookup[master_vert_id] =  pidx_id                    
                    pidx_id += 1

                psdt.pidx.append(master_vert_id)
                psdt.nidx.append(l_index)
                psdt.uvs[0].append(uv_layer[l_index].uv)

                if do_tangents:
                    psdt.dot3.append(l_index)
                
                if last_tri_index == None:
                    last_tri_index = l_index
                    print(f"Starting last_tri_index at {last_tri_index}")
                    
                if t1 == None:
                    t1 = running_tri_index
                elif t2 == None:
                    t2 = running_tri_index
                else:
                    t3 = running_tri_index
                    psdt.prims[0].append(t3)
                    psdt.prims[0].append(t2)
                    psdt.prims[0].append(t1)

                running_tri_index += 1

    vertex_groups = current_obj.vertex_groups
    bone_names = vertex_groups.keys()
    twdtdata = {}
    for name in bone_names:
        mgn.bone_names.append(name)
        selverts = [v for v in bm.vertices]
        indexval = current_obj.vertex_groups[name].index
        for v in selverts:
            for n in v.groups:
                if n.group == indexval:
                    if not v.index in twdtdata:
                        twdtdata[v.index] = []
                    twdtdata[v.index].append([indexval, n.weight])
    od = collections.OrderedDict(sorted(twdtdata.items()))
    mgn.twdt = list(od.values())

    print(f"Assembling final IFF ... ")
    mgn.write()
    now = time.time()        
    print(f"Successfully wrote: {filepath} Duration: " + str(datetime.timedelta(seconds=(now-starttime))))
    return {'FINISHED'}