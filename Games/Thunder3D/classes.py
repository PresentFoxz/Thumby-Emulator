import micropython
import random
import library as lib
from math import *

DEADZONE = 1 << 4

cW = lib.w_Half << lib.FIXED_BITS
cH = lib.h_Half << lib.FIXED_BITS

sprtID = 0
triID  = 0

transformed = [None] * (lib.MAX_TRIS * 3)
projected   = [None] * (lib.MAX_TRIS * 3)

yaw, pitch = None, None
sinY, cosY, sinX, cosX = None, None, None, None

class Entities:
    def __init__(self, x, y, z, rx, ry, rz, sx, sy, sz, idx):
        self.pos  = [x, y, z]
        self.rot  = [rx, ry, rz]
        self.size = [sx, sy, sz]
        self.idx  = idx

class Camera:
    def __init__(self, x, y, z, rx, ry, rz, near, far, acc, frict, fov):
        self.x = lib.FMath.TO_FIXED_BITS(x)
        self.y = lib.FMath.TO_FIXED_BITS(y)
        self.z = lib.FMath.TO_FIXED_BITS(z)
        
        self.rx = lib.FMath.TO_FIXED_BITS(rx)
        self.ry = lib.FMath.TO_FIXED_BITS(ry)
        self.rz = lib.FMath.TO_FIXED_BITS(rz)
        
        self.xVel = lib.FMath.TO_FIXED_BITS(0.0)
        self.yVel = lib.FMath.TO_FIXED_BITS(0.0)
        self.zVel = lib.FMath.TO_FIXED_BITS(0.0)
        
        self.acc   = lib.FMath.TO_FIXED_BITS(acc)
        self.frict = lib.FMath.TO_FIXED_BITS(frict)
        self.fov   = lib.FMath.TO_FIXED_BITS(fov)
        
        self.near = lib.FMath.TO_FIXED_BITS(near)
        self.far  = lib.FMath.TO_FIXED_BITS(far)
        
        self.rot_x = lib.FMath.TO_FIXED_BITS(1.2)
        self.rot_y = lib.FMath.TO_FIXED_BITS(1.2)
        
        self.norm_x = lib.FMath.TO_FIXED_BITS(0.0)
        self.norm_y = lib.FMath.TO_FIXED_BITS(0.0)
        self.norm_z = lib.FMath.TO_FIXED_BITS(1.0)
    
    @micropython.native
    def updateFunctions(self):
        global yaw, pitch, sinY, cosY, sinX, cosX
        yaw = lib.FMath.angle_to_index(self.ry)
        pitch = lib.FMath.angle_to_index(self.rx)
        
        sinY, cosY = lib.FMath.FIXED_SIN(yaw), lib.FMath.FIXED_COS(yaw)
        sinX, cosX = lib.FMath.FIXED_SIN(pitch), lib.FMath.FIXED_COS(pitch)
        
        self.norm_x = lib.FMath.FIXED_MUL(sinY, cosX)
        self.norm_y = -sinX
        self.norm_z = lib.FMath.FIXED_MUL(cosY, cosX)
    
    @micropython.native
    def movement(self, btn):
        yaw = lib.FMath.angle_to_index(self.ry)
        sinY = lib.FMath.FIXED_SIN(yaw)
        cosY = lib.FMath.FIXED_COS(yaw)
        
        if btn.buttonA.pressed():
            if btn.buttonU.pressed(): self.yVel += self.acc
            if btn.buttonD.pressed(): self.yVel -= self.acc
        else:
            if btn.buttonB.pressed():
                if btn.buttonU.pressed(): self.rx += self.rot_x
                if btn.buttonD.pressed(): self.rx -= self.rot_x
                
                if btn.buttonL.pressed(): self.ry -= self.rot_y
                if btn.buttonR.pressed(): self.ry += self.rot_y
            else:
                if btn.buttonU.pressed():
                    self.xVel += lib.FMath.FIXED_MUL(self.acc, sinY)
                    self.zVel += lib.FMath.FIXED_MUL(self.acc, cosY)
                if btn.buttonD.pressed():
                    self.xVel -= lib.FMath.FIXED_MUL(self.acc, sinY)
                    self.zVel -= lib.FMath.FIXED_MUL(self.acc, cosY)
                
                if btn.buttonL.pressed():
                    self.xVel -= lib.FMath.FIXED_MUL(self.acc, cosY)
                    self.zVel += lib.FMath.FIXED_MUL(self.acc, sinY)
                if btn.buttonR.pressed():
                    self.xVel += lib.FMath.FIXED_MUL(self.acc, cosY)
                    self.zVel -= lib.FMath.FIXED_MUL(self.acc, sinY)
        
        self.xVel = lib.FMath.FIXED_MUL(self.xVel, self.frict)
        self.yVel = lib.FMath.FIXED_MUL(self.yVel, self.frict)
        self.zVel = lib.FMath.FIXED_MUL(self.zVel, self.frict)
        
        if -DEADZONE < self.xVel < DEADZONE: self.xVel = 0
        if -DEADZONE < self.yVel < DEADZONE: self.yVel = 0
        if -DEADZONE < self.zVel < DEADZONE: self.zVel = 0
        
        self.x += self.xVel
        self.y += self.yVel
        self.z += self.zVel

