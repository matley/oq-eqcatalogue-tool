# Copyright (c) 2010-2012, GEM Foundation.
#
# eqcataloguetool is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# EqCatalogueTool is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with eqcataloguetool. If not, see <http://www.gnu.org/licenses/>.

"""
Module :mod:`eqcatalogue.grouping` defines
:class:`GroupMeasuresByEventSourceKey`,
:class:`GroupMeasuresByHierarchicalClustering`.
"""

import numpy as np

# FIXME: Remove the unused import of matplotlib.
# To allow the use of this code on an headless machine we import mpl
# and change the rendering backend to Agg before the module
# scipy.cluster, that is needed in this module and imports matplotlib,
# chooses a rendering backend that requires a display. We remark that
# it is not possible to change the mpl rendering backend once it has
# been set.
import matplotlib
matplotlib.use('Agg')

from scipy.cluster import hierarchy


class GroupMeasuresByEventSourceKey(object):
    """
    Group measures by event source key, that is for each source key of
    an event a group of measure is associated.
    """

    @classmethod
    def group(cls, measure_filter):
        """
        Groups the measures that are the result of measure_filter
        """
        groups = {}
        for m in measure_filter.all():
            key = m.event.source_key
            if not key in groups:
                groups[key] = []
            groups[key].append(m)
        return groups

    def group_measures(self, measure_filter):
        """
        Groups the measures that are the result of measure_filter
        """
        return self.__class__.group(measure_filter)


class GroupMeasuresByHierarchicalClustering(object):
    """
    Group measures by time clustering using a hierarchical clustering
    algorithm.

    :param key_fn: the function used to get the measure feature we
        perform the clustering on. If not given, a function that
        extract the time of the measure is provided as default.
    :param args: the args passed to scipy.cluster.hierarchy.fclusterdata.
    """

    def __init__(self, key_fn=None, args=None):
        self._clustering_args = {'t': 200,
            'criterion': 'distance'
            }
        if args:
            self._clustering_args.update(args)
        self._key_fn = key_fn or GroupMeasuresByHierarchicalClustering.get_time

    @classmethod
    def get_time(cls, measure):
        """
        return the origin time of the measure, a float with the unix
        timestamp (plus milliseconds)
        """
        return float(measure.origin.time.strftime('%s'))

    def group_measures(self, measure_filter):
        """
        Groups the measures that are the result of measure_filter
        """
        measures = measure_filter.all()

        data = np.array([self._key_fn(m) for m in measures])
        npdata = np.reshape(np.array(data), [len(data), 1])

        clusters = hierarchy.fclusterdata(npdata, **self._clustering_args)

        grouped = {}
        for i, cluster in enumerate(clusters):
            current = grouped.get(cluster, [])
            current.append(measures[i])
            grouped[cluster] = current
        return grouped
