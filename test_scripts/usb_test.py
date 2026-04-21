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
    FIRST_BUFFER_SIZE = 12 # Tamaño en bytes de la supuesta "tabla de descriptores" que hay en la dirección 0x00B00000 (Donde la cámara carga el OS)
    STORAGEID_RAM = 0x20001
    STORAGEID_ROM = 0x10000

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
        print(f" Bytes enviados: {payload.hex()}\n")
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
    
def build_ptp_packet(opcode, transaction_id=0, params=None):
    """
    Construye un paquete de comando PTP listo para enviar por USB.

    :param opcode: El OpCode (ej: 0x1002 para OpenSession, 0x9003 para Serial)
    :param transaction_id: ID incremental de la transacción
    :param params: Lista de parámetros adicionales (máximo 5 según estándar PTP)
    :return: Bytes empaquetados en Little Endian
    """
    if params is None:
        params = []

    # El header PTP base mide 12 bytes: 
    # [Length (4b)] [Type (2b)] [OpCode (2b)] [TransactionID (4b)]
    packet_length = 12 + (len(params) * 4)

    # El 'Type' para comandos siempre es 1
    packet_type = 1

    # Construimos el formato para struct.pack:
    # < : Little Endian
    # I : Unsigned Int (4 bytes) - Para Length
    # H : Unsigned Short (2 bytes) - Para Type
    # H : Unsigned Short (2 bytes) - Para OpCode
    # I : Unsigned Int (4 bytes) - Para TransactionID
    # {len(params)}I : 'I' repetida por cada parámetro
    fmt = f"<IHH I {len(params)}I"

    packet = struct.pack(fmt, packet_length, packet_type, opcode, transaction_id, *params)

    return packet

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

def ejecutar_test_storage(dev):
    try:
        # 1. ABRIR SESIÓN (Obligatorio, 16 bytes)
        # TransactionID debe ser 0. El SessionID es el parámetro (1).
        print("\n--- [1] Abriendo Sesión (0x1002) ---")
        pkt_open = build_ptp_packet(opcode=0x1002, transaction_id=0, params=[1])
        send_ptp(dev, pkt_open)
        
        resp_open = receive_ptp(dev)
        if not resp_open or resp_open[6:8] != b'\x01\x20': # 0x2001 es OK
            print(f"Fallo al abrir sesión. Respuesta: {resp_open.hex() if resp_open else 'Nada'}")
            return

        print("Sesión abierta con éxito (OK).")

        # 2. GET STORAGE IDs (0x1004)
        # Una vez abierta, el TransactionID debe subir a 1.
        print("\n--- [2] Solicitando Storage IDs (0x1004) ---")
        pkt_storage = build_ptp_packet(opcode=0x1004, transaction_id=1)
        send_ptp(dev, pkt_storage)
        
        # Primero recibimos el DATA PHASE (donde están los IDs)
        data_ids = receive_ptp(dev, size=1024)
        # Luego recibimos el RESPONSE PHASE (el OK final)
        resp_final = receive_ptp(dev, size=12)

        if data_ids:
            print(f"DATA recibida (Hex): {data_ids.hex()}")
            # El estándar PTP dice que los primeros 4 bytes del payload 
            # de datos son la cantidad de elementos en el array.
            # Los bytes 12 en adelante (después del header de 12 bytes) son los IDs.
            num_storages = struct.unpack("<I", data_ids[12:16])[0]
            print(f"Número de unidades de almacenamiento: {num_storages}")
            
            for i in range(num_storages):
                start = 16 + (i * 4)
                s_id = struct.unpack("<I", data_ids[start:start+4])[0]
                print(f" -> StorageID {i}: {hex(s_id)}")

        # 3. CERRAR SESIÓN (Para no bloquear la cámara)
        print("\n--- [3] Cerrando Sesión (0x1003) ---")
        pkt_close = build_ptp_packet(opcode=0x1003, transaction_id=2)
        send_ptp(dev, pkt_close)
        receive_ptp(dev)

    except Exception as e:
        print(f"Error en el proceso: {e}")