class Render:
    @staticmethod
    @micropython.native
    def worldToCam(cx, cy, cz, vx, vy, vz, sinX, sinY, cosX, cosY):
        nx = vx - cx
        ny = vy - cy
        nz = vz - cz
        
        dz = (lib.FMath.FIXED_MUL(sinY, nx) + lib.FMath.FIXED_MUL(cosY, nz))
        dx = int(lib.FMath.FIXED_MUL(cosY, nx) - lib.FMath.FIXED_MUL(sinY, nz))
        dy = int(lib.FMath.FIXED_MUL(cosX, ny) - lib.FMath.FIXED_MUL(sinX, dz))
        dz2 = int(lib.FMath.FIXED_MUL(sinX, ny) + lib.FMath.FIXED_MUL(cosX, dz))
        
        return dx, -dy, dz2
    
    @staticmethod
    @micropython.native
    def projectPoint(r, mX, mY, fov, near, far):
        x, y, z = r
    
        if z <= near or z >= far: return None
        if z == 0: z = 1
            
        x2D = lib.FMath.FIXED_DIV(x, z)
        y2D = lib.FMath.FIXED_DIV(y, z)
        
        x2D = lib.FMath.FIXED_MUL(x2D, fov) + mX
        y2D = lib.FMath.FIXED_MUL(y2D, fov) + mY
        
        return x2D >> lib.FIXED_BITS, y2D >> lib.FIXED_BITS
    
    @staticmethod
    @micropython.native
    def insertion_sort(depths, count):
        for i in range(1, count):
            key = depths[i][:]
            if (key[1] == -1): continue
            
            j = i - 1
            while j >= 0 and depths[j][0] < key[0]:
                depths[j + 1] = depths[j]
                j -= 1
    
            depths[j + 1] = key
    
    @micropython.viper
    def h_dither_line(y:int, x_start:int, x_end:int, color:int):
        height = int(lib.height)
        width  = int(lib.width)
    
        if y < 0 or y >= height: return
        if x_start < 0: x_start = 0
        if x_end > width: x_end = width
        if x_start >= x_end: return
    
        buf = ptr8(lib.buf)
        bayer = ptr8(lib.BAYER4x4_FLAT)
    
        page = y >> 3
        bit  = y & 7
        mask = 1 << bit
        inv  = 255 - mask
        row  = page * width
        
        color_scaled:int = (color * 16) // 3
        yb:int = (y & 3) << 2
    
        for x in range(x_start, x_end):
            idx:int = row + x
            threshold:int = bayer[yb + (x & 3)]
    
            if color_scaled > threshold: buf[idx] = buf[idx] | mask
            else: buf[idx] = buf[idx] & inv
    
    @staticmethod
    @micropython.viper
    def h_line(y:int, x_start:int, x_end:int, color:int):
        height = int(lib.height)
        width  = int(lib.width)
    
        if y < 0 or y >= height: return
    
        if x_start < 0: x_start = 0
        if x_end > width: x_end = width
        if x_start >= x_end: return
    
        page = y >> 3
        bit  = y & 7
        mask = 1 << bit
        row  = page * width
    
        buf = ptr8(lib.buf)
        inv = 255 - mask
        
        for x in range(x_start, x_end):
            if color: buf[row + x] |= mask
            else: buf[row + x] &= inv
    
    @staticmethod
    @micropython.native
    def plotPixel(x, y, color):
        if x < 0 or x >= lib.width or y < 0 or y >= lib.height: return
    
        page = (y >> 3) * lib.width
        idx = page + x
        mask = 1 << (y & 7)
    
        lib.buf[idx] |= mask
    
    @staticmethod
    @micropython.native
    def fill(color):
        start = lib.interlace
        for y in range(start, lib.height, 2):
            Render.h_line(y, 0, lib.width, color)
    
    @staticmethod
    @micropython.native
    def fillRect(x, y, w, h, color):
        xWidth = x + w
        for yPos in range(y, (y + h)):
            if (yPos & 1) != lib.interlace: continue
            Render.h_line(yPos, x, xWidth, color)
    
    @staticmethod
    @micropython.viper
    def checkRend(x0:int, y0:int, x1:int, y1:int, x2:int, y2:int) -> int:
        minX:int = x0
        maxX:int = x0
        minY:int = y0
        maxY:int = y0
        
        if x1 < minX: minX = x1
        if x2 < minX: minX = x2
        if x1 > maxX: maxX = x1
        if x2 > maxX: maxX = x2
        if y1 < minY: minY = y1
        if y2 < minY: minY = y2
        if y1 > maxY: maxY = y1
        if y2 > maxY: maxY = y2
        
        width:int  = int(lib.width)
        height:int = int(lib.height)
        
        if maxX < 0 or minX >= width or maxY < 0 or minY >= height: return 1
        return 0
    
    @staticmethod
    @micropython.native
    def directVerts(pos, cam, verts_out, color_out, depth_out, count, tris_data, normals, colors):
        global triID, cosX, cW, cH, sinY, cosY, sinX, cosX, forwardX, forwardY, forwardZ
        cCount = -1
        
        cx, cy, cz = cam.x, cam.y, cam.z
        fov, near, far = cam.fov, cam.near, cam.far
        
        vP0, vP1, vP2 = lib.FMath.TO_FIXED_BITS(pos[0]), lib.FMath.TO_FIXED_BITS(pos[1]), lib.FMath.TO_FIXED_BITS(pos[2])
        for triIDX, tri in enumerate(tris_data):
            if triID >= lib.MAX_TRIS: break
            v0, v1, v2 = tri
            
            r0 = Render.worldToCam(cx, cy, cz, v0[0] + vP0, v0[1] + vP1, v0[2] + vP2, sinX, sinY, cosX, cosY)
            r1 = Render.worldToCam(cx, cy, cz, v1[0] + vP0, v1[1] + vP1, v1[2] + vP2, sinX, sinY, cosX, cosY)
            r2 = Render.worldToCam(cx, cy, cz, v2[0] + vP0, v2[1] + vP1, v2[2] + vP2, sinX, sinY, cosX, cosY)
            if r0 is None or r1 is None or r2 is None: continue
            
            nx, ny, nz = normals[triIDX]
            dot = (lib.FMath.FIXED_MUL(nx, cam.norm_x) + lib.FMath.FIXED_MUL(ny, cam.norm_y) + lib.FMath.FIXED_MUL(nz, cam.norm_z))
            if dot > 0: continue
            
            p0 = Render.projectPoint(r0, cW, cH, fov, near, far)
            p1 = Render.projectPoint(r1, cW, cH, fov, near, far)
            p2 = Render.projectPoint(r2, cW, cH, fov, near, far)
            if p0 is None or p1 is None or p2 is None: continue
    
            if Render.checkRend(*p0, *p1, *p2) != 0: continue
    
            cCount += 1
            verts_out[triID] = [p0[0], p0[1], p1[0], p1[1], p2[0], p2[1]]
            color_out[triID] = colors[triIDX]
            depth_out[cCount + count] = [int((r0[2] + r1[2] + r2[2]) // 3), 0, triID]
            triID += 1
    
        return cCount
    
    @staticmethod
    @micropython.native
    def setupSprite(pos, size, cam, sprite, sprt_out, depth_out, count):
        global sprtID, sinY, cosY, sinX, cosX, cW, cH
        if count >= lib.MAX_TRIS: return 0
        
        vP0, vP1, vP2 = lib.FMath.TO_FIXED_BITS(pos[0]), lib.FMath.TO_FIXED_BITS(pos[1]), lib.FMath.TO_FIXED_BITS(pos[2])
        
        r = Render.worldToCam(cam.x, cam.y, cam.z, vP0, vP1, vP2, sinX, sinY, cosX, cosY)
        if r is None: return 0
        
        p = Render.projectPoint(r, cW, cH, cam.fov, cam.near, cam.far)
        if p is None: return 0
        
        if p[0] < 0 or p[0] >= lib.width: return 0
        if p[1] < 0 or p[1] >= lib.height: return 0
    
        sprt_out[sprtID]  = [int(p[0]), int(p[1])]
        depth_out[count] = [int(r[2]), 1, sprtID]
        sprtID += 1
        
        return 1
    
    @staticmethod
    @micropython.native
    def customTri(x0, y0, x1, y1, x2, y2, color, fill):
        if y1 < y0: x0, y0, x1, y1 = x1, y1, x0, y0
        if y2 < y0: x0, y0, x2, y2 = x2, y2, x0, y0
        if y2 < y1: x1, y1, x2, y2 = x2, y2, x1, y1
    
        if y0 == y2: return
    
        FP = 8
        scale = 1 << FP
    
        dy02 = y2 - y0
        dy01 = y1 - y0
        dy12 = y2 - y1
    
        dx02 = (x2 - x0) * scale // dy02 if dy02 != 0 else 0
        dx01 = (x1 - x0) * scale // dy01 if dy01 != 0 else 0
        dx12 = (x2 - x1) * scale // dy12 if dy12 != 0 else 0
    
        interlace = lib.interlace
        xA = x0 * scale
        xB = x0 * scale
    
        y = y0
        while y < y1:
            if 0 <= y < lib.height and (y & 1) == interlace:
                xa = xA >> FP
                xb = xB >> FP
                if xa > xb: xa, xb = xb, xa
    
                if fill:
                    Render.h_dither_line(y, xa, xb + 1, color)
                else:
                    Render.plotPixel(xa, y, color)
                    Render.plotPixel(xb, y, color)
    
            xA += dx02
            xB += dx01
            y += 1
        
        xB = x1 * scale
    
        while y < y2:
            if 0 <= y < lib.height and (y & 1) == interlace:
                xa = xA >> FP
                xb = xB >> FP
                if xa > xb: xa, xb = xb, xa
    
                if fill:
                    Render.h_dither_line(y, xa, xb + 1, color)
                else:
                    Render.plotPixel(xa, y, color)
                    Render.plotPixel(xb, y, color)
    
            xA += dx02
            xB += dx12
            y += 1
    
    @staticmethod
    @micropython.native
    def renderWorld(verts, sprt, color, depth, count):
        global triID, sprtID
        if (count <= 0): return
        if (count > 1): Render.insertion_sort(depth, count)
        
        for i in range(count):
            z, dState, dID = depth[i]
            
            if (dState == -1): 
                break
            elif (dState == 0):
                if verts[dID] is None or color[dID] is None: continue
                Render.customTri(*verts[dID], color[dID], True)
            elif (dState == 1):
                pos = sprt[dID]
                if pos is None: continue
                Render.fillRect(pos[0] - 5, pos[1] - 5, 10, 10, 1)
                
        sprtID = 0
        triID  = 0
    
    @staticmethod
    def loadOBJ(filename, invert):
        verts   = []
        tris    = []
        normals = []
        color   = []
    
        with open(filename, "r") as f:
            for line in f:
                if line.startswith("v "):
                    parts = line.split()
    
                    x = lib.FMath.TO_FIXED_BITS(float(parts[1]))
                    y = lib.FMath.TO_FIXED_BITS(float(parts[2]))
                    z = lib.FMath.TO_FIXED_BITS(float(parts[3]))
    
                    verts.append([x, y, z])
                
                elif line.startswith("f "):
                    parts = line.split()
                    
                    idxs = []
                    
                    def calcNormal(a, b, c):
                        ax, ay, az = b[0]-a[0], b[1]-a[1], b[2]-a[2]
                        bx, by, bz = c[0]-a[0], c[1]-a[1], c[2]-a[2]
                        
                        nx = ay*bz - az*by
                        ny = az*bx - ax*bz
                        nz = ax*by - ay*bx
                        
                        length = sqrt(nx*nx + ny*ny + nz*nz)
                        nx /= length
                        ny /= length
                        nz /= length
                        
                        nx = lib.FMath.TO_FIXED_BITS(nx)
                        ny = lib.FMath.TO_FIXED_BITS(ny)
                        nz = lib.FMath.TO_FIXED_BITS(nz)
                        
                        return [nx, -ny, nz]

                    for p in parts[1:]:
                        if "/" in p: idx = int(p.split("/")[0]) - 1
                        else: idx = int(p) - 1
                        idxs.append(idx)
                    
                    if len(idxs) == 3:
                        tri = idxs
                        if invert:
                            tri[1], tri[2] = tri[2], tri[1]
                        tris.append(tri)
                        color.append(random.randint(1, 3))
                        
                        n = calcNormal(verts[idxs[0]], verts[idxs[1]], verts[idxs[2]])
                        normals.append(n)
                    elif len(idxs) == 4:
                        t1 = [idxs[0], idxs[1], idxs[2]]
                        t2 = [idxs[0], idxs[2], idxs[3]]
    
                        if invert:
                            t1[1], t1[2] = t1[2], t1[1]
                            t2[1], t2[2] = t2[2], t2[1]
    
                        tris.append(t1)
                        tris.append(t2)
    
                        color.append(random.randint(1, 3))
                        color.append(random.randint(1, 3))
                        
                        n1 = calcNormal(verts[t1[0]], verts[t1[1]], verts[t1[2]])
                        n2 = calcNormal(verts[t2[0]], verts[t2[1]], verts[t2[2]])
                        
                        normals.append(n1)
                        normals.append(n2)
                    
        return {
            "verts": verts,
            "tris": tris,
            "normal": normals,
            "color": color
        }