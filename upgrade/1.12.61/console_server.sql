CREATE TABLE console_server (
	hardware_entity_id NUMBER(*,0) CONSTRAINT CONSOLE_SERVER_HW_ENT_ID_NN NOT NULL,
	CONSTRAINT console_server_hw_ent_fk FOREIGN KEY (hardware_entity_id) REFERENCES hardware_entity (id) ON DELETE CASCADE,
	CONSTRAINT console_server_pk PRIMARY KEY (hardware_entity_id)
);

CREATE TABLE console_port (
	console_server_id NUMBER(*,0) CONSTRAINT console_port_consrv_id_nn NOT NULL,
	client_id NUMBER(*,0) CONSTRAINT console_port_client_id_nn NOT NULL,
	client_port VARCHAR2(16 CHAR) CONSTRAINT console_port_client_port_nn NOT NULL,
	creation_date DATE CONSTRAINT console_port_creation_date_nn NOT NULL,
	port_number NUMBER(*,0) CONSTRAINT console_port_port_number_nn NOT NULL,
	CONSTRAINT console_port_client_port_uk UNIQUE (client_id, client_port),
	CONSTRAINT console_port_console_server_fk FOREIGN KEY (console_server_id) REFERENCES console_server (hardware_entity_id) ON DELETE CASCADE,
	CONSTRAINT console_port_hw_ent_fk FOREIGN KEY (client_id) REFERENCES hardware_entity (id) ON DELETE CASCADE,
	CONSTRAINT console_port_pk PRIMARY KEY (console_server_id, port_number)
);

QUIT;
