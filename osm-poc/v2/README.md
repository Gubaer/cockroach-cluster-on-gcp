# Version 2 of the OSM POC

# Sample Queries

Select the number of nodes

```sql
> select count(1) from osm.nodes;
```

Select the number nodes representing a hotel
```sql
> select count(1) from osm.nodes
  where tags @> '{"tourism":"hotel"}';
```

Select the first 100 names of the available hotels. Note, that we can't sort
by `tags->'name'`
```sql
> select tags->'name' from osm.nodes
  where tags @> '{"tourism":"hotel"}'
  limit 100;
```
