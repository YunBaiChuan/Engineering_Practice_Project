CREATE DATABASE IF NOT EXISTS campus_agent_db 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE campus_agent_db;

CREATE TABLE IF NOT EXISTS `users` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '用户ID',
    `username` VARCHAR(50) NOT NULL COMMENT '学号',
    `password` VARCHAR(255) NOT NULL COMMENT '密码（加密存储）',
    `name` VARCHAR(100) DEFAULT NULL COMMENT '姓名',
    `status` TINYINT DEFAULT 1 COMMENT '状态：0禁用，1启用',
    `last_login` DATETIME DEFAULT NULL COMMENT '最后登录时间',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';