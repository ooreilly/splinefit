from splinefit import gmsh

def load(test):

    txt = open('fixtures/' + test + '.geo').read() 
    return txt

def test_get_command():

    geo = "Point(1) = {1.0, 2.0, 3.0};"
    point = gmsh.get_command('Point', geo)
    assert point['1'][0] == '1.0'

    tests = ['test1']

    for test in tests:
        splines = gmsh.get_command('Spline', load(test))
        points  = gmsh.get_command('Point', load(test))
        assert gmsh.check_groupmembers(splines, points)

def test_check_group():

    a = {0 : [0], 1 : [1]}
    b = {0 : 1, 1 : 1}
    assert gmsh.check_groupmembers(a, b)
    b = [0, 1]
    assert gmsh.check_groupmembers(a, b)
    a = {0 : [0], 1 : [1, 2]}
    assert not gmsh.check_groupmembers(a, b)


def test_get_variables():

    geo = 'a = 10;'
    var = gmsh.get_variables(geo)
    assert var['a'] == '10'
    geo = 'p2 = 10.0 + p2;'
    var = gmsh.get_variables(geo)
    assert var['p2'] == '10.0 + p2'
    geo = '2p = 10.0 + p2;'
    var = gmsh.get_variables(geo)
    assert var == None
    geo = 'p_2 = 1 - 2;'
    var = gmsh.get_variables(geo)
    assert var['p_2'] == '1 - 2'
