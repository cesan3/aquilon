-- This is from a previous upgrade.
DROP TABLE RACK_SAVE;

-- These are all duplicate constraints.
ALTER TABLE "HOST" DROP CONSTRAINT "SYS_C0046943";
ALTER TABLE "ARCHETYPE" DROP CONSTRAINT "SYS_C0046943";
ALTER TABLE "HOST" DROP CONSTRAINT "HOST_PERSONALITY_ID_NN";

COMMIT;
