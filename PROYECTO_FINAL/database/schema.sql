CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100) NULL,
    last_name VARCHAR(100) NOT NULL,
    second_last_name VARCHAR(100) NULL,
    document_number VARCHAR(20) NOT NULL UNIQUE,
    email VARCHAR(150) NOT NULL UNIQUE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('client', 'mechanic', 'admin', 'owner')),
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE businesses (
    business_id SERIAL PRIMARY KEY,
    business_name VARCHAR(150) NOT NULL,
    tax_id VARCHAR(20) NOT NULL,
    address VARCHAR(255) NOT NULL,
    business_phone VARCHAR(20) NULL,
    business_registration_number VARCHAR(50) NULL,
    legal_documents_verified BOOLEAN DEFAULT FALSE,
    owner_user_id INTEGER NOT NULL UNIQUE REFERENCES users(user_id)
);

CREATE TABLE vehicles (
    vehicle_id SERIAL PRIMARY KEY,
    owner_user_id INTEGER NOT NULL REFERENCES users(user_id),
    license_plate VARCHAR(10) NOT NULL UNIQUE,
    brand VARCHAR(50) NOT NULL,
    model VARCHAR(50) NOT NULL,
    year SMALLINT NOT NULL,
    color VARCHAR(30) NULL,
    vehicle_type VARCHAR(20) NOT NULL CHECK (vehicle_type IN ('car', 'motorcycle', 'truck', 'van')),
    vin VARCHAR(17) NULL UNIQUE,
    engine_displacement NUMERIC(6,2) NULL,
    mileage INTEGER NULL,
    fuel_type VARCHAR(20) NOT NULL CHECK (fuel_type IN ('gasoline', 'diesel', 'electric', 'hybrid')),
    transmission_type VARCHAR(20) NOT NULL CHECK (transmission_type IN ('manual', 'automatic'))
);

CREATE TABLE bays (
    bay_id SERIAL PRIMARY KEY,
    business_id INTEGER NOT NULL REFERENCES businesses(business_id),
    bay_number VARCHAR(20) NOT NULL,
    has_elevator BOOLEAN NOT NULL DEFAULT FALSE,
    status VARCHAR(20) NOT NULL DEFAULT 'available' CHECK (status IN ('available', 'under_maintenance')),
    UNIQUE (business_id, bay_number)
);

CREATE TABLE services (
    service_id SERIAL PRIMARY KEY,
    business_id INTEGER NOT NULL REFERENCES businesses(business_id),
    service_name VARCHAR(100) NOT NULL,
    description TEXT NULL,
    estimated_duration_minutes INTEGER NOT NULL,
    base_price INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive'))
);

CREATE TABLE appointments (
    appointment_id SERIAL PRIMARY KEY,
    client_user_id INTEGER NOT NULL REFERENCES users(user_id),
    vehicle_id INTEGER NOT NULL REFERENCES vehicles(vehicle_id),
    service_id INTEGER NOT NULL REFERENCES services(service_id),
    bay_id INTEGER NOT NULL REFERENCES bays(bay_id),
    mechanic_user_id INTEGER NOT NULL REFERENCES users(user_id),
    scheduled_start TIMESTAMP NOT NULL,
    scheduled_end TIMESTAMP NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'in_progress', 'completed', 'cancelled')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE payments (
    payment_id SERIAL PRIMARY KEY,
    appointment_id INTEGER NOT NULL REFERENCES appointments(appointment_id),
    payment_type VARCHAR(20) NOT NULL CHECK (payment_type IN ('deposit', 'balance')),
    payment_method VARCHAR(20) NOT NULL CHECK (payment_method IN ('cash', 'card', 'transfer')),
    amount INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed', 'refunded')),
    paid_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE parts (
    part_id SERIAL PRIMARY KEY,
    business_id INTEGER NOT NULL REFERENCES businesses(business_id),
    part_name VARCHAR(100) NOT NULL,
    unit_price INTEGER NOT NULL,
    stock_quantity INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive'))
);

CREATE TABLE service_tracking (
    tracking_id SERIAL PRIMARY KEY,
    appointment_id INTEGER NOT NULL REFERENCES appointments(appointment_id),
    status VARCHAR(20) NOT NULL CHECK (status IN ('received', 'diagnosing', 'in_repair', 'quality_check', 'ready_for_pickup', 'delivered')),
    notes TEXT NULL,
    current_mileage INTEGER NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE service_tracking_parts (
    tracking_id INTEGER NOT NULL REFERENCES service_tracking(tracking_id),
    part_id INTEGER NOT NULL REFERENCES parts(part_id),
    quantity INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (tracking_id, part_id)
);

