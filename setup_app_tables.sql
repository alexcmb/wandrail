-- Tables pour les comptes utilisateurs et features sociales
-- À exécuter une seule fois sur la base tourisme_train

CREATE SCHEMA IF NOT EXISTS userapp;

CREATE TABLE IF NOT EXISTS userapp.users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    pseudo VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    ville_depart VARCHAR(100) DEFAULT 'Nantes',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS userapp.user_visits (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES userapp.users(id) ON DELETE CASCADE,
    destination VARCHAR(255) NOT NULL,
    co2_saved_kg FLOAT DEFAULT 0,
    dist_km FLOAT DEFAULT 0,
    visited_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS userapp.user_favorites (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES userapp.users(id) ON DELETE CASCADE,
    destination VARCHAR(255) NOT NULL,
    added_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, destination)
);

CREATE TABLE IF NOT EXISTS userapp.user_reviews (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES userapp.users(id) ON DELETE CASCADE,
    destination VARCHAR(255) NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5) NOT NULL,
    comment TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, destination)
);
