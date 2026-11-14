import math, numpy as np
def V(p): return np.array([p[0], p[2], -p[1]], float)
def projector(eye, tgt, W, H, fov=None, ortho=None):
    E, T = V(eye), V(tgt); f = T - E; f /= np.linalg.norm(f)
    r = np.cross(f, [0, 1, 0]); r /= np.linalg.norm(r); u = np.cross(r, f); a = W / H
    def proj(p):
        d = V(p) - E; xc, yc, zc = d @ r, d @ u, d @ f
        if ortho: nx, ny = xc / (ortho * a), yc / ortho
        else:
            t = math.tan(math.radians(fov) / 2); nx, ny = xc / (zc * t * a), yc / (zc * t)
        return np.array([(nx + 1) / 2 * W, (1 - ny) / 2 * H])
    return proj
SITE = np.load('/home/claude/crit1/site.npy')
