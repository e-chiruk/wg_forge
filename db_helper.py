from psycopg2.extras import RealDictCursor

class Base(object):
    __tablename__ = None

    def __init__(self, connection):
        if self.__tablename__ is None:
            raise ValueError('Table name is not defined')
        self.connection = connection

    def _cursor(self):
        return self.connection.cursor(cursor_factory=RealDictCursor)

    def _all(self, params=None):
        cursor = self._cursor()
        if params is None:
            params = ''
        cursor.execute(
            'SELECT * FROM {}{}'.format(self.__tablename__, params)
        )
        return cursor.fetchall()

    def _columns(self):
        cursor = self._cursor()
        cursor.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = '{}'".format(self.__tablename__)
        )
        return cursor.fetchall()

    def _count(self):
        cursor = self._cursor()
        cursor.execute(
            'SELECT count(*) FROM {}'.format(self.__tablename__)
        )
        return int(cursor.fetchone()['count'])

    def _insert(self, columns, values):
        cursor = self._cursor()
        placeholders = ('%s, ' * len(columns)).strip(', ')
        columns = '", "'.join(columns)
        columns = '"{}"'.format(columns)
        statement = 'INSERT INTO {table} ({cols}) VALUES({places})'.format(
            table=self.__tablename__,
            cols=columns,
            places=placeholders
        )
        cursor.execute(statement, values)
        self.connection.commit()

    def _update(self, columns, values, key, value):
        self._cursor().execute(
            'UPDATE {table} SET "{values}" = %s WHERE {key} = %s'.format(
                table=self.__tablename__,
                values='" = %s, "'.join(columns),
                key=key
            ),
            list(values) + [value]
        )
        self.connection.commit()

    def _delete(self, key, value):
        self._cursor().execute('DELETE FROM {} WHERE "{}" = %s'.format(self.__tablename__, key), [value])
        self.connection.commit()

    def _find(self, key, value):
        cursor = self._cursor()
        cursor.execute('SELECT * FROM {} WHERE "{}" = %s'.format(self.__tablename__, key), (value,))
        return cursor.fetchone()


class Cats(Base):
    __tablename__ = 'cats'

    def all(self, attribute, order, limit, offset):
        params = None
        if attribute is not None and order is not None and limit is not None and offset is not None:
            params = ' ORDER BY {0} {1} LIMIT {2} OFFSET {3}'.format(attribute, order, limit, offset)
            return self._all(params=params)
        if limit is not None and offset is not None:
            params = ' LIMIT {} OFFSET {}'.format(limit, offset)
            return self._all(params=params)
        if attribute is not None and order is not None:
            params = ' ORDER BY {} {}'.format(attribute, order)
        return self._all(params=params)


    def add(self, name, color, tail_length, whiskers_length):
        columns = ('name', 'color', 'tail_length', 'whiskers_length')
        values = (name, color, tail_length, whiskers_length)
        self._insert(columns=columns, values=values)

    def find(self, name):
        return self._find('name', name)

    def get_colors(self):
        cursor = self._cursor()
        cursor.execute('SELECT unnest(enum_range(NULL::cat_color))')
        colors =[]
        for row in cursor.fetchall():
            colors.append(row['unnest'])
        return colors

    def get_attributes(self):
        attributes = []
        for row in self._columns():
            attributes.append(row['column_name'])
        return attributes

    def count(self):
        return self._count()

    def delete(self, column, value):
        self._delete(column, value)

class CatColorsInfo(Base):
    __tablename__ = 'cat_colors_info'

    def get_color_info(self):
        if self._count() == 0:
            cursor = self._cursor()
            cursor.execute('INSERT INTO {} (color, count) '
                           'SELECT color, count(color) FROM public.cats GROUP BY color;'.format(self.__tablename__))
            self.connection.commit()
        else:
            cursor = self._cursor()
            cursor.execute('UPDATE {} SET count = (SELECT count(color) FROM public.cats '
                           'WHERE cats.color = cat_colors_info.color)'.format(self.__tablename__))
            self.connection.commit()
        return self._all()

class CatsStat(Base):
    __tablename__ = 'cats_stat'

    def _get_mean(self, table, column):
        cursor = self._cursor()
        cursor.execute('SELECT avg({0}) FROM {1}'.format(column, table))
        return cursor.fetchone()['avg']

    def _get_median(self, table, column):
        cursor = self._cursor()
        cursor.execute('SELECT percentile_disc(0.5) WITHIN GROUP (ORDER BY {0}) '
                       'FROM {1}'.format(column, table))
        return cursor.fetchone()['percentile_disc']

    def _get_mode(self, table, column):
        cursor = self._cursor()
        cursor.execute('SELECT {0} FROM {1} '
                       'GROUP BY {0} HAVING count(*) >= '
                       'ALL(SELECT count(*) FROM {1} GROUP BY {0});'.format(column, table))
        mode = []
        for row in cursor.fetchall():
            mode.append(row[column])
        mode = str(mode)
        mode = mode.replace('[', '\'{').replace(']', '}\'')
        return mode

    def get_cats_stat(self):
        cursor = self._cursor()
        if self._count() != 0:
            cursor.execute('DELETE FROM {}'.format(self.__tablename__))
            self.connection.commit()

        cursor.execute('INSERT INTO {0} (tail_length_mean, tail_length_median, tail_length_mode, '
                       'whiskers_length_mean, whiskers_length_median, whiskers_length_mode) '
                       'VALUES({1}, {2}, {3}, {4}, {5}, {6})'
                       .format(self.__tablename__, self._get_mean('cats', 'tail_length'),
                                   self._get_median('cats', 'tail_length'), self._get_mode('cats', 'tail_length'),
                                   self._get_mean('cats', 'whiskers_length'), self._get_median('cats', 'whiskers_length'),
                                   self._get_mode('cats', 'whiskers_length')))
        self.connection.commit()
        return self._all()