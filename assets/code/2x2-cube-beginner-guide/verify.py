"""Geometric checks for the blog's 2x2 method. Python 3, no dependencies."""
from itertools import permutations, product

NORMALS = {'R': (1,0,0), 'L': (-1,0,0), 'U': (0,1,0),
           'D': (0,-1,0), 'F': (0,0,1), 'B': (0,0,-1)}
TOP = [('U','R','F'), ('U','F','L'), ('U','L','B'), ('U','B','R')]
A = "R U R' U'"
B = "R' D' R D"
T = "R U R' U' R' F R2 U' R' U' R U R' F'"

def solved():
    return {(p,n): f for p in product((-1,1), repeat=3)
            for f,n in NORMALS.items() if sum(a*b for a,b in zip(p,n)) == 1}

def rot(v, axis, sign):
    a = list(v)
    i,j = (axis+1)%3, (axis+2)%3
    a[i],a[j] = -sign*v[j], sign*v[i]
    return tuple(a)

def move(s, token):
    f = token[0]
    n = NORMALS[f] if f != 'y' else NORMALS['U']
    axis = next(i for i,x in enumerate(n) if x)
    turns = 2 if token.endswith('2') else (3 if token.endswith("'") else 1)
    for _ in range(turns):
        s = {(rot(p,axis,-n[axis]),rot(v,axis,-n[axis]))
             if f == 'y' or p[axis] == n[axis] else (p,v): c
             for (p,v),c in s.items()}
    return s

def alg(s, text):
    for token in text.split():
        s = move(s,token)
    return s

def uniform(s):
    return all(len({c for (p,v),c in s.items() if v == n}) == 1
               for n in NORMALS.values())

def align(s):
    for _ in range(4):
        if uniform(s):
            return s
        s = move(s,'U')
    return None

def pair(s, face):
    n = NORMALS[face]
    return len({c for (p,v),c in s.items() if p[1] == 1 and v == n}) == 1

def last_layer(s):
    # Orient every top corner at the same work position; only U between corners.
    for _ in range(4):
        for repeats in range(7):
            if s[((1,1,1),NORMALS['U'])] == 'U':
                break
            s = alg(s,B)
        else:
            raise AssertionError('orientation did not terminate')
        s = move(s,'U')
    assert all(c == 'U' for (p,v),c in s.items() if v == NORMALS['U'])
    assert all(s[k] == c for k,c in solved().items() if k[0][1] == -1)
    done = align(s)
    if done:
        return done
    if not any(pair(s,f) for f in 'FRBL'):
        s = alg(s,T)
    for _ in range(4):
        if pair(s,'L'):
            break
        s = move(s,'y')
    else:
        raise AssertionError('no pair after first permutation')
    return align(alg(s,T))

def corner_position(faces):
    return tuple(sum(NORMALS[f][i] for f in faces) for i in range(3))

def main():
    count = 0
    for perm in permutations(range(4)):
        for ori3 in product(range(3), repeat=3):
            ori = (*ori3, -sum(ori3)%3)
            s = solved()
            for dest,src,twist in zip(TOP,perm,ori):
                p = corner_position(dest)
                for i,f in enumerate(dest):
                    s[(p,NORMALS[f])] = TOP[src][(i+twist)%3]
            result = last_layer(s)
            assert result is not None and uniform(result), (perm,ori)
            count += 1
    # A repeated at most five times inserts each possible UFR white corner
    # into DFR, preserving all other bottom corners.
    base = solved()
    for k in (1,3,5):
        s = alg(base, ' '.join([A]*k))
        for _ in range(6):
            if all(s[key] == c for key,c in base.items() if key[0] == (1,-1,1)):
                break
            s = alg(s,A)
        assert s == base
    print(f'PASS: {count} last-layer states (24 permutations x 27 orientations)')
    print('PASS: first-layer insertion in all 3 UFR orientations')

if __name__ == '__main__':
    main()
