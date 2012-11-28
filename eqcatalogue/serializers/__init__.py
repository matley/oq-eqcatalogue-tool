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
This module defines a map to exporter functions
"""


from eqcatalogue.serializers import csv


MEASURES_EXPORTERS = {
    'csv': csv.export_measures
}


def get_measure_exporter(fmt):
    """
    Returns the measure exporter associated with the format `fmt`
    """
    return MEASURES_EXPORTERS[fmt]
