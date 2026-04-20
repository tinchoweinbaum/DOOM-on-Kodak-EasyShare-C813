"""
Archivo para testar scripts de envío y recibo de paquetes con la cámara por usb
"""
import usb.core # Libreria para manejo de dispositivos usb
import usb.util # utilidades para esto, tipos de datos y esas cosas.

import struct # struct para poder armar los codigos ptp mas facilmente

class KODAK_ES_C813:
    IdVendor = 0x40a
    idProduct = 0x5c3
    ENDPOINT_BULK_IN = 0x83
    ENDPOINT_BULK_OUT = 0x4
    ENDPOINT_INTERRUPT_IN = 0x85

def listarUsb():
    # Busca todos los dispositivos conectados
    dispositivos = usb.core.find(find_all=True)

    print("Listando dispositivos USB encontrados:")
    print("-" * 40)

    for dev in dispositivos:
        # Obtener el ID de fabricante y de producto en formato hexadecimal
        vid = hex(dev.idVendor)
        pid = hex(dev.idProduct)
        
        # Intentar obtener el nombre del fabricante (a veces requiere permisos)
        try:
            fabricante = usb.util.get_string(dev, dev.iManufacturer)
            producto = usb.util.get_string(dev, dev.iProduct)
            print(f"ID {vid}:{pid} | {fabricante} {producto}")
        except:
            # Si no puede leer los strings, imprime solo los IDs
            print(f"ID {vid}:{pid} | (No se pudo leer nombre del dispositivo)")

    print("-" * 40)

def getDevice(idVendor, idProduct):
    "Recibe un idVendor e idProduct y devuelve un objeto dev que representa el dispositivo USB con esos ID´s"
    dev = usb.core.find(idVendor=idVendor, idProduct=idProduct)
    if dev is None:
        return None
    dev.set_configuration()
    return dev

def getEndpoints(idVendor, idProduct):

    # Buscamos específicamente a la Kodak
    dev = usb.core.find(idVendor=idVendor, idProduct=idProduct) # Busca el dispositivo especificado y lo "guarda" en un objeto de la clase usb.core

    if dev is None:
        print(f"No se encontró el dispositivo con idProduct {idProduct} e idVendor {idVendor}.")
    else:
        dev.set_configuration() # Le quita el control del dispostivo al OS para que el script haga todo mientras esté corriendo. Secuestro del dispositivo.
        
        cfg = dev.get_active_configuration() # Pide a la cámara que liste todos sus endpoints.
        intf = cfg[(0,0)]
        
        for ep in intf: # Recorre endpoint por endpoint para listarlos según tipo y direccionalidad.
            # Determinamos si es de Entrada (IN) o Salida (OUT)
            direccion = "IN (Cámara -> PC)" if usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_IN else "OUT (PC -> Cámara)"
            
            # Determinamos el tipo de transferencia
            tipo = ""
            if usb.util.endpoint_type(ep.bmAttributes) == usb.util.ENDPOINT_TYPE_BULK:
                tipo = "BULK (Datos pesados/Firmware)"
            elif usb.util.endpoint_type(ep.bmAttributes) == usb.util.ENDPOINT_TYPE_INTR:
                tipo = "INTERRUPT (Eventos/Botones)"
                
            print(f"Dirección: {hex(ep.bEndpointAddress)} | Tipo: {tipo} | {direccion}")

        print("-" * 40)

def send_ptp(dev, payload):
    """
    Función para envíar paquetes del protocolo ptp a la cámara por USB.
    """
    try:
        # Enviamos los bytes (el payload ya debe venir armado con su Header PTP)
        dev.write(KODAK_ES_C813.ENDPOINT_BULK_OUT, payload)
        print(f" Bytes enviados: {payload.hex()}")
    except usb.core.USBError as e:
        print(f"Error enviando PTP: {e}")

def receive_ptp(dev, size=1024):
    """
    Función listener en el endpoint de IN de la cámara. 5 segundos de timeout
    """
    try:
        respuesta = dev.read(KODAK_ES_C813.ENDPOINT_BULK_IN, size, timeout=5000)
        return respuesta.tobytes()
    except usb.core.USBError as e:
        print(f"Error recibiendo PTP: {e}")
        return None

