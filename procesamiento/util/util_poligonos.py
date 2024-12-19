from multiprocessing import pool
from shapely.geometry import LineString, Point, Polygon
import json
import logging

def leer_poligono(nombre_json_fondo,nombre_poligono):

    with open(nombre_json_fondo) as f:
        data = json.load(f)

    lista_shapes=data['shapes']

    poligonos=[]

    for shape in lista_shapes:

        nombre_label=shape['label']

        if not nombre_label==nombre_poligono:
            continue

        lista_points=shape['points']
        lista_tuplas=[]

        for p in lista_points:
            lista_tuplas.append((p[0],p[1]))

        poligono = Polygon(lista_tuplas)
        #poligonos.append(Polygon(lista_tuplas))

    return poligono

def leer_poligono_trabajadorGoldfield(nombre_json_fondo,nombre_poligono):

    with open(nombre_json_fondo) as f:
        data = json.load(f)

    lista_shapes=data['shapes']

    poligonos=[]

    for shape in lista_shapes:

        nombre_label=shape['label']

        if not nombre_label==nombre_poligono:
            continue

        lista_points=shape['points']
        lista_tuplas=[]

        for p in lista_points:
            lista_tuplas.append((p[0],p[1]))

        #poligono = Polygon(lista_tuplas)
        poligonos.append(Polygon(lista_tuplas))

    return poligonos

def leer_poligono_zona_despuntes(nombre_json_fondo,nombre_poligono):

    with open(nombre_json_fondo) as f:
        data = json.load(f)

    lista_shapes=data['shapes']

    poligonos=[]

    for shape in lista_shapes:

        nombre_label=shape['label']

        if not nombre_label==nombre_poligono:
            continue

        lista_points=shape['points']
        lista_tuplas=[]

        for p in lista_points:
            lista_tuplas.append((p[0],p[1]))

        poligono = Polygon(lista_tuplas)
        #poligonos.append(Polygon(lista_tuplas))

    return poligono

def leer_puntos_poligono(nombre_json_fondo,nombre_poligono):

    with open(nombre_json_fondo) as f:
        data = json.load(f)

    lista_shapes = data["shapes"]

    puntos = []

    for shape in lista_shapes:

        nombre_label = shape["label"]

        if not nombre_label == nombre_poligono:
            continue

        lista_points=shape['points']
        lista_tuplas=[]

        for p in lista_points:
            lista_tuplas.append((p[0],p[1]))
        lista_tuplas.append((lista_tuplas[0]))
        puntos.append(lista_tuplas)
    return puntos

def centro_box(rx1,ry1,rx2,ry2):
    rcx=(rx2-rx1)/2.0+rx1
    rcy=(ry2-ry1)/2.0+ry1

    centro=Point(rcx,rcy)

    return centro

def centro_box_puntos(rx1,ry1,rx2,ry2):
    rcx=(rx2-rx1)/2.0+rx1
    rcy=(ry2-ry1)/2.0+ry1

    centro=[rcx,rcy]

    return centro

def centro_box_inferior(rx1,ry1,rx2,ry2):
    rcx=(rx2-rx1)/2.0+rx1
    centro=[rcx,ry2 + 5]

    return centro

def box_dentro_poligono(rx1,ry1,rx2,ry2,poligono):

    rcx=(rx2-rx1)/2.0+rx1
    rcy=(ry2-ry1)/2.0+ry1

    centro=Point(rcx,rcy)

    if poligono.contains(centro):
        return True

    return False

def base_box_dentro_poligono(rx1,ry1,rx2,ry2,poligono):

    rcx=(rx2-rx1)/2.0+rx1
    rcy=ry2

    centro=Point(rcx,rcy)

    if poligono.contains(centro):
        return True

    return False

def box_overlap_poligono(rx1,ry1,rx2,ry2,poligono):

    box_poligono = Polygon([(rx1, ry1), (rx2, ry1), (rx2, ry2), (rx1, ry2)])

    if(poligono.overlaps(box_poligono)):
        return True

    return False

def poligono_contiene_box(rx1,ry1,rx2,ry2,zx1,zy1,zx2,zy2):

    box_poligono = Polygon([(rx1, ry1), (rx2, ry1), (rx2, ry2), (rx1, ry2)])
    poligono = Polygon([(zx1, zy1), (zx2, zy1), (zx2, zy2), (zx1, zy2)])

    if(poligono.contains(box_poligono)):
        return True

    return False

