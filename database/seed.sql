-- ============================================
-- SEED DATA - Datos de prueba para desarrollo
-- ============================================

-- 1. USERS (3 usuarios: owner, mechanic, client)
INSERT INTO users (first_name, middle_name, last_name, second_last_name, document_number, email, role, password_hash, phone, status)
VALUES
('Carlos', NULL, 'Ramirez', 'Gomez', '1001234567', 'carlos.owner@tallermecanico.com', 'owner', 'hashed_password_123', '3001234567', 'active'),
('Andres', NULL, 'Torres', 'Lopez', '1002345678', 'andres.mecanico@tallermecanico.com', 'mechanic', 'hashed_password_123', '3012345678', 'active'),
('Laura', 'Maria', 'Gonzalez', 'Diaz', '1003456789', 'laura.cliente@gmail.com', 'client', 'hashed_password_123', '3023456789', 'active');

-- 2. BUSINESSES (1 negocio, dueño = Carlos)
INSERT INTO businesses (business_name, tax_id, address, business_phone, business_registration_number, legal_documents_verified, owner_user_id)
VALUES
('Taller Mecanico El Motor', '900123456-7', 'Calle 45 # 12-34, Bogota', '6011234567', 'RM-2024-00123', TRUE, 1);

-- 3. VEHICLES (2 vehiculos, propietario = Laura, user_id 3)
INSERT INTO vehicles (owner_user_id, license_plate, brand, model, year, color, vehicle_type, vin, engine_displacement, mileage, fuel_type, transmission_type)
VALUES
(3, 'ABC123', 'Mazda', '3', 2020, 'Rojo', 'car', '1HGCM82633A123456', 2.00, 45000, 'gasoline', 'automatic'),
(3, 'XYZ789', 'Yamaha', 'FZ', 2022, 'Negro', 'motorcycle', NULL, 150.00, 8000, 'gasoline', 'manual');

-- 4. BAYS (2 bahias del negocio)
INSERT INTO bays (business_id, bay_number, has_elevator, status)
VALUES
(1, 'Bahia 1', TRUE, 'available'),
(1, 'Bahia 2', FALSE, 'available');

-- 5. SERVICES (2 servicios del catalogo)
INSERT INTO services (business_id, service_name, description, estimated_duration_minutes, base_price, status)
VALUES
(1, 'Cambio de aceite', 'Cambio de aceite y filtro', 45, 80000, 'active'),
(1, 'Alineacion y balanceo', 'Alineacion de llantas y balanceo', 60, 120000, 'active');

-- 6. APPOINTMENTS (1 cita: Laura agenda con su Mazda, mecanico Andres)
INSERT INTO appointments (client_user_id, vehicle_id, service_id, bay_id, mechanic_user_id, scheduled_start, scheduled_end, status)
VALUES
(3, 1, 1, 1, 2, '2026-09-15 09:00:00', '2026-09-15 09:45:00', 'confirmed');

-- 7. PAYMENTS (2 pagos: deposito ya pagado, saldo pendiente)
INSERT INTO payments (appointment_id, payment_type, payment_method, amount, status, paid_at)
VALUES
(1, 'deposit', 'transfer', 30000, 'completed', '2026-09-13 10:00:00'),
(1, 'balance', 'cash', 50000, 'pending', NULL);

-- 8. PARTS (1 repuesto en inventario)
INSERT INTO parts (business_id, part_name, unit_price, stock_quantity, status)
VALUES
(1, 'Filtro de aceite', 15000, 20, 'active');

-- 9. SERVICE_TRACKING (1 registro de seguimiento de la cita)
INSERT INTO service_tracking (appointment_id, status, notes, current_mileage)
VALUES
(1, 'received', 'Vehiculo recibido, sin daños visibles', 45000);

-- 10. SERVICE_TRACKING_PARTS (repuesto usado en ese seguimiento)
INSERT INTO service_tracking_parts (tracking_id, part_id, quantity)
VALUES
(1, 1, 1);