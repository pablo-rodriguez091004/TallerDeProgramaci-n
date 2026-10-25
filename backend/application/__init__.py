"""
Capa de aplicacion: casos de uso por bounded context.

Cada servicio recibe sus dependencias (puertos del dominio) por CONSTRUCTOR;
nunca crea adaptadores ni importa Flask/SQLAlchemy. El cableado concreto
vive en bootstrap.py (composition root) y las pruebas unitarias pasan mocks.
"""
