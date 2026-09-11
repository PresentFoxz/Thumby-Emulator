import micropython
import random
import library as lib
from math import *

DEADZONE = 1 << 4

cW = lib.w_Half << lib.FIXED_BITS
cH = lib.h_Half << lib.FIXED_BITS

sprtID = 0
triID  = 0

yaw, pitch = None, None
sinY, cosY, sinX, cosX = None, None, None, None

class Entities:
    def __init__(self, x, y, z, rx, ry, rz, sx, sy, sz, idx):
        self.x = lib.FMath.TO_FIXED_BITS(x)
        self.y = lib.FMath.TO_FIXED_BITS(y)
        self.z = lib.FMath.TO_FIXED_BITS(z)
        
        self.rx = lib.FMath.TO_FIXED_BITS(rx)
        self.ry = lib.FMath.TO_FIXED_BITS(ry)
        self.rz = lib.FMath.TO_FIXED_BITS(rz)
        
        self.sx = lib.FMath.TO_FIXED_BITS(sx)
        self.sy = lib.FMath.TO_FIXED_BITS(sy)
        self.sz = lib.FMath.TO_FIXED_BITS(sz)

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

                if self.rx > lib.FMath.TO_FIXED_BITS(68): self.rx = lib.FMath.TO_FIXED_BITS(68)
                if self.rx < lib.FMath.TO_FIXED_BITS(-68): self.rx = lib.FMath.TO_FIXED_BITS(-68)
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
            base = i * 3

            keyZ     = depths[base]
            keyState = depths[base + 1]
            keyID    = depths[base + 2]
            if keyState == -1: continue
            
            j = i - 1
            while j >= 0:
                jb = j * 3
                if depths[jb] >= keyZ: break

                nb = (j + 1) * 3

                depths[nb]     = depths[jb]
                depths[nb + 1] = depths[jb + 1]
                depths[nb + 2] = depths[jb + 2]
                j -= 1
            
            dst = (j + 1) * 3
            depths[dst]     = keyZ
            depths[dst + 1] = keyState
            depths[dst + 2] = keyID
    
    @staticmethod
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
        
        color_scaled:int = int(lib.MUL_OPP(color * 16, 3))
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
        shd = ptr8(lib.shd)
        inv = 255 - mask
        
        for x in range(x_start, x_end):
            if color == 1:
                buf[row + x] |= mask
                shd[row + x] &= inv
            elif color == 2:
                buf[row + x] &= inv
                shd[row + x] |= mask
            elif color == 3:
                buf[row + x] |= mask
                shd[row + x] |= mask
            else:
                buf[row + x] &= inv
                shd[row + x] &= inv
    
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
    @micropython.viper
    def checkBounds(x0:int, y0:int, x1:int, y1:int, x2:int, y2:int):
        width:int  = int(lib.width)
        height:int = int(lib.height)

        if x0 < 0: x0 = 0
        if x1 < 0: x1 = 0
        if x2 < 0: x2 = 0
        if x0 >= width: x0 = width - 1
        if x1 >= width: x1 = width - 1
        if x2 >= width: x2 = width - 1

        if y0 < 0: y0 = 0
        if y1 < 0: y1 = 0
        if y2 < 0: y2 = 0
        if y0 >= height: y0 = height - 1
        if y1 >= height: y1 = height - 1
        if y2 >= height: y2 = height - 1

        return x0, y0, x1, y1, x2, y2

    @staticmethod
    @micropython.native
    def directVerts(px, py, pz, cam, verts_out, color_out, depth_out, count, tris_data, normals, colors):
        global triID, cosX, cW, cH, sinY, cosY, sinX, cosX, forwardX, forwardY, forwardZ
        cCount = 0
        
        cx, cy, cz = cam.x, cam.y, cam.z
        fov, near, far = cam.fov, cam.near, cam.far
        for i in range(len(tris_data) // 3):
            if triID >= lib.MAX_TRIS or (count + cCount) >= lib.MAX_TRIS: break
            tID = i * 3
            v0 = tris_data[tID]
            v1 = tris_data[tID + 1]
            v2 = tris_data[tID + 2]
            
            r0 = Render.worldToCam(cx, cy, cz, v0[0] + px, v0[1] + py, v0[2] + pz, sinX, sinY, cosX, cosY)
            r1 = Render.worldToCam(cx, cy, cz, v1[0] + px, v1[1] + py, v1[2] + pz, sinX, sinY, cosX, cosY)
            r2 = Render.worldToCam(cx, cy, cz, v2[0] + px, v2[1] + py, v2[2] + pz, sinX, sinY, cosX, cosY)
            if r0 is None or r1 is None or r2 is None: continue
            
            nx, ny, nz = normals[i]
            dot = (lib.FMath.FIXED_MUL(nx, cam.norm_x) + lib.FMath.FIXED_MUL(ny, cam.norm_y) + lib.FMath.FIXED_MUL(nz, cam.norm_z))
            if dot > 0: continue
            
            p0 = Render.projectPoint(r0, cW, cH, fov, near, far)
            p1 = Render.projectPoint(r1, cW, cH, fov, near, far)
            p2 = Render.projectPoint(r2, cW, cH, fov, near, far)
            if p0 is None or p1 is None or p2 is None: continue
    
            if Render.checkRend(*p0, *p1, *p2) != 0: continue

            x0, y0, x1, y1, x2, y2 = Render.checkBounds(*p0, *p1, *p2)

            o = triID * 6
            verts_out[o]     = x0
            verts_out[o + 1] = y0
            verts_out[o + 2] = x1
            verts_out[o + 3] = y1
            verts_out[o + 4] = x2
            verts_out[o + 5] = y2
            color_out[triID] = colors[i]

            newCount = (cCount + count) * 3
            depth_out[newCount] = lib.MUL_OPP(r0[2] + r1[2] + r2[2], 3)
            depth_out[newCount + 1] = 0
            depth_out[newCount + 2] = triID

            cCount += 1
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
    @micropython.viper
    def customLine(x1:int, y1:int, x2:int, y2:int, color:int):
        interlace:int = int(lib.interlace)
        
        buf = ptr8(lib.buf)

        width:int = int(lib.width)
        height:int = int(lib.height)

        if x1 < 0 and x2 < 0: return
        if x1 >= width and x2 >= width: return

        if y1 < 0 and y2 < 0: return
        if y1 >= height and y2 >= height: return

        dx:int = x2 - x1
        if dx < 0: dx = 0 - dx

        sx:int = 0 - 1
        if x1 < x2: sx = 1

        dy:int = y2 - y1
        if dy < 0: dy = 0 - dy
        
        dy = 0 - dy

        sy:int = 0 - 1
        if y1 < y2: sy = 1

        err:int = dx + dy
        while True:
            if (y1 & 1) == interlace:
                if x1 >= 0 and x1 < width and y1 >= 0 and y1 < height:
                    page:int = (y1 >> 3) * width
                    mask:int = 1 << (y1 & 7)
                    inv:int = 255 - mask
    
                    if color: buf[page + x1] |= mask
                    else: buf[page + x1] &= inv
    
            if x1 == x2 and y1 == y2: break

            err2:int = err << 1

            if err2 >= dy:
                err += dy
                x1 += sx

            if err2 <= dx:
                err += dx
                y1 += sy

    @staticmethod
    @micropython.viper
    def customTri(x0:int, y0:int, x1:int, y1:int, x2:int, y2:int, color:int):
        if y1 < y0:
            tx:int = x0
            ty:int = y0
            x0 = x1
            y0 = y1
            x1 = tx
            y1 = ty
        if y2 < y0:
            tx:int = x0
            ty:int = y0
            x0 = x2
            y0 = y2
            x2 = tx
            y2 = ty
        if y2 < y1:
            tx:int = x1
            ty:int = y1
            x1 = x2
            y1 = y2
            x2 = tx
            y2 = ty
    
        if y0 == y2: return
    
        scale:int = int(256)
    
        dy02:int = int(y2 - y0)
        dy01:int = int(y1 - y0)
        dy12:int = int(y2 - y1)
    
        dx02:int = int(lib.MUL_OPP((x2 - x0) * scale, dy02)) if dy02 != 0 else 0
        dx01:int = int(lib.MUL_OPP((x1 - x0) * scale, dy01)) if dy01 != 0 else 0
        dx12:int = int(lib.MUL_OPP((x2 - x1) * scale, dy12)) if dy12 != 0 else 0
    
        interlace:int = int(lib.interlace)
        height:int = int(lib.height)

        xA:int = int(x0 * scale)
        xB:int = int(x0 * scale)
        y:int = y0

        while y < y1:
            if 0 <= y < height and (y & 1) == interlace:
                xa:int = int(xA >> 8)
                xb:int = int(xB >> 8)
                if xa > xb:
                    tmp:int = xa
                    xa = xb
                    xb = tmp
    
                Render.h_line(y, xa, xb + 1, color)
    
            xA += dx02
            xB += dx01
            y += 1
        
        xB = x1 * scale
    
        while y < y2:
            if 0 <= y < height and (y & 1) == interlace:
                xa:int = int(xA >> 8)
                xb:int = int(xB >> 8)
                if xa > xb:
                    tmp:int = xa
                    xa = xb
                    xb = tmp
    
                Render.h_line(y, xa, xb + 1, color)
    
            xA += dx02
            xB += dx12
            y += 1
    
    @staticmethod
    @micropython.viper
    def setupTris(verts, o:int, color:int, check:bool) -> int:
        fillCount:int = 0

        o0:int = o
        o1:int = o + 1
        o2:int = o + 2
        o3:int = o + 3
        o4:int = o + 4
        o5:int = o + 5

        x0:int = int(verts[o0])
        y0:int = int(verts[o1])
        x1:int = int(verts[o2])
        y1:int = int(verts[o3])
        x2:int = int(verts[o4])
        y2:int = int(verts[o5])

        if check:
            if int(z) <= 2200 and int(triIndex) >= int(fillStart):
                Render.customTri(x0, y0, x1, y1, x2, y2, color)
                fillCount += 1
            else:
                if color > 1: color = 1
                elif color < 0: color = 0
                Render.customLine(x0, y0, x1, y1, color)
                Render.customLine(x1, y1, x2, y2, color)
                Render.customLine(x2, y2, x0, y0, color)
        else:
            Render.customTri(x0, y0, x1, y1, x2, y2, color)
            fillCount += 1

        return fillCount
    
    @staticmethod
    @micropython.viper
    def renderWorld(verts, sprt, color, depth, count:int, check:bool):
        global triID, sprtID
        if (count <= 0): return
        if (count > 1): Render.insertion_sort(depth, count)

        triCount:int = 0
        for i in range(count):
            d:int = int(i * 3)

            if int(depth[d + 1]) == 0: triCount += 1
        
        fillStart:int = triCount >> 1

        triIndex:int = 0
        filledCount:int = 0
        
        for i in range(count):
            d:int = int(i * 3)

            z:int      = int(depth[d])
            dState:int = int(depth[d + 1])
            dID:int    = int(depth[d + 2])
            
            if (dState == -1): break
            elif (dState == 0):
                o:int = int(dID * 6)
                filledCount += int(Render.setupTris(verts, o, color[dID], check))
                triIndex += 1
            elif (dState == 1):
                x:int = int(sprt[dID][0])
                y:int = int(sprt[dID][1])
                if x and y: continue
                Render.fillRect(x - 5, y - 5, 10, 10, 1)
        
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
                    faceColor = int(parts[-1])
                    def calcNormal(a, b, c):
                        ax, ay, az = b[0]-a[0], b[1]-a[1], b[2]-a[2]
                        bx, by, bz = c[0]-a[0], c[1]-a[1], c[2]-a[2]

                        nx = (ay*bz - az*by) >> lib.FIXED_BITS
                        ny = (az*bx - ax*bz) >> lib.FIXED_BITS
                        nz = (ax*by - ay*bx) >> lib.FIXED_BITS

                        return [nx, -ny, nz]

                    for p in parts[1:-1]:
                        if "/" in p: idx = int(p.split("/")[0])
                        else: idx = int(p)

                        idxs.append(idx)
                    
                    if len(idxs) == 3:
                        tri = idxs
                        if invert:
                            tri[1], tri[2] = tri[2], tri[1]
                        tris.append(tri)
                        color.append(faceColor)
                        
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
    
                        color.append(faceColor)
                        color.append(faceColor)
                        
                        n1 = calcNormal(verts[t1[0]], verts[t1[1]], verts[t1[2]])
                        n2 = calcNormal(verts[t2[0]], verts[t2[1]], verts[t2[2]])
                        
                        normals.append(n1)
                        normals.append(n2)
        
        print("Tri Length: " + str(len(tris)) + " | Vert Length: " + str(len(verts)))
        return {
            "verts": verts,
            "tris": tris,
            "normal": normals,
            "color": color
        }