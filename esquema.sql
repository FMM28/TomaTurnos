CREATE DATABASE IF NOT EXISTS turnos;
USE turnos;

-- Usuarios del sistema
CREATE TABLE usuario (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(45) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(45) NOT NULL
);

-- Áreas de atención
CREATE TABLE area (
    id_area INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(45) UNIQUE NOT NULL
);

-- Trámites por área
CREATE TABLE tramite (
    id_tramite INT AUTO_INCREMENT PRIMARY KEY,
    id_area INT NOT NULL,
    name VARCHAR(45) NOT NULL,
    FOREIGN KEY (id_area) REFERENCES area(id_area)
);

-- Ventanillas de atención
CREATE TABLE ventanilla (
    id_ventanilla INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(45) NOT NULL,
    id_area INT,
    FOREIGN KEY (id_area) REFERENCES area(id_area)
);

-- Asignación de usuarios a trámites
CREATE TABLE asignacion (
    id_asignacion INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_tramite INT NOT NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario),
    FOREIGN KEY (id_tramite) REFERENCES tramite(id_tramite)
);

-- Ticket principal
CREATE TABLE ticket (
    id_ticket INT AUTO_INCREMENT PRIMARY KEY,
    fecha_hora DATETIME NOT NULL,
    turno INT NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'activo'
);

-- Trámites asociados a un ticket
CREATE TABLE ticket_tramite (
    id_ticket_tramite INT AUTO_INCREMENT PRIMARY KEY,
    id_ticket INT NOT NULL,
    id_tramite INT NOT NULL,
    estado VARCHAR(20) DEFAULT 'espera',
    prioridad INT,
    FOREIGN KEY (id_ticket) REFERENCES ticket(id_ticket),
    FOREIGN KEY (id_tramite) REFERENCES tramite(id_tramite)
);

-- Atención en ventanilla
CREATE TABLE atencion (
    id_atencion INT AUTO_INCREMENT PRIMARY KEY,
    id_ticket_tramite INT NOT NULL,
    id_ventanilla INT NOT NULL,
    id_usuario INT NOT NULL,
    estado VARCHAR(20),
    descripcion_estado VARCHAR(45),
    hora_inicio DATETIME,
    hora_fin DATETIME,
    FOREIGN KEY (id_ticket_tramite) REFERENCES ticket_tramite(id_ticket_tramite),
    FOREIGN KEY (id_ventanilla) REFERENCES ventanilla(id_ventanilla),
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario)
);
