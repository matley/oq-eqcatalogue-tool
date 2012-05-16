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

import unittest
import numpy as np
from numpy.ma.testutils import assert_almost_equal
from eqcatalogue import regression
from eqcatalogue import managers


class ShouldPerformRegression(unittest.TestCase):

    def test_linear_regression(self):
        # Assess
        A = 0.85
        B = 1.03
        native_measures = managers.MeasureManager('mb')
        target_measures = managers.MeasureManager('Mw')
        native_measures.measures = np.random.uniform(3., 8.5, 1000)
        native_measures.sigma = np.random.uniform(0.02, 0.2, 1000)
        target_measures.measures = A + B * native_measures.measures
        target_measures.sigma = np.random.uniform(0.025, 0.2, 1000)
        emsr = regression.EmpiricalMagnitudeScalingRelationship(
            native_measures,
            target_measures)

        # Act
        output = emsr.apply_regression_model(regression.LinearModel)

        # Assert
        assert_almost_equal(np.array([A, B]), output.beta)
        self.assertTrue(output.res_var < 1e-20)

    def test_polynomial_regression(self):
        # Assess
        A = 0.046
        B = 0.556
        C = 0.673
        native_measures = managers.MeasureManager('mb')
        target_measures = managers.MeasureManager('Mw')
        native_measures.measures = np.random.uniform(3., 8.5, 1000)
        native_measures.sigma = np.random.uniform(0.02, 0.2, 1000)
        target_measures.measures = C + B * native_measures.measures +\
          A * (native_measures.measures ** 2.)
        target_measures.sigma = np.random.uniform(0.025, 0.2, 1000)
        emsr = regression.EmpiricalMagnitudeScalingRelationship(
            native_measures,
            target_measures)

        # Act
        output = emsr.apply_regression_model(regression.PolynomialModel,
                                             order=2)

        # Assert
        assert_almost_equal(np.array([C, B, A]), output.beta)
        self.assertTrue(output.res_var < 1e-20)