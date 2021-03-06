ALTER TABLE disk ADD backing_store_id INTEGER;
ALTER TABLE disk ADD CONSTRAINT disk_backing_store_fk FOREIGN KEY (backing_store_id) REFERENCES "resource" (id);
UPDATE disk SET backing_store_id = share_id WHERE share_id IS NOT NULL;
UPDATE disk SET backing_store_id = filesystem_id WHERE filesystem_id IS NOT NULL;
UPDATE disk SET disk_type = 'virtual_disk' WHERE disk_type = 'virtual_localdisk';
ALTER TABLE disk DROP COLUMN share_id;
ALTER TABLE disk DROP COLUMN filesystem_id;
CREATE INDEX disk_backing_store_idx ON disk (backing_store_id);
QUIT;
