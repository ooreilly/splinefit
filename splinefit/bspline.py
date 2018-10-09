import numpy as np

def cubic(t):
    """
    Evaluate C^2 continuous cubic BSpline basis for each function B0, B1, B2, B3.

    out = [t^3, t^2, t, 1] * B

    To compute the Bspline curve, simply dot the resulting values with the
    control points.

    C(u) = [t^3, t^2, t, 1] * B_i * P, P = [P_i, P_{i+1}, P_{i+2}, P_{i+3}],

    where P are the control points.

    Arguments:
        t : Parameter, `0 <= t <= 1`.

    Returns
        out : Value of Bspline basis in each cell.


    """
    B= np.array([[-1, 3, -3, 1],
                 [3, -6, 3, 0],
                 [-3, 0, 3, 0],
                 [1, 4, 1, 0]])/6
    u = np.array([t**3, t**2, t, 1])

    out = u.dot(B)
    return out

def normalize(pts, n):
    """
    Renormalize points so that for each point `pt`, we have `0 <= pt <= n`.

    Arguments:
        pts : List of points (array of size (m,))
        n : Number of control points - 1.

    Returns:
        out : Normalized points
        nc : Normalization constants

    """
    pmin = np.min(pts) 
    pmax = np.max(pts)
    out = n*(pts - pmin)/(pmax - pmin)
    nc = (pmin, pmax)
    return out, nc 

def denormalize(npts, nc, n):
    """
    Restore normalized points, to their original, unnormalized representation

    Arguments:
        npts : List of normalized points (array of size (m,))
        nc : Normalization constants (see `normalize`)
        n : Number of control points - 1.

    Returns:
        out : Normalized points

    """
    out = npts*(nc[1] - nc[0])/n + nc[0]
    return out

def lower(pts):
    """
    Determine the lowest index of the control points that lie in the
    neighborhood of the query points `pts`.

    Arguments:
        pts : Query points, must be normalized to 0 <= pts <= n, where n+1 is
            the number of control points.
    """
    return int(np.floor(pts) - 1)

def upper(pts):
    """
    Same as `lower`, but returns the highest index.
    """
    return int(np.floor(pts) + 2)

def eval(P, npts=10):

    t = np.linspace(0, 1, npts)
    x = np.zeros(((len(P)-3)*npts,))
    y = np.zeros(((len(P)-3)*npts,))
    k = 0
    for i in range(1,len(P)-2):
        ctrlpts = P[i-1:i+3]
        for ti in t:
            qx = cubic(ti).dot(ctrlpts)
            y[k] = qx
            x[k] = i + ti - 1
            k += 1
    return x, y

def eval_basis(xc, n):
    idx = np.floor(xc)
    t = (xc - idx)/n
    w = cubic(t)
    return w

def set_ctrlpt(xc, yc, n):
    """

    Assign value to control point by solving the constrained optimization
    problem:

    min || \sum_a P_a ||^2 subject to \sum_a w_a P_a = yc

    Solution is given by:

    P_k = w_k*yc/(sum_a w_a^2)

    Arguments:
        xc : x-coordinate of point. Determines which control point to
            influence. 
        yc : y-coordinate of point. Determines what weight to assign to the
            affected control point.
         n : Number of control points - 1

    Returns:
        val : Value of control point.
        idx : Index of control point.

    """

    w = eval_basis(xc, n)
    return w*yc/(w.dot(w)), (lower(xc) + 2, upper(xc) + 3) 


def findspan(n, p, u, U):
    """

    n : Number of control points
    p : degree
    u : parameter to find span for, should lie in 0 <= u <= 1.
    U : knot vector

    """
    if u == U[n+1]:
        return n

    for i in range(p, p + n):
        if u >= U[i] and u < U[i+1]:
            return i
    return n
    low = p
    high = n + 1
    mid = int((low+high)/2)
    while (u < U[mid] or u >= U[mid+1]):
        if (u < U[mid]):
            high = mid
        else:
            low = mid
        mid = int((low + high)/2)
    return mid

def basisfuns(i,u,p,U):
    N = np.zeros((p+1,))
    left = np.zeros((p+1,))
    right = np.zeros((p+1,))
    N[0] = 1.0
    for j in range(1,p+1):
        left[j] = u - U[i+1-j]
        right[j] = U[i+j] - u
        saved = 0.0
        for r in range(j):
            denom = right[r+1] + left[j-r]
            if np.isclose(denom,0):
                N[r] = 1
                break
            temp = N[r]/denom
            N[r] = saved+right[r+1]*temp
            saved = left[j-r]*temp
        N[j] = saved

    return N

