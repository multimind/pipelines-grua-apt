import cv2
import numpy as np
import math

def calcular_coordenadas_radio_giro(coordenada_en_imagen,radio,puntos_en_circulo,h,inversa):

    coordenada_garra_mundo=cv2.perspectiveTransform(coordenada_en_imagen,h)

    cx=coordenada_garra_mundo[0][0][0]
    cy=coordenada_garra_mundo[0][0][1]

    coordenadas_con_perspectiva=[]

    for i in range (0,puntos_en_circulo):
        circulo_x= cx+radio*math.cos((2*math.pi/puntos_en_circulo)*i)
        circulo_y= cy+radio*math.sin((2*math.pi/puntos_en_circulo)*i)
        t=np.array([[[circulo_x, circulo_y]]], dtype=np.float32)
        transformado=cv2.perspectiveTransform(t,inversa)
        coordenadas_con_perspectiva.append([transformado[0][0][0],transformado[0][0][1]])

    return coordenadas_con_perspectiva