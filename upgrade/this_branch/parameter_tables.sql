/* create tables */
CREATE TABLE param_def_holder (
        id integer CONSTRAINT "PARAM_DEF_HOLDER_ID_NN" NOT NULL,
        type VARCHAR(16) CONSTRAINT "PARAM_DEF_HOLDER_TYPE_NN" NOT NULL,
        creation_date DATE CONSTRAINT "PARAM_DEF_HOLDER_CR_DATE_NN" NOT NULL,
        archetype_id INTEGER,
        feature_id INTEGER,
        CONSTRAINT "PARAM_DEF_HOLDER_FEATURE_UK" UNIQUE (feature_id),
        CONSTRAINT "PARAM_DEF_HOLDER_ARCHETYPE_UK" UNIQUE (archetype_id),
	CONSTRAINT "PARAM_DEF_HOLDER_ARCHETYPE_FK" FOREIGN KEY (archetype_id) REFERENCES archetype (id) ON DELETE CASCADE,
        CONSTRAINT "PARAM_DEF_HOLDER_FEATURE_FK" FOREIGN KEY (feature_id) REFERENCES feature (id) ON DELETE CASCADE,
        CONSTRAINT "PARAM_DEF_HOLDER_PK" PRIMARY KEY (id)
);

CREATE TABLE param_definition (
        id integer CONSTRAINT "PARAM_DEFINITION_ID_NN" NOT NULL,
        path VARCHAR(255) CONSTRAINT "PARAM_DEFINITION_PATH_NN" NOT NULL,
        template VARCHAR(32),
        required integer CONSTRAINT "PARAM_DEFINITION_REQUIRED_NN" NOT NULL,
        value_type VARCHAR(16) CONSTRAINT "PARAM_DEFINITION_VALUE_TYPE_NN" NOT NULL,
        "default" CLOB,
        description VARCHAR(255),
        holder_id INTEGER,
        creation_date DATE CONSTRAINT "PARAM_DEFINITION_CR_DATE_NN" NOT NULL,
	CONSTRAINT "PARAM_DEFINITION_HOLDER_FK" FOREIGN KEY (holder_id) REFERENCES param_def_holder (id) ON DELETE CASCADE,
        CONSTRAINT "PARAM_DEFINITION_PK" PRIMARY KEY (id),
        CONSTRAINT "PARAM_DEFINITION_PARAMDEF_CK" CHECK (required IN (0, 1))
);

CREATE TABLE param_holder (
        id integer CONSTRAINT "PARAM_HOLDER_ID_NN" NOT NULL,
        creation_date DATE CONSTRAINT "PARAM_HOLDER_CR_DATE_NN" NOT NULL,
        holder_type VARCHAR(16) CONSTRAINT "PARAM_HOLDER_HOLDER_TYPE_NN" NOT NULL,
        personality_id INTEGER,
        featurelink_id INTEGER,
	CONSTRAINT "PARAM_HOLDER_FLINK_UK" UNIQUE (featurelink_id),
	CONSTRAINT "PARAM_HOLDER_PERSONA_UK" UNIQUE (personality_id),
	CONSTRAINT "PARAM_HOLDER_FEATURELINK_FK" FOREIGN KEY (featurelink_id) REFERENCES feature_link (id) ON DELETE CASCADE,
        CONSTRAINT "PARAM_HOLDER_PERSONA_FK" FOREIGN KEY (personality_id) REFERENCES personality (id) ON DELETE CASCADE,
        CONSTRAINT "PARAM_HOLDER_PK" PRIMARY KEY (id)
);

CREATE TABLE parameter (
        id integer CONSTRAINT "PARAMETER_ID_NN" NOT NULL,
        value CLOB,
        creation_date DATE CONSTRAINT "PARAMETER_CR_DATE_NN" NOT NULL,
        comments VARCHAR(255),
        holder_id INTEGER,
	CONSTRAINT "PARAMETER_PARAMHOLDER_FK" FOREIGN KEY (holder_id) REFERENCES param_holder (id) ON DELETE CASCADE,
        CONSTRAINT "PARAMETER_PK" PRIMARY KEY (id)
);

CREATE SEQUENCE PARAMETER_SEQ;
CREATE SEQUENCE PARAM_DEFINITION_SEQ;
CREATE SEQUENCE PARAM_DEF_HOLDER_SEQ;
CREATE SEQUENCE PARAM_HOLDER_SEQ;

COMMIT;
QUIT;
