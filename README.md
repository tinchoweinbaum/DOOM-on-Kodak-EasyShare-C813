"# DOOM-on-Kodak-EasyShare-C813" 
Lo primero es usar zadig para cambiar el driver que utiliza windows para comunicarse con la cámara, hay que usar libusb x32. Después es trastear con el test_usb.py para conseguir un par de datos críticos:
-> ID´S (VENDOR Y PRODUCT) 
-> ENDPOINTS
-> UNA FORMA DE QUE LA CAMARA DUMPEE LA ROM A LA SD.

