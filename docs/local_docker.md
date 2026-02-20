# Local Docker Details

## PostgreSQL

- **Container Name**: `postgres`
- **Database**: `datacenter`
- **User**: `admin`
- **Password**: `112233` (Based on `transform` scripts)
- **Port**: `5433` (Internal)

## Useful Commands

### Access psql

```bash
docker exec -it postgres psql -U admin -d datacenter
```

### Run Query

```bash
docker exec postgres psql -U admin -d datacenter -c "SELECT * FROM transform_sync_drgs_rw_top10 LIMIT 10;"
```

### Backup (Dump)

```bash
docker exec postgres pg_dump -U admin -F c datacenter > datacenter_local.dump
```

### Restore

```bash
docker exec -i postgres pg_restore -U admin -d datacenter < datacenter_local.dump
```
