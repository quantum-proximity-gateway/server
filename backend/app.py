from litestar import Litestar, get
from litestar.plugins.sqlalchemy import SQLAlchemyAsyncConfig, SQLAlchemyPlugin
from sqlalchemy import ForeignKey, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, selectinload
from sqlalchemy.ext.asyncio import AsyncSession


class Base(DeclarativeBase):
    pass


class Device(Base):
    __tablename__ = 'devices'

    mac_address: Mapped[str] = mapped_column(primary_key=True)
    username: Mapped[str]
    password: Mapped[str]
    key: Mapped[str]
    preferences: Mapped['Preferences'] = relationship(back_populates='device', uselist=False)


class Preferences(Base):
    __tablename__ = 'preferences'

    mac_address: Mapped[str] = mapped_column(
        ForeignKey('devices.mac_address', ondelete='CASCADE'),
        primary_key=True
    )
    settings: Mapped[str]
    device: Mapped[Device] = relationship(back_populates='preferences')


@get('/devices')
async def get_devices(db_session: AsyncSession) -> list[Device]:
    query = select(Device).options(selectinload(Device.preferences))
    result = await db_session.execute(query)
    devices = result.scalars().all()
    return devices

# register device

# validate key

# regenerate key

# retrieve preferences for device

# update preferences for device

db_config = SQLAlchemyAsyncConfig(
    connection_string='sqlite+aiosqlite:///db.sqlite',
    metadata=Base.metadata,
    create_all=True
)
sqlalchemy_plugin = SQLAlchemyPlugin(config=db_config)

app = Litestar(
    route_handlers=[get_devices],
    plugins=[sqlalchemy_plugin],
    debug=True
)