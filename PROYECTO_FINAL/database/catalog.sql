-- Catalogo ampliado (Guia 5): 10 servicios adicionales para el negocio 1.
-- Sirve para una base que ya existe y esta migrada (necesita la restriccion
-- UNIQUE(business_id, service_name) de la migracion ec27632baa28).
-- Es idempotente: si el servicio ya existe, no lo duplica ni lo modifica.
-- Uso: ./scripts/seed_catalog.sh
INSERT INTO services (business_id, service_name, description, estimated_duration_minutes, base_price, status)
VALUES
(1, 'Cambio de pastillas de freno', 'Reemplazo de pastillas de freno y revision del liquido de frenos', 90, 180000, 'active'),
(1, 'Rectificación de discos de freno', 'Rectificado o cambio de discos de freno alabeados que causan vibracion al frenar', 120, 220000, 'active'),
(1, 'Revisión de suspensión', 'Revision y cambio de amortiguadores, bujes, terminales y rotulas', 120, 250000, 'active'),
(1, 'Sincronización de motor', 'Cambio de bujias, limpieza de inyectores y ajuste de la mezcla aire-combustible', 120, 280000, 'active'),
(1, 'Diagnóstico con escáner', 'Lectura de codigos de falla de la computadora del vehiculo (check engine)', 45, 90000, 'active'),
(1, 'Revisión de batería y sistema eléctrico', 'Prueba de bateria, alternador y motor de arranque', 60, 100000, 'active'),
(1, 'Mantenimiento de aire acondicionado', 'Recarga de gas refrigerante, limpieza del evaporador y cambio del filtro de cabina', 90, 200000, 'active'),
(1, 'Revisión de embrague', 'Ajuste o cambio del kit de embrague (disco, prensa y balinera)', 240, 650000, 'active'),
(1, 'Mantenimiento del sistema de refrigeración', 'Cambio de refrigerante y revision de radiador, termostato y mangueras', 90, 170000, 'active'),
(1, 'Cambio de correa de distribución', 'Reemplazo del kit de correa de distribucion y bomba de agua', 240, 550000, 'active')
ON CONFLICT (business_id, service_name) DO NOTHING;
