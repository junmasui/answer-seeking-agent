Generic single-database configuration.


```
PYTHONPATH=./src alembic revision --autogenerate -m "Added tracking columns"
```

```
PYTHONPATH=./src alembic upgrade
```