def curvepoint(p, U, P, u):
    C = 0.0
    n = len(P) - p
    span = findspan(n, p, u, U)
    N = basisfuns(span,u,p,U)
    for i in range(p+1):
        C = C + N[i]*P[span-p+i]
    return C

def surfacepoint(p, U, V, P, u, v):
    S = 0.0
    nv = P.shape[0] - p
    nu = P.shape[1] - p
    span_u = int(np.floor(u)) + p
    span_u = findspan(nu, p, u, U)
    span_v = int(np.floor(v)) + p
    span_v = findspan(nv, p, v, V)
    Nu = basisfuns(span_u,u,p,U)
    Nv = basisfuns(span_v,v,p,V)
    for i in range(p+1):
        for j in range(p+1):
            S = S + Nu[i]*Nv[j]*P[span_v-p+j, span_u-p+i]
    return S

def evalcurve(p, U, P, u):
    y = 0*u
    for i in range(len(u)):
        y[i] = curvepoint(p, U, P, u[i])
    return y

def evalsurface(p, U, V, P, u, v):
    w = np.zeros((len(u), len(v)))
    for i in range(w.shape[0]):
        for j in range(w.shape[1]):
            w[i,j] = surfacepoint(p, U, V, P, u[i], v[j])
    return w

def uniformknots(m, p, a=0, b=1):
    """
    Construct a uniform knot vector

    Arguments:
    m : Number of interior knots
    p : Polynomial degree
    a(optional) : left boundary knot
    b(optional) : right boundary knot

    """
    t = np.linspace(a,b,m+2)
    U = np.r_[(a,)*(p+1),
              t[1:-1],
              (b,)*(p+1)]
    return U

def kmeansknots(s, m, p, a=0, b=1):
    """
    Construct a knot vector by finding knot positions using kmeans for selecting
    knots.
    """
    t = np.linspace(a,b,m)
    from scipy.cluster.vq import vq, kmeans
    t = np.sort(kmeans(s, m)[0])
    U = np.r_[(a,)*(p+1),
              t,
              (b,)*(p+1)]
    return U


def lsq(x, y, U, p):
    """
    Computes the least square fit to the data (x,y) using the knot vector U.

    Arguments:
        x, y : Data points
        U : Knot vector
        p : Degree of BSpline

    Returns:
        P : Control points,
        res : residuals

    """
    assert len(x) == len(y)
    nctrl = len(U) - 1
    n = nctrl - p - 1
    npts = len(x)

    A = np.zeros((npts, nctrl))
    b = np.zeros((npts,))
    for i, xi in enumerate(x):
        span = findspan(n, p, xi, U)
        N = basisfuns(span, xi, p, U)
        for j, Nj in enumerate(N):
            A[i, span + j - p] = Nj
        b[i] = y[i]

    p0 = np.linalg.lstsq(A, b, rcond=None)[0]
    res = np.linalg.norm(A.dot(p0) - b)
    return p0, res

def lsq2surf(u, v, z, U, V, p):
    """
    Computes the least square fit to the mapped data z(u, v) using the knot
    vector U, V.

    Arguments:
        u, v : Mapping of (x, y) coordinates of data points to parameterization
        U, V : Knot vector
        p : Degree of BSpline

    Returns:
        P : Control points (size: mu x mv),
        res : residuals

    """
    assert len(u) == len(v)
    assert len(u) == len(z)

    #FIXME: fails if mu = 1
    mu = len(U) - 1
    mv = len(V) - 1
    nu = mu - p - 1
    nv = mv - p - 1
    npts = len(z)
    P = np.zeros((mu,mv))

    A = np.zeros((npts, mu*mv))
    b = np.zeros((npts,))
    for i in range(npts):
        ui = u[i]
        vi = v[i]
        zi = z[i]
        span_u = findspan(nu, p, ui, U)
        span_v = findspan(nv, p, vi, V)
        Nu = basisfuns(span_u, ui, p, U)
        Nv = basisfuns(span_v, vi, p, V)
        for k, Nk in enumerate(Nu):
            for l, Nl in enumerate(Nv):
                A[i, (span_v + l - p)*mu + (span_u + k - p)] = Nk*Nl
        b[i] = zi

    p0 = np.linalg.lstsq(A, b, rcond=None)[0]
    res = np.linalg.norm(A.dot(p0) - b)
    print("Residual", res)
    P = p0.reshape((mv, mu))
    return P, res


