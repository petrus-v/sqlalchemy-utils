from datetime import date, datetime, time

import pytest
import sqlalchemy as sa

from sqlalchemy_utils import ColorType, EncryptedType, PhoneNumberType
from sqlalchemy_utils.types.encrypted.encrypted_type import (
    AesEngine,
    DatetimeHandler,
    FernetEngine
)

cryptography = None
try:
    import cryptography  # noqa
except ImportError:
    pass


@pytest.fixture
def User(Base, encryption_engine, test_key, padding_mechanism):
    class User(Base):
        __tablename__ = 'user'
        id = sa.Column(sa.Integer, primary_key=True)

        username = sa.Column(EncryptedType(
            sa.Unicode,
            test_key,
            encryption_engine,
            padding_mechanism)
        )

        access_token = sa.Column(EncryptedType(
            sa.String,
            test_key,
            encryption_engine,
            padding_mechanism)
        )

        is_active = sa.Column(EncryptedType(
            sa.Boolean,
            test_key,
            encryption_engine,
            padding_mechanism)
        )

        accounts_num = sa.Column(EncryptedType(
            sa.Integer,
            test_key,
            encryption_engine,
            padding_mechanism)
        )

        phone = sa.Column(EncryptedType(
            PhoneNumberType,
            test_key,
            encryption_engine,
            padding_mechanism)
        )

        color = sa.Column(EncryptedType(
            ColorType,
            test_key,
            encryption_engine,
            padding_mechanism)
        )

        date = sa.Column(EncryptedType(
            sa.Date,
            test_key,
            encryption_engine,
            padding_mechanism)
        )

        time = sa.Column(EncryptedType(
            sa.Time,
            test_key,
            encryption_engine,
            padding_mechanism)
        )

        datetime = sa.Column(EncryptedType(
            sa.DateTime,
            test_key,
            encryption_engine,
            padding_mechanism)
        )

        enum = sa.Column(EncryptedType(
            sa.Enum('One', name='user_enum_t'),
            test_key,
            encryption_engine,
            padding_mechanism)
        )

    return User


@pytest.fixture
def test_key():
    return 'secretkey1234'


@pytest.fixture
def user_name():
    return u'someone'


@pytest.fixture
def user_phone():
    return u'(555) 555-5555'


@pytest.fixture
def user_color():
    return u'#fff'


@pytest.fixture
def user_enum():
    return 'One'


@pytest.fixture
def user_date():
    return date(2010, 10, 2)


@pytest.fixture
def user_time():
    return time(10, 12)


@pytest.fixture
def user_datetime():
    return datetime(2010, 10, 2, 10, 12, 45, 2334)


@pytest.fixture
def test_token():
    import string
    import random
    token = ''
    characters = string.ascii_letters + string.digits
    for i in range(60):
        token += ''.join(random.choice(characters))
    return token


@pytest.fixture
def active():
    return True


@pytest.fixture
def accounts_num():
    return 2


@pytest.fixture
def user(
    request,
    session,
    User,
    user_name,
    user_phone,
    user_color,
    user_date,
    user_time,
    user_enum,
    user_datetime,
    test_token,
    active,
    accounts_num
):
    # set the values to the user object
    user = User()
    user.username = user_name
    user.phone = user_phone
    user.color = user_color
    user.date = user_date
    user.time = user_time
    user.enum = user_enum
    user.datetime = user_datetime
    user.access_token = test_token
    user.is_active = active
    user.accounts_num = accounts_num
    session.add(user)
    session.commit()

    return session.query(User).get(user.id)


@pytest.fixture
def datetime_with_micro_and_timezone():
    import pytz
    tz = pytz.timezone('Pacific/Tahiti')
    return datetime(2017, 8, 21, 4, 26, 36, 523010, tzinfo=tz)


@pytest.fixture
def datetime_with_micro():
    return datetime(2017, 8, 21, 10, 12, 45, 22)


@pytest.fixture
def datetime_simple():
    return datetime(2017, 8, 21, 10, 12, 45)


@pytest.fixture
def time_with_micro():
    return time(10, 12, 45, 22)


@pytest.fixture
def time_simple():
    return time(10, 12, 45)


@pytest.fixture
def date_simple():
    return date(2017, 8, 21)


