DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN
        SELECT c.table_name, c.column_name
        FROM information_schema.columns c
        WHERE c.table_schema = 'public' 
          AND c.table_name LIKE 'transform_%'
          AND c.is_nullable = 'NO'
          AND c.column_name NOT IN (
              SELECT a.attname
              FROM pg_index i
              JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
              JOIN pg_class t ON t.oid = i.indrelid
              WHERE t.relname = c.table_name AND i.indisprimary
          )
    LOOP
        RAISE NOTICE 'Altering %.%', r.table_name, r.column_name;
        EXECUTE 'ALTER TABLE ' || quote_ident(r.table_name) || ' ALTER COLUMN ' || quote_ident(r.column_name) || ' DROP NOT NULL';
    END LOOP;
END $$;