def chords(x, y, a=0, b=1):
    """
    Map (x_j, y_j) to the interval a <= s_j <=b using the chord length
    parameterization.

    s_0 = a 
    s_1 = a + d_1, 
    s_j = s_{j-1} + d_j
    where d_j = dist(P_j - P_{j-1}), and P_j = (x_j, y_j).

    """
    dx = x[1:] - x[0:-1]
    dy = y[1:] - y[0:-1]
    dists = np.sqrt(dx**2 + dy**2)
    d = np.zeros((len(x),))
    for i in range(len(dists)):
        d[i+1] = d[i] + dists[i]

    d = (b-a)*(d-min(d))/(max(d)-min(d)) + a
    return d

def xmap(x, a=0, b=1):
    """
    Map real number x to the interval a <= s_j <=b by normalizing values.

    """

    denom = max(x)-min(x)
    if np.isclose(denom,0):
        denom = 1
    d = (x-min(x))/denom
    d = (b-a)*d + a
    
    return d

def argsort2(u, v):
    """
    Sort the two arrays `u` and `v` treating them as separate dimensions. 
    The order of the output is 
    `w[0] = i[0] + nu*j[0]`
    `w[1] = i[1] + nu*j[0]`
    where `i[0]` is `argmin(u)` and `j[0]` is `argmin(v)`. Hence, `i[1]` is the
    index of the second smallest value in `u` and so forth.
    """
    assert len(u) == len(v)
    i = np.argsort(u)
    j = np.argsort(v)
    w = np.zeros((len(u),))


def lsq2(s, x, y, U, p):
    """
    Fit a curve C(s) = sum_i B_i(s) P, where control points P = (P_x, P_y)

    s defines the mapping of each data point (x_j, y_j) to the curve parameter
    s_j. A simple mapping to use is the L2 distance between points `see l2map`.

    Arguments:
        s : Mapping of (x,y) to the curve
        U : Knot vector
        p : Polynomial degree.

    Returns:
        Px, Py : The coordinates of the control points.
        res : Residuals.

    """
    Px, rx = lsq(s, x, U, p)
    Py, ry = lsq(s, y, U, p)
    return Px, Py, (rx, ry)
 
def smoothing(x, y, sm=0.1, mmax=100, disp=False, p=3):
    """
    Perform least squares fitting by successively increasing the number of knots
    until a desired residual threshold is reached.

    Returns:
        Px, Py : Control points
        U : Knot vector

    """

    m = 2
    it = 0
    res = sm + 1
    while (res > sm and m < mmax):
        it += 1
        Px, Py, U, res = lsq2l2(x, y, m, p)
        res = np.linalg.norm(res)
        if disp:
            print("Iteration: %d, number of knots: %d, residual: %g" % (it, m,
                res))
        m = 2+m
    return Px, Py, U


def lsq2l2(x, y, m, p, knots='kmeans', exclude_endpts=0):
    """
    Perform least squares fitting using `m` number of knots and chordlength
    parameterization and averaged knot vector.
    """
    s = chords(x, y, a=0, b=1)
    if knots == 'uniform':
        U = uniformknots(m, p, a=0, b=1)
    elif knots == 'kmeans':
        U = kmeansknots(s, m, p, a=0, b=1)
    if exclude_endpts:
        # Use interpolation at end points
        sf = s[1:-1]
        xf = x[1:-1]
        yf = y[1:-1]
        Pxf, Pyf, res = lsq2(s, x, y, U[1:-1], p)
        Px = np.r_[x[0],Pxf[1:-1], x[-1]]
        Py = np.r_[y[0],Pyf[1:-1], y[-1]]
    else:
        Px, Py, res = lsq2(s, x, y, U, p)
    return Px, Py, U, res

def lsq2x(x, y, m, p, axis=0):
    """
    Perform least squares fitting using `m` number of knots and normalization of
    input coordinates to 0 <= s <= 1. Argument `axis` controls which coordinate
    to use in the mapping process.
    """
    if axis == 0:
        s = xmap(x, m, a=0, b=1)
    else:
        s = xmap(y, m, a=0, b=1)

    U = uniformknots(m, p, a=0, b=1)
    Px, Py, res = lsq2(s, x, y, U, p)
    return Px, Py, U, res
