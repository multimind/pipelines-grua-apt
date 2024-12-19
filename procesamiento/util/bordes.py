import matplotlib.pyplot as plt
import numpy as np
import json
import cv2
from PIL import Image
from shapely.geometry import Polygon


def obtener_vertices_externos(mask):
    """
    Calcula los puntos más extremos de los polígonos encontrados en la máscara binaria
    """
    contornos, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    vertices_poligonos = []
    # Tolerancia para la simplificación del contorno
    tolerancia = 0.02 * cv2.arcLength(contornos[0], True)

    for contorno in contornos:
        # Aproximar el contorno para reducir el número de vértices
        contorno_aproximado = cv2.approxPolyDP(contorno, tolerancia, True)

        # Convertir el contorno aproximado a una lista de puntos
        puntos = contorno_aproximado[:, 0, :]

        poligono = Polygon(puntos)
        envolvente_convexa = poligono.convex_hull
        vertices_externos = list(envolvente_convexa.exterior.coords)

        vertices_poligonos.append(vertices_externos)


    vertices_externos = []
    for poligono in vertices_poligonos:

        # Encontrar los puntos más extremos
        min_x = min(poligono, key=lambda punto: punto[0])
        max_x = max(poligono, key=lambda punto: punto[0])
        min_y = min(poligono, key=lambda punto: punto[1])
        max_y = max(poligono, key=lambda punto: punto[1])

        # Imprimir los puntos más extremos
        print(f"Punto con menor X: {min_x}")
        print(f"Punto con mayor X: {max_x}")
        print(f"Punto con menor Y: {min_y}")
        print(f"Punto con mayor Y: {max_y}")

        vertices_externos.append([min_x, max_x, min_y, max_y])
    
    return vertices_externos


if __name__ == "__main__":

    ids_imagenes = "/media/aaronponce/Juegos/mm/Fierros/medicion-varillas/segmentador_varillas/dataset_laton/script/ruta_dataset/ids_dataset.json"
    rutas_imagenes = "/media/aaronponce/Juegos/mm/Fierros/medicion-varillas/segmentador_varillas/dataset_laton/script/ruta_dataset/rutas_dataset.json"

    with open(ids_imagenes, "r") as file:
        ids_imagenes = json.load(file)

    with open(rutas_imagenes, "r") as file:
        rutas_imagenes = json.load(file)


    id_imagen = ids_imagenes["train"][0]
    ruta_imagen = rutas_imagenes[id_imagen]["imagen"]
    segmentacion_json = rutas_imagenes[id_imagen]["segmentacion"]

    with open(segmentacion_json, "r") as file:
        data = json.load(file)


    imagen = cv2.imread(ruta_imagen)
    mask = np.zeros(imagen.shape[0:2], dtype=np.uint8)

    for indice in range(0,len(data["shapes"])):
        if data["shapes"][indice]["label"] == "laton":
            poligono = data["shapes"][indice]["points"]
            pts = np.array(poligono, np.int32)
            cv2.fillPoly(mask, [pts], (255,255,255))

    
    vertices_externos = obtener_vertices_externos(mask)
    print(vertices_externos)


