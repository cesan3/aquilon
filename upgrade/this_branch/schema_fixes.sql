ALTER TABLE location_link RENAME CONSTRAINT "LINK_CHILD_LOCATION_FK" TO "LOCATION_LINK_CHILD_FK";
ALTER TABLE location_link RENAME CONSTRAINT "LINK_PARENT_LOCATION_FK" TO "LOCATION_LINK_PARENT_FK";
ALTER TABLE location_link MODIFY (child_id INTEGER NULL);
ALTER TABLE location_link MODIFY (child_id INTEGER CONSTRAINT "LOCATION_LINK_CHILD_ID_NN" NOT NULL);
ALTER TABLE location_link MODIFY (parent_id INTEGER NULL);
ALTER TABLE location_link MODIFY (parent_id INTEGER CONSTRAINT "LOCATION_LINK_PARENT_ID_NN" NOT NULL);
ALTER TABLE location_link MODIFY (distance INTEGER NULL);
ALTER TABLE location_link MODIFY (distance INTEGER CONSTRAINT "LOCATION_LINK_DISTANCE_NN" NOT NULL);
ALTER TABLE location_link DROP PRIMARY KEY;
ALTER TABLE location_link ADD CONSTRAINT "LOCATION_LINK_PK" PRIMARY KEY (child_id, parent_id);

QUIT;