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

import os
from weakref import KeyedRef
import bpy
import base64
import bmesh
import time, datetime, array, functools, math
from . import vector3D
from . import swg_types
from . import vertex_buffer_format
from . import data_types
from . import export_flr
from . import export_msh
from . import export_lod
from . import support
from . import extents

from mathutils import Matrix, Vector, Color
from bpy_extras import io_utils, node_shader_utils

from bpy_extras.wm_utils.progress_report import (
    ProgressReport,
    ProgressReportSubstep,
)

def save(context,
         filepath,
         *,
         flip_uv_vertical=False,
         export_children=True,
         use_imported_crc=False
         ):
    collection = bpy.context.view_layer.active_layer_collection.collection
    if collection != None:
        dirname = os.path.dirname(filepath)
        fullpath = os.path.join(dirname, collection.name+".pob")
        extract_dir=context.preferences.addons[__package__].preferences.swg_root
        return export_one(fullpath, extract_dir, collection, flip_uv_vertical, export_children, use_imported_crc)
    else:
        print(f"You must have an active Collection export a POB!")
        return {'status':"ERROR", 'message':f"You must have an active Collection export a POB!"}

def export_one(fullpath, extract_dir, collection, flip_uv_vertical, export_children, use_imported_crc):
    root = os.path.dirname(os.path.dirname(fullpath))

    pobFile = swg_types.PobFile(fullpath)
    start = time.time()
    print(f'Exporting pob: {fullpath} Flip UV: {flip_uv_vertical}')

    if use_imported_crc:
        if 'crc' in collection:
            print(f"Using existing Crc: {collection['crc']}")
            pobFile.crc = collection['crc']
        else:
            print(f"Error! Asked to 'Use Imported Crc' but there is no 'crc' Custom Prop on main collection. Did you not import this POB from SWG?")
            return {'status':'ERROR', 'message': "Asked to 'Use Imported Crc' but there is no 'crc' Custom Prop on main collection. Did you not import this POB from SWG?"}

    
    #portalCol = None
    #pathgraphCol = None
    portalObjs = []
    cells = []
    center_by_cell={}
    avg_of_path_nodes={}
    
    for child in collection.children:
        cells.append(child)
        for grandchild in child.children:
            if grandchild.name.startswith("Portals_"):
                for obj in grandchild.objects:
                    if (obj not in portalObjs) and (obj.type == 'MESH'):
                        idtl = support.obj_to_idtl(obj)
                        pobFile.portals.append(swg_types.Portal(idtl.verts, idtl.indexes))
                        portalObjs.append(obj)

    portal_connections={}
    clockwise_by_portal={}

    if len(cells) > 0:
        for cell_id, cellCol in enumerate(cells): 
            referencePath = None
            floorFile = None
            flr=None
            flrObj=None
            lightDatas=[]
            collision = extents.NullExtents()
            thisCellsPortals=[]
            portalData=[]
            
            name=f'r{cell_id}'
            if cellCol.name != name:
                name = f'{name}_{cellCol.name}'                

            for child in cellCol.children:
                if child.name.startswith("Appearance_"):
                    referencePath = f'appearance/lod/{collection.name}_{name}.lod'
                    fullLodPath = f'{root}/{referencePath}'
                    center_by_cell[cell_id] = export_lod.avg_vert_position_in_blender(child)
                    if export_children:
                        result = export_as_lod(child, extract_dir, fullLodPath )
                elif child.name.startswith("Collision_"):
                    collision = support.create_extents_from_collection(child)
                elif child.name.startswith("Lights_"):
                    for obj in child.objects:
                        if obj.type == 'LIGHT':
                            lightData = support.swg_light_from_blender(obj)
                            if lightData != None:
                                lightDatas.append(lightData)
                            else:
                                print(f"Couldn't convert {obj.name} to light!")
                        else:
                            print(f"Warning! Non-light type child in Lights collection for {cellCol.name}")
                elif child.name.startswith("Portals_"):
                    # skip door hardpoints which are technically different objects in the portal collection
                    for obj in child.objects:
                        if obj.type != 'MESH':
                            continue
                        
                        if obj in portalObjs:                        
                            pid = get_global_portal_id(portalObjs, obj)
                            thisCellsPortals.append([obj, pid])
                            if not pid in portal_connections:
                                portal_connections[pid] = []
                            portal_connections[pid].append(cell_id)
                        else:
                            print(f"Error! Cell: {cellCol.name} Portal: {obj.name} is NOT in global Portals collection.")
                            return {'status':'ERROR', 'message': f"2Cell: {cellCol.name} Portal: {obj.name} is NOT in global Portals collection."}
 
                else:
                    print(f"Unhandled child collection for cell {name}: {child.name}")

            for child in cellCol.objects:
                if child.name.startswith("Appearance_"):
                    referencePath = f'appearance/mesh/{collection.name}_{name}_mesh_r{cell_id}.msh'
                    fullMshPath = f'{root}/{referencePath}'
                    center_by_cell[cell_id] = export_msh.avg_vert_position_in_blender(child)
                    if export_children:
                        result = export_as_msh(child, extract_dir, fullMshPath)
                elif child.name.startswith("Floor_"):
                    flrObj = child

            if flrObj != None:
                floorFile=f'appearance/collision/{collection.name}_{name}_collision_floor0.flr'
                passablePortals = [x for x in thisCellsPortals if is_portal_passable(x[0])]
                result, flr = export_flr.export_one(f'{root}/{floorFile}', flrObj, passablePortals, False)

                # After we export the flr, the pathgraph will have been updated properly, so find the avg location of its
                # nodes for our building pathgraph later
                position = Vector()
                if len(flr.pathGraph.nodes) > 0:
                    for node in flr.pathGraph.nodes:
                        position += Vector(node.position)
                    position = position / len(flr.pathGraph.nodes)

                avg_of_path_nodes[cell_id] = position                

                if 'FINISHED' not in result:
                    print(f"Error exporting floor for cell {cellCol.name}: {flrObj.name}")
                    return {'status':"ERROR", 'message':f"Error exporting floor for cell {cellCol.name}: {flrObj.name}"}
                else:
                    print(f'Wrote floor file: {str(flr)}')
                    for tri in flr.tris:
                        if tri.portalId1 != -1:
                            pid = thisCellsPortals[tri.portalId1][1]
                            if not pid in portal_connections:
                                portal_connections[pid] = []
                        elif tri.portalId2 != -1:
                            pid = thisCellsPortals[tri.portalId2][1]
                            if not pid in portal_connections:
                                portal_connections[pid] = []
                        elif tri.portalId3 != -1:
                            pid = thisCellsPortals[tri.portalId3][1]
                            if not pid in portal_connections:
                                portal_connections[pid] = []
            else:
                print(f"Error! cell {cell_id} ({cellCol.name}) has no floor!")
                return {'status':"ERROR", 'message':f"Error! cell {cell_id} ({cellCol.name}) has no floor!"}

            for portal in thisCellsPortals:
                for pi, portalObj in enumerate(portalObjs):
                    if portal[0] == portalObj:
                        if pi not in clockwise_by_portal:
                            clockwise_by_portal[pi] = cell_id

                        doorstyle = None
                        doorHp = None
                        children = support.getChildren(portalObj)
                        if len(children) == 1 and children[0].type == 'EMPTY' and children[0].empty_display_type == 'ARROWS':
                            ob = children[0]
                            doorstyle = ob['doorstyle']
                            doorHp = support.hardpoint_from_obj(ob)[0:12] # skip the last element, which is the hp name used for LODs
                            
                        portalData.append(swg_types.PortalData(pi, True, is_portal_passable(portalObj), -1, doorstyle, doorHp))

            cell = swg_types.Cell(cellCol.name, portalData, referencePath, floorFile, collision, lightDatas)
            pobFile.cells.append(cell)

    print(f"Processing connecting cells with portal_connections: {str(portal_connections)}")
    print(f"clockwise_by_portal: {clockwise_by_portal}")
    for cell_id, cell in enumerate(pobFile.cells):
        for portal in cell.portals:
            # print(f"Checking Cell: {cell_id} Portal: {portal.id}: ")
            # clockwise = determine_if_portal_points_into_cell(portalObjs[portal.id], center_by_cell[cell_id])
            for connecting_portal in portal_connections:
                if portal.id == connecting_portal:
                    if cell_id in portal_connections[portal.id]:
                        connected_cell=None
                        for other_cell in portal_connections[portal.id]:
                            if other_cell == cell_id:
                                continue
                            connected_cell = other_cell

            if connected_cell == None:
                print(f"Error. Can not find connecting room for Cell: {cell_id} Portal: {portal.id}")
                return {'status':"ERROR", 'message':f"Error. Can not find connecting room for Cell: {cell_id} Portal: {portal.id}"}
            else:
                portal.connecting_cell = connected_cell
                print(f"Cell: {cell_id} Portal: {portal.id} leads to cell: {portal.connecting_cell}!")

            portal.clockwise = True if clockwise_by_portal[portal.id] == cell_id else False

    buildingPathGraphIndex = 0
    buildingPathGraph = swg_types.PathGraph()
    node_by_portal={}
    for portal_id, portal in enumerate(pobFile.portals):
        total = Vector()
        for vert in portal.verts:
            total += Vector(vert)

        if len(portal.verts) > 0:
            total /= len(portal.verts)

        node = swg_types.PathGraphNode()
        node.type = 5

        for portalData in pobFile.cells[0].portals:
            if portal_id == portalData.id:
                node.type = 3
                break

        node.position = total
        node.index = buildingPathGraphIndex
        node.key = portal_id
        node.radius = 0
        buildingPathGraph.nodes.append(node)
        buildingPathGraphIndex += 1
        node_by_portal[portal_id] = node

    node_by_cell={}
    for cell_id, cell in enumerate(pobFile.cells):
        node = swg_types.PathGraphNode()
        node.type = 4
        node.position = avg_of_path_nodes[cell_id]
        node.index = buildingPathGraphIndex
        node.key = cell_id
        node.radius = 0
        buildingPathGraph.nodes.append(node)
        buildingPathGraphIndex += 1
        node_by_cell[cell_id] = node

        for portalData in cell.portals:
            edge = swg_types.PathGraphEdge()
            edge.indexA = node_by_cell[cell_id].index
            edge.indexB = node_by_portal[portalData.id].index
            buildingPathGraph.edges.append(edge)

            edge2 = swg_types.PathGraphEdge()
            edge2.indexA = node_by_portal[portalData.id].index
            edge2.indexB = node_by_cell[cell_id].index
            buildingPathGraph.edges.append(edge2)

    pobFile.pathGraph = buildingPathGraph
    
    pobFile.write(fullpath)
    now = time.time()
    print(f"Successfully wrote: {fullpath} Duration: " + str(datetime.timedelta(seconds=(now-start))))
    return {'status':'FINISHED'}

def export_as_lod(collection, extract_dir, path):
    return export_lod.export_one(path, extract_dir, collection, True, True)

def export_as_msh(child, extract_dir, path):
    return export_msh.export_one(path, extract_dir, child, True)

def determine_if_portal_points_into_cell(portalObj, flrObj, testVertindex):
    poralMesh = portalObj.to_mesh() 
    face = poralMesh.polygons[0]  
    norm = face.normal
    pointOnPortal = poralMesh.vertices[0].co

    floorTriMesh = flrObj.to_mesh()
    pointOnFloorTri = floorTriMesh.vertices[testVertindex].co

    vec = pointOnFloorTri - pointOnPortal
    dot = vec.dot(norm)
    #print(f" pointOnPortal: {pointOnPortal}  Normal: {norm} pointOnFloorTri: {pointOnFloorTri} Dot: {dot}")
    return dot > 0

def get_global_portal_id(portalObjs, portal):
    for pid, p in enumerate(portalObjs):
        if portal == p:
            return pid
    return None

def is_portal_passable(obj):
    if obj.type != 'MESH':
        return False
    elif 'passable' in obj:
        return obj['passable'] == True
    else:
        return True