DROP TABLE IF EXISTS "devices";
DROP TABLE IF EXISTS "preferences";

CREATE TABLE "devices" (
  "mac_address" PRIMARY KEY,
  "username" TEXT NOT NULL,
  "password" TEXT NOT NULL,
  "key" TEXT NOT NULL,
  "last_used" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "registered_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE "preferences" (
    "mac_address" TEXT PRIMARY KEY,
    "preferences" TEXT NOT NULL,
    FOREIGN KEY ("mac_address") REFERENCES "devices" ("mac_address")
);