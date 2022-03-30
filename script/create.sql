create schema filetransfer;
use filetransfer;
DROP TABLE IF EXISTS `user`;
DROP TABLE IF EXISTS `fileinfo`;
-- user
CREATE TABLE `user`
(
	`username` VARCHAR(20) CHARACTER SET UTF8 COLLATE UTF8_BIN NOT NULL,
	`password` VARCHAR(20) CHARACTER SET UTF8 COLLATE UTF8_BIN NOT NULL,
    	`last_time` LONG NOT NULL,
	PRIMARY KEY(`username`)
);

-- fileInfo
CREATE TABLE `fileinfo`
(
	`filename` VARCHAR(20) CHARACTER SET UTF8 COLLATE UTF8_BIN NOT NULL,
	`filepath` VARCHAR(200) CHARACTER SET UTF8 COLLATE UTF8_BIN NOT NULL,
    	`upload_time` LONG NOT NULL,
	`username` VARCHAR(20) CHARACTER SET UTF8 COLLATE UTF8_BIN NOT NULL,
	`size` VARCHAR(20) CHARACTER SET UTF8 COLLATE UTF8_BIN NOT NULL
);

SELECT COUNT(*) count, table_schema FROM INFORMATION_SCHEMA.TABLES WHERE table_schema = 'filetransfer' GROUP BY table_schema;