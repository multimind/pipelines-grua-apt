import logging
from logging.handlers import RotatingFileHandler
import os
#este entrega mas detalle format='%(asctime)s - %(message)s  [ %(filename)s %(funcName)s %(lineno)s ]',level=log_level)

def configurar(nombre_camara,log_level,limpiar_al_partir):
    """Configura ``logger``.

    Esta función configura el ``logger`` y crea una carpeta de ``logs``.

    :param str nombre_camara: Nombre que se le dará la archivo ``.log``.
    :param str log_level: Nivel de alerta del log. Los valores que acepta son: ``logging.DEBUG``, ``logging.INFO``, ``logging.WARNING``, ``logging.ERROR`` y ``logging.CRITICAL``.
    :param bool limpiar_al_partir: Opcional; Si es ``True`` se limpian los archivos al iniciar. (Por defecto es ``False``)
    """

    if not os.path.exists('log/'):
        os.mkdir("log/")
        
    handler=RotatingFileHandler('log/'+nombre_camara+'.log',
        maxBytes= 10*1024*1024, 
        backupCount=5
    )
    
    root_logger= logging.getLogger()
    root_logger.setLevel(log_level) 
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    root_logger.addHandler(handler)

    if limpiar_al_partir:
        handler.doRollover()
