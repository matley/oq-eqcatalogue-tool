# Copyright (c) 2010-2012, GEM Foundation.
#
# eqcatalogueTool is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# eqcatalogueTool is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with eqcatalogueTool. If not, see <http://www.gnu.org/licenses/>.

"""
The module  provides the API to create and access
the database.

Moreover, it contains the class definitions of the basic domain models
stored into the db (eventsources, events, measures, origins and
measure metadata).
"""


DEFAULT_ENGINE = 'eqcatalogue.datastores.spatialite'

SCALES = ('mL', 'mb', 'Mb',
          'Ms', 'md', 'MD',
          'MS', 'mb1', 'mb1mx',
          'ms1', 'ms1mx', 'ML',
          'Ms1', 'mbtmp', 'Ms7',
          'mB', 'Md', 'Ml', 'M',
          'MG', 'ml', 'mpv',
          'mbLg', 'MW', 'Mw',
          'MLv', 'mbh', 'MN',
          'ME',
          'Muk'  # unknown magnitude (JMA)
    )

METADATA_TYPES = ('phases', 'stations',
                  'azimuth_gap', 'azimuth_error',
                  'min_distance', 'max_distance',
                  'num_stations')


class EventSource(object):
    """A source catalogue of seismic events. E.g. ISC Web Catalogue

    :attribute id:
      Internal identifier

    :attribute created_at:
      When this object has been imported into the catalogue db

    :attribute name:
      an unique event source short name.

    :attribyte agencies:
      a list of :py:class:`~eqcatalogue.models.Agency` instances
      imported by this eventsource

    :attribyte events:
      a list of :py:class:`~eqcatalogue.models.Event` instances
      imported by this eventsource

    :attribyte origins:
      a list of :py:class:`~eqcatalogue.models.Origin` instances
      imported by this eventsource
    """

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "EventSource %s" % self.name


class Agency(object):
    """
    The agency which recorded the measures.

    :attribute id:
      Internal identifier

    :attribute created_at:
      When this object has been imported into the catalogue db

    :attribute source_key:
      the identifier used by the event source for the object

    :attribute eventsource:
      the source object we have imported the agency from. It is unique
      together with `source_key`
    """
    def __repr__(self):
        return "Agency %s" % self.source_key

    def __init__(self, source_key, eventsource):
        self.source_key = source_key
        self.eventsource = eventsource


class Event(object):
    """
    Models a seismic event.

    :attribute id:
      Internal identifier

    :attribute created_at:
      When this object has been imported into the catalogue db

    :attribute source_key:
      the identifier used by the event source for the object

    :attribute name:
      an event short name

    :attribute eventsource:
      the source object we have imported the agency from. unique
      together with `source_key`
      """

    def __init__(self, source_key, eventsource, name=None):
        self.source_key = source_key
        self.eventsource = eventsource
        if name:
            self.name = name

    def __repr__(self):
        return "Event %s from %s" % (self.source_key,
                                     self.eventsource)


class MagnitudeMeasure(object):
    """
    Describes a single measure of the magnitude of an event

    :attribute id:
      Internal identifier

    :attribute created_at:
      When this object has been imported into the catalogue db

    :attribute event:
      the :py:class:`~eqcatalogue.models.Event`
      object associated with this measure

    :attribute agency:
      the :py:class:`~eqcatalogue.models.Agency`
      that has provided the measure

    :attribute origin:
      the origin related to this measure

    :attribute scale:
      the scale used for this measure.
      It is unique together with `agency_id` and `origin_id`

    :attribute value:
      the magnitude expressed in the unit suitable for the scale used

    :attribute standard_error:
      the standard error of the magnitude value
    """

    def __init__(self, agency, event, origin, scale, value,
                 standard_error=None):
        self.agency = agency
        self.event = event
        self.origin = origin
        self.scale = scale
        self.value = value
        self.standard_error = standard_error

    def __repr__(self):
        return "measure of %s at %s by %s: %s %s (sigma=%s)" % (
            self.event, self.origin, self.agency, self.value, self.scale,
            self.standard_error)

    @classmethod
    def make_from_lists(cls, scale, values, sigmas):
        """
        Returns a list of measures with the given scale, values and
        standard errors
        """
        return [cls(agency=None, event=None, origin=None,
                    scale=scale, value=v[0], standard_error=v[1])
                    for v in zip(values, sigmas)]

    def convert(self, new_value, formula, standard_error):
        """
        Convert the measure to a ConvertedMeasure with `new_value`
        through `formula`
        """
        return ConvertedMeasure(self.agency, self.event, self.origin,
                   formula.target_scale, new_value, standard_error,
                   self, [formula])


class ConvertedMeasure(object):
    """
    A converted measure is measure that is the result of a conversion
    """
    def __init__(self, agency, event, origin, scale, value,
                 standard_error=None, original_measure=None, formulas=None):
        # we do not inherit by MagnitudeMeasure because it could be
        # sqlalchemizable, and, consenquently it may have some magic
        # in the constructor that we don't want here
        self.agency = agency
        self.event = event
        self.origin = origin
        self.scale = scale
        self.value = value
        self.standard_error = standard_error
        self.original_measure = original_measure
        self.formulas = formulas or []

    def __repr__(self):
        return "converted measure %s %s (sigma=%s) converted by %s from %s" % (
            self.value, self.scale, self.standard_error, self.formulas,
            self.original_measure)

    def convert(self, new_value, formula, standard_error):
        """
        Convert the measure to a ConvertedMeasure with `new_value`
        and `standard_error` through `formula`.
        """
        return self.__class__(
            self.agency, self.event, self.origin, formula.target_scale,
            new_value, standard_error, self.original_measure,
            self.formulas + [formula])