def box_dentro_poligono_maquina(rx1,ry1,rx2,ry2,zx1,zy1,zx2,zy2):

    poligono = Polygon([(zx1, zy1), (zx2, zy1), (zx2, zy2), (zx1, zy2)])

    rcx=(rx2-rx1)/2.0+rx1
    rcy=(ry2-ry1)/2.0+ry1

    centro=Point(rcx,rcy)

    if poligono.contains(centro):
        return True

    return False

def box_poligono(rx1,ry1,rx2,ry2):
    
    box_poligono = Polygon([(rx1, ry1), (rx2, ry1), (rx2, ry2), (rx1, rx2)])

    return box_poligono

def linea_inferior_poligono(rx1,ry1,rx2,ry2,poligono):
    
    linea = LineString([(rx1, ry2), (rx2, ry2)])
    punto1 = Point(rx1, ry2)
    punto2 = Point(rx2, ry2)

    if poligono.contains(punto1) and poligono.contains(punto2):
        return True

    return False
    

def barra_zona_prohibida(rx1,ry1,rx2,ry2,poligono):
    punto1 = Point(rx1, ry1)
    punto2 = Point(rx2, ry2)
    punto3 = Point(rx2, ry1)
    punto4 = Point(rx1, ry2)

    puntos = [poligono.contains(punto1), poligono.contains(punto2), poligono.contains(punto3), poligono.contains(punto4)].count(True)

    if puntos >= 2:
        return True

    return False

def barra_incandescente_trabada(rx1,ry1,rx2,ry2,poligono):
    punto1 = Point(rx1, ry1)
    punto2 = Point(rx2, ry2)
    punto3 = Point(rx2, ry1)
    punto4 = Point(rx1, ry2)

    puntos = [poligono.contains(punto1), poligono.contains(punto2), poligono.contains(punto3), poligono.contains(punto4)].count(True)

    if puntos == 4:
        return True

    return False


def leer_poligono_domo(nombre_json_fondo,nombre_poligono):

    with open(nombre_json_fondo) as f:
        data = json.load(f)

    lista_shapes=data['shapes']
    #print(lista_shapes)
    poligono=[]
    listas_de_poligonos = []
    for shape in lista_shapes:

        nombre_label=shape['label']

        if not nombre_label==nombre_poligono:
            continue

        lista_points=shape['points']

        lista_tuplas=[]
        for p in lista_points:
            lista_tuplas.append((p[0],p[1]))
        listas_de_poligonos.append(Polygon(lista_tuplas))

    return listas_de_poligonos

def leer_poligono_subdivisiones(nombre_json_fondo,nombre_poligono):

    with open(nombre_json_fondo) as f:
        data = json.load(f)

    lista_shapes=data['shapes']
    poligono=[]
    listas_de_poligonos = []
    for shape in lista_shapes:

        nombre_label=shape['label']

        if not nombre_label.startswith(nombre_poligono):
            continue
        
        zona = nombre_label.split('_')[-1]

        lista_points=shape['points']

        lista_tuplas=[]
        for p in lista_points:
            lista_tuplas.append((p[0],p[1]))
        listas_de_poligonos.append((Polygon(lista_tuplas), zona))

    return listas_de_poligonos
    
def linea_dentro_poligono(rx1,ry1,rx2,ry2,poligono):

    #rx1=box[1]
    #ry1=box[0]
    #rx2=box[3]
    #ry2=box[2]

    linea=LineString([(rx1, ry1), (rx2, ry2)])

    if poligono.intersects(linea):
        return True

    return False

def transformar_lista(poligono):
    lista_tuplas = []

    for i in poligono:
        lista_tuplas.append((i[0], i[1]))
    return Polygon(lista_tuplas)

def interseccion_area_boxes(poligono1, poligono2):
    intersection = poligono1.intersection(poligono2)

    intersection_area = intersection.area

    return intersection_area

def punto_medio_poligono(rx1,ry1,rx2,ry2,poligono):

    mx = (rx1 + rx2) / 2
    punto_medio = Point(int(mx), ry2)

    if poligono.contains(punto_medio):
        return True

    return False

def box_salida_cizalla(rx1,ry1,rx2,ry2,poligono):
    punto1 = Point(rx1, ry1)
    punto2 = Point(rx2, ry2)
    punto3 = Point(rx2, ry1)
    punto4 = Point(rx1, ry2)

    puntos = [poligono.contains(punto1), poligono.contains(punto2), poligono.contains(punto3), poligono.contains(punto4)].count(True)

    if puntos >= 1:
        return True

    return False
