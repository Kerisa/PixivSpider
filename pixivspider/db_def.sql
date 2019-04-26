DROP TABLE IF EXISTS creator;
DROP TABLE IF EXISTS illust;
DROP TABLE IF EXISTS download_failed;

CREATE TABLE `creator` (
	`id`	INTEGER PRIMARY KEY NOT NULL UNIQUE,
	`name`	TEXT,
	`add_time`	TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	`comment`	TEXT
);

CREATE TABLE `illust` (
	`id`	INTEGER PRIMARY KEY NOT NULL UNIQUE,
	`author_id`	INTEGER NOT NULL,
	`name`	TEXT,
	`type`	TEXT,
	`tags`	TEXT,
	`json_blob`  TEXT,
	`download_time`	TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	`sub_img_count`	INTEGER,
	FOREIGN KEY (author_id) REFERENCES creator (id)
);

CREATE TABLE `download_failed` (
    `illust_id` INTEGER PRIMARY KEY NOT NULL UNIQUE,
	`author_id`	INTEGER NOT NULL,
    `url` TEXT,
    `add_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `last_time` TIMESTAMP,
	FOREIGN KEY (author_id) REFERENCES creator (id)
);