def check_storage_info(dev, storage_id):
    """
    Realiza un ciclo completo de sesión para obtener info de un Storage específico.
    """
    try:
        # 1. ABRIR SESIÓN (TransactionID SIEMPRE 0)
        print(f"\n--- [1] Abriendo Sesión para analizar {hex(storage_id)} ---")
        pkt_open = build_ptp_packet(opcode=0x1002, transaction_id=0, params=[1])
        send_ptp(dev, pkt_open)
        res_open = receive_ptp(dev)
        
        if not res_open or res_open[6:8] != b'\x01\x20': # 0x2001 es OK (Little Endian)
            print(f"Error al abrir sesión: {res_open.hex() if res_open else 'Sin respuesta'}")
            return

        # 2. PEDIR STORAGE INFO (TransactionID 1)
        print(f"--- [2] Solicitando Info de {hex(storage_id)} ---")
        pkt = build_ptp_packet(opcode=0x1005, transaction_id=1, params=[storage_id])
        send_ptp(dev, pkt)
        
        # Leemos el Data Phase (Type 2)
        data = receive_ptp(dev, size=1024)
        
        # Leemos el Response Phase (Type 3 - El OK final del comando)
        status = receive_ptp(dev, size=12)

        if data:
            # Validamos si es un paquete de datos (Type 0x0002 en bytes 4-5)
            if data[4:6] == b'\x02\x00':
                print(f"Dataset recibido: {data.hex()}")
                try:
                    # El estándar dice: Offset 12 son 8 bytes para Max Capacity
                    capacidad = struct.unpack("<Q", data[12:20])[0]
                    print(f"Capacidad Total: {capacidad} bytes ({capacidad / (1024*1024):.2f} MB)")
                except Exception as e:
                    print(f"Error al parsear bytes: {e}")
            else:
                print(f"La cámara no mandó datos, mandó esto: {data.hex()}")

        # 3. CERRAR SESIÓN (TransactionID 2)
        print(f"--- [3] Cerrando Sesión ---")
        pkt_close = build_ptp_packet(opcode=0x1003, transaction_id=2)
        send_ptp(dev, pkt_close)
        receive_ptp(dev)

    except Exception as e:
        print(f"Fallo crítico en check_storage_info: {e}")

def test_final_nand(dev):
    ID_NAND = 0x10001 # Cambiamos de 0x20001 a 0x10001
    TAMANO_DUMMY = 512 # Probamos con solo un sector (512 bytes) para no saturar
    
    try:
        # 1. Abrir sesión
        print("\n--- [1] Abriendo sesión ---")
        pkt_open = build_ptp_packet(0x1002, 0, [1])
        send_ptp(dev, pkt_open)
        receive_ptp(dev)

        # 2. Intentar 0x900c en la NAND
        print(f"--- [2] Test 0x900c en NAND ({hex(ID_NAND)}) ---")
        pkt_command = build_ptp_packet(0x900c, 1, [ID_NAND, 0, 0])
        send_ptp(dev, pkt_command)
        
        # Mandamos el header de datos + 512 bytes de estática (basura)
        header_data = struct.pack("<IHH I", 12 + TAMANO_DUMMY, 2, 0x900c, 1)
        basura = b'\xff\x00' * (TAMANO_DUMMY // 2)
        
        dev.write(0x04, header_data + basura)
        
        print("Enviado. Esperando respuesta...")
        res = receive_ptp(dev)
        print("Respuesta de la cámara:", res.hex() if res else "Timeout")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Intentar cerrar sesión para no dejar el puerto tomado
        send_ptp(dev, build_ptp_packet(0x1003, 2))
        receive_ptp(dev)

if __name__ == "__main__":

    listarUsb()
    # getEndpoints(KODAK_ES_C813.IdVendor, KODAK_ES_C813.idProduct)
    camara = getDevice(KODAK_ES_C813.IdVendor,KODAK_ES_C813.idProduct)
    # printDeviceInfo(camara)
    # ejecutar_test_storage(camara)
    # check_storage_info(camara,0x10000)
    test_final_nand(camara)