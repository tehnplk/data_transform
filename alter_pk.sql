ALTER TABLE transform_sync_bed_type_all DROP CONSTRAINT IF EXISTS pk_transform_sync_bed_type_all CASCADE;
ALTER TABLE transform_sync_bed_type_all ADD CONSTRAINT pk_transform_sync_bed_type_all PRIMARY KEY (hoscode, export_code, bedno, roomno);
ALTER TABLE transform_sync_bed_type_all ALTER COLUMN bedtype DROP NOT NULL;