def printDeviceInfo(dev):
    """
    Función de alto nivel: Solo se preocupa por QUÉ pedir, no CÓMO enviarlo.
    """
    print("\n--- Solicitando DeviceInfo (0x1001) ---")
    
    # Paquete PTP: [Len: 12][Type: Command=1][OpCode: 0x1001][TransID: 1]
    header = b'\x0c\x00\x00\x00\x01\x00\x01\x10\x01\x00\x00\x00'
    
    send_ptp(dev, header)
    data = receive_ptp(dev)
    
    if data:
        print(f"Respuesta Hex: {data.hex()}")
        print(f"Respuesta ASCII: {data.decode('ascii', errors='ignore')}")

def tomar_foto(dev):
    "Esta función hace creer al OS que está sacando una foto, pero realmente no lo hace por estar en modo PTP. Simplemente envía el opCode de 'sacar foto'"
    print("\n--- DISPARANDO CÁMARA (0x100e) ---")
    
    # Paquete PTP: [Len: 20] (porque incluimos dos parámetros de 4 bytes cada uno)
    # [Len][Type][OpCode][TransID][Param1][Param2]
    # Param1: 0x00000000 (StorageID) | Param2: 0x00000000 (ObjectFormat)
    header = b'\x14\x00\x00\x00\x01\x00\x0e\x10\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    
    send_ptp(dev, header)
    res = receive_ptp(dev)
    
    if res:
        print("Respuesta de la cámara:", res.hex())

def test_vendor_codes(dev):
    # Los códigos que extrajimos de tu respuesta anterior
    opcodes_a_probar = [0x9005, 0x9006, 0x9007, 0x9008, 0x9009, 0x900a, 0x900b, 
                         0x900c, 0x900d, 0x900e, 0x900f, 0x9010, 0x9011]
    
    for code in opcodes_a_probar:
        print(f"\nProbrando OpCode: {hex(code)}")
        
        # Intentamos un paquete de comando estándar pero con el código de Kodak
        # Algunos comandos de lectura piden la dirección como parámetro
        # Vamos a probar enviarlo simple primero
        header = b'\x0c\x00\x00\x00\x01\x00' + code.to_bytes(2, 'little') + b'\x01\x00\x00\x00'
        
        send_ptp(dev, header)
        res = receive_ptp(dev, 1024) # Pedimos un poco más de info por las dudas
        
        if res:
            print(f"!!! RESPUESTA del {hex(code)}: {res.hex()[:60]}...")
        else:
            print(f"El código {hex(code)} no devolvió nada o dio error.")

# 1. Abrir sesión (ya sabemos que funciona)
# 2. Intentar el Dump de RAM con la estructura que vimos en los headers

def dump_cam_os_segment(dev):
    print("\n--- DUMPEANDO SEGMENTO CamOS A ARCHIVO ---")
    
    address = 0x00B00000 
    size = 1024 # Vamos a pedir 1KB de nuevo
    
    cmd = struct.pack('<IHHII I', 20, 1, 0x900c, 3, address, size)
    
    try:
        dev.write(0x04, cmd)
        
        # Leemos el Data Container completo
        # El header es 12, así que leemos 12 + el tamaño de los datos
        full_res = dev.read(0x83, 1024 + 12)
        
        header = full_res[:12]
        ram_data = full_res[12:]
        
        print(f"Capturados {len(ram_data)} bytes de RAM.")
        
        with open("camOS_dump.bin", "wb") as f:
            f.write(ram_data)
            
        # IMPORTANTE: Después del Data Container, la cámara MANDA UN RESPONSE (12 bytes)
        # Hay que leerlo para "limpiar" el buffer USB
        final_status = dev.read(0x83, 12)
        print(f"Status final de la cámara: {final_status.tobytes().hex()}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":

    listarUsb()
    # getEndpoints(KODAK_ES_C813.IdVendor, KODAK_ES_C813.idProduct)
    camara = getDevice(KODAK_ES_C813.IdVendor,KODAK_ES_C813.idProduct)
    #printDeviceInfo(camara)
    #test_vendor_codes(camara)
    dump_cam_os_segment(camara)