CREATE DATABASE IF NOT EXISTS plant_tracker_db;
USE plant_tracker_db;

DROP TABLE IF EXISTS plant_photos;
DROP TABLE IF EXISTS care_activities;
DROP TABLE IF EXISTS plants;
DROP TABLE IF EXISTS gardeners;
DROP TABLE IF EXISTS admins;

CREATE TABLE admins (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    status ENUM('enabled', 'disabled') NOT NULL DEFAULT 'enabled',
    join_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE gardeners (
    gardener_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    status ENUM('enabled', 'disabled') NOT NULL DEFAULT 'enabled',
    join_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE plants (
    plant_id INT AUTO_INCREMENT PRIMARY KEY,
    gardener_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    species VARCHAR(100) NOT NULL,
    plant_type ENUM('indoor', 'outdoor') NOT NULL,
    water_frequency_days INT NOT NULL,
    sunlight ENUM('Full Sun', 'Partial Sun', 'Full Shade', 'Indirect Light', 'Low Light') NOT NULL,
    difficulty ENUM('Easy', 'Moderate', 'Challenging') NOT NULL,
    is_public BOOLEAN NOT NULL DEFAULT FALSE,
    health_status ENUM('Healthy', 'Needs Attention', 'Sick') NOT NULL DEFAULT 'Healthy',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (gardener_id) REFERENCES gardeners(gardener_id)
);

CREATE TABLE care_activities (
    activity_id INT AUTO_INCREMENT PRIMARY KEY,
    plant_id INT NOT NULL,
    activity_type ENUM('Watering', 'Fertilizing', 'Pruning', 'Repotting', 'Inspection', 'Other') NOT NULL,
    notes TEXT,
    activity_date DATETIME NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plant_id) REFERENCES plants(plant_id)
);

CREATE TABLE plant_photos (
    photo_id INT AUTO_INCREMENT PRIMARY KEY,
    plant_id INT NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    caption VARCHAR(255),
    uploaded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plant_id) REFERENCES plants(plant_id)
);

USE plant_tracker_db;

INSERT INTO admins (username, email, password_hash)
VALUES (
    'admin',
    'admin@test.com',
    'scrypt:32768:8:1$bSY3QBUwQizT9UGS$8a8317b4af6112ba7137600b136c5601f961695300ca16132c84384717055be3badf7ca211c6a7e4dbb5f98a86212a4bb396ee4910fa1d596e6df5c2bcce90d2'
);
# admin123

select * from plants;
select *from admins;
delete from admins where admin_id=1;
SELECT gardener_id, username, email, status, password_hash
FROM gardeners;
UPDATE gardeners
SET password_hash = 'scrypt:32768:8:1$rBvApBz6QoIgaqvg$bf5497a9496e6c9576dab89b124e72f220959e18e598c79ab9aafddbb9cb2d83160e9540eb10dd0450c3c40dd562f38e375b784492e09339a0baedde98b7a9ac',
    status = 'enabled'
WHERE username = 'Xu.weihao';