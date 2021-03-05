from os import getenv

from databases import Database


DATABASE_URL = getenv("POSTGRES_URL", "postgresql://postgres:password@localhost:5432/erupe?sslmode=disable")
database = Database(DATABASE_URL)
