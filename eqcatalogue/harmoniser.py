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
This module provides the main class that handles the harmonisation
of a set of measures to a single target scale
"""

import math
from scipy.misc import derivative


class FormulaPathFinder(object):
    """
    A path finder algorithm that compute the proper sequence of
    formulas to be applied on a measure to convert to a target scale
    """

    def __init__(self, formulas):
        self._formulas = formulas

    def all_formulas(self):
        """
        Return a list of all the registered formulas
        """
        return sum(self._formulas.values(), [])

    def applicable_formulas(self, measure):
        """
        Return the list of formulas that can be applied to `measure`.
        A formula can be applied to a measure if such measure belongs
        to its domain
        """
        return [f for f in self.all_formulas()
                if f.is_applicable_for(measure)]

    def find_formulas_for(self, measure, target_scale):
        """
        Find formulas to convert `measure` to `target_scale`

        If the `measure` is already in the target scale it returns None.

        If it exists a single formula to convert `measure`, it will
        return a list with a single element (built in O(N) time).

        If more formulas are needed to convert `measure` to
        `target_scale` a O(N^3) algorithm is used to get a list of
        formulas that should be sequentially applied to `measure` to
        get the converted measure.
        """

        # if we do not have any formula to convert to the target
        # scale, just return
        if target_scale not in self._formulas:
            return

        # if we have a formula that can convert directly the measure
        # to the target scale, we return it
        for formula in self._formulas[target_scale]:
            if formula.is_applicable_for(measure):
                return [formula]

        # otherwise we will do a graph visiting where the formula are
        # the nodes and two formulas `foo` and `bar` are connected if
        # the codomain of `foo` is a subset of the domain of `bar`.

        candidate_starting_formulas = self.applicable_formulas(measure)
        ret = []

        for starting_formula in candidate_starting_formulas:
            to_visit = [[starting_formula, 0, measure]]
            previous_depth = -1
            current_path = []

            while to_visit:
                formula, depth, original_measure = to_visit.pop()
                next_measure = formula.apply(original_measure)
                next_formulas = self.applicable_formulas(next_measure)

                if depth > previous_depth:
                    current_path.append(formula)
                else:
                    current_path.pop()

                if next_measure.scale == target_scale:
                    ret.append(current_path[:])

                for formula in next_formulas:
                    to_visit.append([formula, depth + 1, next_measure])

        # if we have multiple solutions just return the first one
        if len(ret):
            return ret[0]

        return ret


class Harmoniser(object):
    """
    This class is responsible to convert a set of measures into a
    target scale by using a set of conversion formula

    :attribute target_scale
      The target scale considered

    :attribute _formulas
      The list of formulas used to convert measures
    """
    def __init__(self, target_scale):
        self.target_scale = target_scale
        self._formulas = {}

    def add_conversion_formula(self, formula, module_error,
                               domain, target_scale):
        """
        Create a conversion formula from a `function` and make
        it available for the harmoniser.

        E.g.
        an_harmoniser.add_conversion_formula(
              lambda measure: measure * 1.2 + 0.1,
              0.2, domain=C(scale="mb") & C(agency__in=["ISC"]),
              target_scale="Mw")

        :param formula:
          A callable that requires in input the value to be converted

        :param module_error:
          The error associated with the formula.

        :param domain:
          The domain of measures mapped by conversion formula (an
          object, e.g. a list/set that can be queried with the in
          operator)

        :param target_scale:
          The target scale
        """

        formula = ConversionFormula(formula, module_error,
            domain, target_scale)
        self._add_formula(formula)

    def add_conversion_formula_from_model(self, model):
        """
        Create a conversion formula from a regression model and make
        it available for the harmoniser

        :param model
          A regression model
        """
        formula = ConversionFormula.make_from_model(model)
        self._add_formula(formula)

    def _add_formula(self, formula):
        """
        Add a conversion formula to the formula database
        """
        scale = formula.target_scale
        self._formulas[scale] = self._formulas.get(scale, [])
        self._formulas[scale].append(formula)

    def harmonise(self, measures, path_finder_cls=FormulaPathFinder,
                    measure_uncertainty=0.0, allow_trivial_conversion=True):
        """
        Harmonise an iterator of measures.

        :param measures:
          the measures to be converted
        :param path_finder_cls:
          the class used to find the sequence of formulas
          to apply to get a conversion.
        :param measure_uncertainty:
          default grade of uncertainty, error related to the measures
          if no standard error for measures is no defined.
        :returns: the converted and the unconverted measures
        :rtype: a 2-tuple. The former is dictionary where the keys are
        the converted measures and the value is a dictionary storing
        the converted value and the formula used for the conversion.
        The latter is a list of the unconverted measures
        """
        converted = {}
        unconverted = []
        path_finder = path_finder_cls(self._formulas)

        for m in measures:
            formulas = path_finder.find_formulas_for(m, self.target_scale)
            if formulas:
                value = formulas[0].apply(m, measure_uncertainty)
                for formula in formulas[1:]:
                    value = formula.apply(value, measure_uncertainty)
                converted[m] = dict(
                    measure=value,
                    formulas=formulas)
            elif m.scale == self.target_scale and allow_trivial_conversion:
                converted[m] = dict(
                    measure=m,
                    formulas=[])
            else:
                unconverted.append(m)

        return converted, unconverted


class ConversionFormula(object):
    """
    An object holding a formula that can convert a measure into a
    target magnitude scale

    :attribute formula:
      A callable that accepts one argument that holds the measure value
      to be converted.

    :attribute module_error:
      The error associated with the formula.

    :attribute domain:
      A list of measures that stores exhaustively the domain of the
      formula

    :attribute target_scale
      The target scale
    """
    def __init__(self, formula, module_error, domain, target_scale):
        self.formula = formula
        self.module_error = module_error
        self.domain = domain
        self.target_scale = target_scale

    def is_applicable_for(self, measure):
        """Returns true if the measure given in input can be converted"""
        return measure in self.domain

    def __repr__(self):
        domain_len = len(self.domain)
        domain_str = "%d measures" % domain_len
        if domain_len:
            domain_str += "(%s" % self.domain[0]
            if domain_len > 1:
                domain_str += " ..."
            domain_str += ")"
        else:
            domain_str = str(self.domain)
        return "Formula to %s (domain: %s)" % (
            self.target_scale, domain_str)

    @classmethod
    def make_from_model(cls, model):
        """
        Build a conversion model by a regression model
        """
        return cls(formula=model.func,
                    module_error=model.residual(),
                    domain=model.native_measures,
                    target_scale=model.target_scale)

    def apply(self, measure, measure_uncertainty=0.0):
        """
        Apply the conversion to `measure`. Raise an error if the
        `measure` does not belong to the domain of the conversion
        formula. If the measure doesn't provide a standard error
        the measure_uncertainty value is used instead.
        """
        if not self.is_applicable_for(measure):
            raise ValueError(
                "You can not apply the conversion to this measure")
        measure_error = (measure.standard_error
                         if measure.standard_error is not None
                         else measure_uncertainty)

        new_value = self.formula(measure.value)
        standard_error = math.sqrt(self.module_error ** 2
            + ((derivative(self.formula, measure.value)) ** 2)
            * (measure_error ** 2))

        return measure.convert(new_value, self, standard_error)
