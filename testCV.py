#DEFINICION CLASE PARA BUSCAR CIRCULOS
import numpy as np
import cv2
import ClasificadorColor
import sys

#DECLARACION DE VARIABLES INTERNAS

#DIMENSIONES PARA RECORTAR LA IMAGEN
xMax = 800
xMin = 5
yMax = 222
yMin = 70

class detectaFondo:

    def __init__(self):
        self.fondo= np.zeros((180,795,3),np.uint8)
        self.fondoHSV = np.zeros((180,795,3),np.uint8)

    def capturaFondo(self,cap,enviar1,q):

        flag=0
        while(flag==0):
            frame = cap.read()
            
            frame = frame[yMin:yMax,xMin:xMax]
            enviar1.send(['N',frame])
            while not q.empty():
                variable=q.get()
                if(variable==5):
                    self.fondo = frame
                    self.fondoHSV = cv2.cvtColor(self.fondo,cv2.COLOR_BGR2HSV)
                    flag=1
                    break
                if(variable==4):
                    cap.stop()
                    exit()
                    break

    def getfondoHSV(self):
        return(self.fondoHSV)

class Filtrado:

    def __init__(self):
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3))
     
    def filtrado(self,cap,fondo):
        #CAPTURA DEL FRAME
        self.frame = cap.read()
        self.frame = self.frame[yMin:yMax,xMin:xMax]
        #cv2.imshow('vivo',self.frame)
        #CONVERSION A HSV
        self.frameHSV = cv2.cvtColor(self.frame,cv2.COLOR_BGR2HSV)
        #cv2.imshow('HSV',self.frameHSV)
        #RESTA EN HSV
        self.diferencia = cv2.absdiff(fondo,self.frameHSV)
        #cv2.imshow('dif',self.diferencia)
        #CONVERSION A GRIS
        self.dif_gray = cv2.cvtColor(self.diferencia,cv2.COLOR_BGR2GRAY)
        #FILTRADO
        self.dif_gray = cv2.GaussianBlur(self.dif_gray,(5,5),0)
        #RELLENO por defecto valor 25
        th,im_th = cv2.threshold(self.dif_gray,45,200,cv2.THRESH_BINARY_INV)
        im_flood = im_th.copy()
        h,w = im_th.shape[:2]
        mask = np.zeros((h+2,w+2),np.uint8)
        cv2.floodFill(im_flood,mask,(0,0),255)
        im_flood_inv = cv2.bitwise_not(im_flood)
        #IMAGEN DE SALIDA
        im_out = im_th | im_flood_inv
        #cv2.imshow('flood',im_out)
        #APLICACION DE FILTRO GAUSS
        gauss_fill = cv2.GaussianBlur(im_out,(3,3),0)
        #DETECCION DE BORDES
        canny = cv2.Canny(gauss_fill,25,175)
        #OPERACIONES DE DILATAMIENTO Y FILTRO NUEVAMENTE
        self.dilate = cv2.dilate(canny,self.kernel,iterations=2)
        self.dilate = cv2.GaussianBlur(self.dilate,(3,3),0)
        
		
        #cv2.waitKey(1)

    def getFrameFiltrado(self):

        ret = self.dilate.copy()
        return ret
	
    def getFrameOriginal(self):
        return self.frame

class detectaCirculos:

    def __init__(self):
        self.mascaraContorno = np.zeros((yMax-yMin,635,3),np.uint8)
        self.mascara = np.zeros((50, 50, 3), np.uint8)
        self.pixelesPromedio = np.zeros((10, 3), np.uint8)
        self.contornos  = 0
        self.promedio = 0
        self.coefForma = 0
        self.habCircles = 0
        self.circuloEncontrado = 0
        self.indicepic = 0
        self.objetoNoCircular = 0

    def contornoExterior(self,dilate,frame):

        if (dilate is not None):
			
            _, contornos, _ = cv2.findContours(dilate,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contornos:
				
		#M = cv2.moments(cnt)
                #cX = int(M["m10"] / M["m00"])
                #cY = int(M["m01"] / M["m00"])

                (x,y,w,h) = cv2.boundingRect(cnt)
                w = float(w)
                h = float(h)

                if(w*h > 3000 and (x> 100 and x<400)):
					
                    print("")
                    print("Posible objeto circular, por area")
                    #cv2.circle(frame, (cX, cY), 7, (255, 255, 255), -1)
                    print("Area: ", w*h)
                    self.coefForma =  float (w)/float(h)
                    print("Ceof Forma: ", self.coefForma)

                    if ((self.coefForma)> 0.80 and  (self.coefForma) <1.20):
                        print("Objeto posiblemente circular, por coef forma")
                        self.habCircles = 1

                    else:
			print("Objeto no circular, descartado por coef forma")
                        self.objetoNoCircular = 1

    def buscaCirculos(self,mascaraDilate,frame):

        if(self.habCircles == 1):

            self.habCircles = 0
	    
            self.circles = cv2.HoughCircles(mascaraDilate,cv2.HOUGH_GRADIENT,3,250,
                                           param1=110,
                                           param2=150, #PARAMETRO EN 150 POR DEFECTO!
                                           minRadius=40, #ORIGINAL 25
                                           maxRadius=65)

            if (self.circles is not None):

                for circuloActual in self.circles[0,:]:
		            
		    print("Objeto circular, confirmado por Hough")
                    centroX = circuloActual[0]
                    centroY = circuloActual[1]
                    radio   = circuloActual[2]
                    self.circuloEncontrado = 1
                    #cv2.circle(frame, (centroX,centroY), radio,[0,255,0], 5)
                    #cv2.imshow('circulo',frame)
                    #cv2.waitKey(1)
                    
                    mascara = frame[int(centroY)-25:int(centroY)+25,int(centroX)-25:int(centroX)+25]
                    if mascara.size:
                        color_promedio_columnas = np.average(mascara,axis = 0)
                        self.promedio = np.average(color_promedio_columnas, axis = 0)
                        #cv2.imshow("mascara",mascara)
            else:
                
		print("Objeto no circular, descartado por Hough")
                self.objetoNoCircular = 1

    def CirculoDetectado(self):
        #Devuelve 1 en el caso de que se haya detectado un circulo
        ret = 0
        if (self.circuloEncontrado == 1):
            self.circuloEncontrado = 0
            ret = 1
            
        return ret

    def ObjetoDetectado(self):
        #Devuelve 1 en el caso de qe se haya detectado un objeto
        ret = 0
        if(self.objetoNoCircular == 1):
            self.objetoNoCircular = 0
            ret = 1
  
        return ret

    def getPromedio(self):
        #devuelvo color promedio de la tapita detectada
        return self.promedio

