BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "keys" (
	"userid"	    TEXT NOT NULL UNIQUE,
	"pubkey"	    TEXT NOT NULL,
	"privkey"	    TEXT NOT NULL,
	"user_pubkey"	TEXT,
	PRIMARY KEY("userid")
);
COMMIT;
