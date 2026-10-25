"""
Capa de dominio (nucleo de la arquitectura hexagonal).

Solo Python estandar: entidades, reglas de negocio y PUERTOS (interfaces
abstractas). No puede importar Flask, SQLAlchemy ni librerias de red/IO;
tests/test_architecture.py lo verifica en cada corrida de pytest.

Un subpaquete por bounded context (DDD):
  identity      usuarios y credenciales
  catalog       gestion del negocio: taller, bahias, servicios, repuestos, vehiculos
  scheduling    agendamiento (nucleo): disponibilidad simultanea bahia + mecanico
  payments      pagos simulados (deposito + saldo)
  tracking      seguimiento del servicio en el taller
  ai_assistant  sugerencia de servicios con LLM (RAG)
"""
