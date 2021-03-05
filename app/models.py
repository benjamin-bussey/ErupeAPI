from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects import postgresql
import time

import sqlalchemy

metadata = sqlalchemy.MetaData()

user = sqlalchemy.Table(
    "users",
    metadata,
    Column("id", postgresql.INTEGER, primary_key=True, index=True),
    Column("username", postgresql.TEXT),
    Column("password", postgresql.TEXT),
)

character = sqlalchemy.Table(
    "characters",
    metadata,
    Column("id", postgresql.INTEGER, primary_key=True, index=True),
    Column("user_id", postgresql.INTEGER, ForeignKey('users.id')),
    Column("is_female", postgresql.BOOLEAN, default=False),
    Column("is_new_character", postgresql.BOOLEAN, default=True),
    Column("small_gr_level", postgresql.INTEGER, default=0),
    Column("gr_override_mode", postgresql.BOOLEAN, default=True),
    Column("name", postgresql.VARCHAR(length=15), default=''),
    Column("unk_desc_string", postgresql.VARCHAR(length=31), default=''),
    Column("gr_override_level", postgresql.INTEGER, default=0),
    Column("gr_override_unk0", postgresql.INTEGER, default=0),
    Column("gr_override_unk1", postgresql.INTEGER, default=0),
    Column("exp", postgresql.INTEGER, default=0),
    Column("weapon", postgresql.INTEGER, default=0),
    Column("last_login", postgresql.INTEGER, default=int(time.time())),
    Column("savedata", postgresql.BYTEA),
    Column("decomyset", postgresql.BYTEA),
    Column("hunternavi", postgresql.BYTEA),
    Column("otomoairou", postgresql.BYTEA),
    Column("partner", postgresql.BYTEA),
    Column("platebox", postgresql.BYTEA),
    Column("platedata", postgresql.BYTEA),
    Column("platemyset", postgresql.BYTEA),
    Column("rengokudata", postgresql.BYTEA),
    Column("savemercenary", postgresql.BYTEA),
    Column("restrict_guild_scout", postgresql.BOOLEAN, nullable=False, default=False)
)

guild = sqlalchemy.Table(
    "guilds",
    metadata,
    Column("id", postgresql.INTEGER, primary_key=True, index=True),
    Column("name", postgresql.VARCHAR(length=24)),
    Column("created_at", postgresql.TIMESTAMP, default=int(time.time())),
    Column("leader_id", postgresql.INTEGER, ForeignKey('users.id'), nullable=False),
    Column("main_motto", postgresql.VARCHAR(length=255), default=""),
    Column("rp", postgresql.INTEGER, default=0),
    Column("comment", postgresql.VARCHAR(length=255), nullable=False, default=""),
    Column("festival_colour", postgresql.ENUM("none", "red", "blue", name="festival_colour", create_type=False),
           default="none"),
    Column("guild_hall", postgresql.INTEGER, default=0)
)

guild_characters = sqlalchemy.Table(
    "guild_characters",
    metadata,
    Column("id", postgresql.INTEGER, primary_key=True, index=True),
    Column("guild_id", postgresql.INTEGER, ForeignKey("guilds.id")),
    Column("character_id", postgresql.INTEGER, ForeignKey("characters.id")),
    Column("joined_at", postgresql.TIMESTAMP, default=int(time.time())),
    Column("is_applicant", postgresql.BOOLEAN, nullable=False, default=False),
    Column("is_sub_leader", postgresql.BOOLEAN, nullable=False, default=False),
    Column("order_index", postgresql.INTEGER, default=1)
)
