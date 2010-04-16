ALTER TABLE ESX_CLUSTER ADD (SWITCH_ID INTEGER DEFAULT NULL);
commit;

ALTER TABLE "ESX_CLUSTER" ADD CONSTRAINT "ESX_CLUSTER_SWITCH_FK" FOREIGN KEY ("SWITCH_ID") REFERENCES "TOR_SWITCH" ("ID") ENABLE;
commit;