class Origin(object):
    """
    Describes a point at a given depth and a time.
    For each quantity a measure of the  accuracy is described.

    :attribute id:
      Internal identifier

    :attribute created_at:
      When this object has been imported into the catalogue db

    :attribute source_key:
      the identifier used by the event source for the object

    :attribute time:
      Time in format "YYYY-MM-DD HH:MM:SS.SSS".

    :attribute time_error:
      Time errors expressed in seconds.

    :attribute time_rms:
      Time error expressed as a Root Mean Square in seconds.

    :attribute position:
      Point coordinate (latitude and longitude).
      You can create a point object by using the utility function
      `eqcatalogue.models.CatalogueDatabase.position_from_latlng`

    :attribute semi_major_90error:
      Semi-Major axis of the 90th percentile confidence ellipsis of the
      epicentre.

    :attribute semi_minor_90error:
      Semi-Minor axis of the 90th percentile confidence ellipsis of the
      epicentre.

    :attribute azimuth_error:
      Azimuth with respect to geographical north of the Semi-Major axis.

    :attribute depth:
      depth of the hypocentre in km.

    :attribute depth_error:
      Error in km on the hypocentre depth.

    :attribute eventsource:
      the source object we have imported the origin from. unique
      together with `source_key`
    """
    def __repr__(self):
        return "Origin %s %s" % (self.id, self.source_key)

    def __init__(self, position, time, eventsource, source_key,
                 **kwargs):
        self.time = time
        self.position = position
        self.eventsource = eventsource
        self.source_key = source_key
        for k, v in kwargs.items():
            setattr(self, k, v)


class MeasureMetadata(object):
    """Metadata of a measurement.

    :attribute id:
      Internal identifier

    :attribute created_at:
      When this object has been imported into the catalogue db

    :attribute magnitudemeasure:
      the measure, the metadata is associated with

    :attribute name:
      the name of the metadata. It is unique together with magnitudemeasure

    :attribute value:
      the float value of the metadata.
    """
    def __repr__(self):
        return "%s = %s" % (self.name, self.value)

    def __init__(self, metadata_type, value, magnitudemeasure):
        assert(metadata_type in METADATA_TYPES)
        self.name = metadata_type
        self.value = value
        self.magnitudemeasure = magnitudemeasure


class Singleton(type):
    """Metaclass to implement the singleton pattern"""
    def __init__(mcs, name, bases, der):
        super(Singleton, mcs).__init__(name, bases, der)
        mcs.instance = None

    def __call__(mcs, *args, **kw):
        if mcs.instance is None:
            mcs.instance = super(Singleton, mcs).__call__(*args, **kw)
        return mcs.instance


class CatalogueDatabase(object):
    """
    This is the main class used to access the database. It is a
    singleton object, so you should instantiate it only once in your
    application, before using any other eqcatalogue object that access
    to the database.

    :param engine_class_module:
      A module that implements an engine protocol.
      If not provided, the default is eqcatalogue.datastores.spatialite

    Any other params is passed to the engine constructor.
    For spatialite, you have the following keyword arguments:

    :keyword memory:
      Open an in-memory database
    :type memory: Boolean
    :keyword filename:
      Open a file database located at path `filename`. If not given, the
      default is `eqcatalogue.db`
    :type filename: string
    :keyword drop:
      Drop and recreate the database after opening

    e.g.::
      cat = CatalogueDatabase(filename="my-catalogue.db")
    """

    __metaclass__ = Singleton

    def __init__(self, engine=DEFAULT_ENGINE, **engine_params):
        self._engine_class = self.__class__.get_engine(engine)
        self._engine = self._engine_class(**engine_params)

    def recreate(self):
        """
        Recreate the database. It destroys all the data and recreate
        the schema.
        """
        self._engine.recreate()

    @classmethod
    def reset_singleton(cls):
        """
        Reset the singleton, allowing to switch between different databases
        """
        cls.instance = None

    @classmethod
    def get_engine(cls, module_name):
        """
        Return the Engine class that is defined into `module_name`
        """
        module = __import__(module_name, fromlist=['Engine'])
        return module.Engine

    def position_from_latlng(self, latitude, longitude):
        """
        Utility function to create a POINT object suitable to be stored
        into :class:`eqcatalogue.models.Origin.position`
        """
        return self._engine_class.position_from_latlng(latitude, longitude)

    @property
    def session(self):
        """
        Return the current CatalogueDatabase session
        """
        return self._engine.session

    def get_or_create(self, class_object, query_args, creation_args=None):
        """Handy method to create an object of type `class_object`
        given the query conditions in `query_args`. If an object
        already exists it returns it, otherwise it creates the object
        with params given by `creation_args`"""
        query = self.session.query(class_object)
        queryset = query.filter_by(**query_args)
        if queryset.count():
            return queryset[0], False
        else:
            if not creation_args:
                creation_args = query_args
            else:
                creation_args.update(query_args)
            obj = class_object(**creation_args)
            self.session.add(obj)
            return obj, True