@pytest.mark.skipif('cryptography is None')
class EncryptedTypeTestCase(object):

    @pytest.fixture
    def Team(self, Base, encryption_engine, padding_mechanism):
        self._team_key = None

        class Team(Base):
            __tablename__ = 'team'
            id = sa.Column(sa.Integer, primary_key=True)
            key = sa.Column(sa.String(50))
            name = sa.Column(EncryptedType(
                sa.Unicode,
                lambda: self._team_key,
                encryption_engine,
                padding_mechanism)
            )
        return Team

    @pytest.fixture
    def init_models(self, User, Team):
        pass

    def test_unicode(self, user, user_name):
        assert user.username == user_name

    def test_string(self, user, test_token):
        assert user.access_token == test_token

    def test_boolean(self, user, active):
        assert user.is_active == active

    def test_integer(self, user, accounts_num):
        assert user.accounts_num == accounts_num

    def test_phone_number(self, user, user_phone):
        assert str(user.phone) == user_phone

    def test_color(self, user, user_color):
        assert user.color.hex == user_color

    def test_date(self, user, user_date):
        assert user.date == user_date

    def test_datetime(self, user, user_datetime):
        assert user.datetime == user_datetime

    def test_time(self, user, user_time):
        assert user.time == user_time

    def test_enum(self, user, user_enum):
        assert user.enum == user_enum

    def test_lookup_key(self, session, Team):
        # Add teams
        self._team_key = 'one'
        team = Team(key=self._team_key, name=u'One')
        session.add(team)
        session.commit()
        team_1_id = team.id

        self._team_key = 'two'
        team = Team(key=self._team_key)
        team.name = u'Two'
        session.add(team)
        session.commit()
        team_2_id = team.id

        # Lookup teams
        self._team_key = session.query(Team.key).filter_by(
            id=team_1_id
        ).one()[0]

        team = session.query(Team).get(team_1_id)

        assert team.name == u'One'

        session.expunge_all()

        self._team_key = session.query(Team.key).filter_by(
            id=team_2_id
        ).one()[0]

        team = session.query(Team).get(team_2_id)

        assert team.name == u'Two'

        session.expunge_all()

        # Remove teams
        session.query(Team).delete()
        session.commit()


class AesEncryptedTypeTestCase(EncryptedTypeTestCase):

    @pytest.fixture
    def encryption_engine(self):
        return AesEngine

    def test_lookup_by_encrypted_string(self, session, User, user, user_name):
        test = session.query(User).filter(
            User.username == user_name
        ).first()

        assert test.username == user.username


class TestAesEncryptedTypeWithPKCS5Padding(AesEncryptedTypeTestCase):

    @pytest.fixture
    def padding_mechanism(self):
        return 'pkcs5'


class TestAesEncryptedTypeWithOneAndZeroesPadding(AesEncryptedTypeTestCase):

    @pytest.fixture
    def padding_mechanism(self):
        return 'oneandzeroes'


class TestAesEncryptedTypeWithZeroesPadding(AesEncryptedTypeTestCase):

    @pytest.fixture
    def padding_mechanism(self):
        return 'zeroes'


class TestAesEncryptedTypeTestcaseWithNaivePadding(AesEncryptedTypeTestCase):

    @pytest.fixture
    def padding_mechanism(self):
        return 'naive'

    def test_decrypt_raises_value_error_with_invalid_key(self, session, Team):
        self._team_key = 'one'
        team = Team(key=self._team_key, name=u'One')
        session.add(team)
        session.commit()

        self._team_key = 'notone'
        with pytest.raises(ValueError):
            assert team.name == u'One'


class TestFernetEncryptedTypeTestCase(EncryptedTypeTestCase):

    @pytest.fixture
    def encryption_engine(self):
        return FernetEngine

    @pytest.fixture
    def padding_mechanism(self):
        return None


class TestDatetimeHandler(object):

    def test_datetime_with_micro_and_timezone(self):
        original_datetime = datetime_with_micro_and_timezone()
        original_datetime_isoformat = original_datetime.isoformat()
        python_type = datetime

        assert DatetimeHandler.process_value(
            original_datetime_isoformat,
            python_type
        ) == original_datetime

    def test_datetime_with_micro(self):
        original_datetime = datetime_with_micro()
        original_datetime_isoformat = original_datetime.isoformat()
        python_type = datetime

        assert DatetimeHandler.process_value(
            original_datetime_isoformat,
            python_type
        ) == original_datetime

    def test_datetime_simple(self):
        original_datetime = datetime_simple()
        original_datetime_isoformat = original_datetime.isoformat()
        python_type = datetime

        assert DatetimeHandler.process_value(
            original_datetime_isoformat,
            python_type
        ) == original_datetime

    def test_time_with_micro(self):
        original_time = time_with_micro()
        original_time_isoformat = original_time.isoformat()
        python_type = time

        assert DatetimeHandler.process_value(
            original_time_isoformat,
            python_type
        ) == original_time

    def test_time_simple(self):
        original_time = time_simple()
        original_time_isoformat = original_time.isoformat()
        python_type = time

        assert DatetimeHandler.process_value(
            original_time_isoformat,
            python_type
        ) == original_time

    def test_date_simple(self):
        original_date = date_simple()
        original_date_isoformat = original_date.isoformat()
        python_type = date

        assert DatetimeHandler.process_value(
            original_date_isoformat,
            python_type
        ) == original_date
