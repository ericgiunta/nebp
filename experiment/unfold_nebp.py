import numpy as np
import sys
sys.path.insert(0, '../')
import paths
from nebp_flux import extract_mcnp
from response import response_data
from process_activities import Au_Foil_Data
from bss_in_beam import BSS_Data
from origami import unfold


class Unfold_NEBP(object):

    """An object that handles all of the unfolding for the NEBP flux."""

    def __init__(self, data_source, P, method, params):
        """Initialization will store inputs and then run the unfolding."""

        # check inputs
        message = "data_souce must be 'ft_au', 'bs', or 'all'."
        assert data_source in ('ft_au', 'bs', 'all'), message

        # set inputs
        self.data_source = data_source
        self.P = P
        self.method = method
        self.params = params

        # get default spectrum
        self.ds = self.prepare_default_spectrum()

        # prep response matrix
        self.R, self.eb = self.prepare_response_matrix()

        # get responses
        self.N = self.prepare_responses()
        print(self.N)

        # unfold
        self.solution = self.unfold()

        return

    def prepare_default_spectrum(self):
        """Docstring."""

        # get the flux data at 100kW
        flux_data = extract_mcnp('n', self.P)

        # sum to only energy dependent (exclude the first cos group)
        flux = np.sum(flux_data[:, 1:, :, 0], axis=(0, 1))[1:]

        return flux

    def prepare_response_matrix(self):
        """This function prepares the response function given the data that is
        selected to be used in the unfolding."""

        # determine what data will be used
        rf_names = []

        # first, do the gold
        if self.data_source in ('ft_au', 'all'):
            for i in range(9):
                rf_names.append('ft_au{}'.format(i))

        # then the bonner spheres
        if self.data_source in ('bs', 'all'):
            for i in (0, 2, 3, 5, 8, 10, 12):
                rf_names.append('bs{}-1'.format(i))

        # get response functions
        responses = response_data()

        # print the keys
        print(responses.keys())
        print(rf_names)

        # this pulls only the rfs for the bonner spheres
        response_functions = []
        for name in rf_names:

            # pull out the response
            response = responses[name]

            # then append the response
            response_functions.append(response.int)

            # grab a set of bin edges (they should all match)
            eb = response.edges

        # convert to numpy array
        response_functions = np.array(response_functions)

        return response_functions, eb

    def prepare_responses(self):
        """This function grabs all the measured responses from both experiments
        and returns whatever data is asked for by the data_source.
        This also scales the responses to match the nominal power level."""

        # initialize a structure for the data
        responses = np.zeros(16)

        # first, do the gold
        experimental_data = Au_Foil_Data()

        # set the first part to the gold responses
        responses[:len(experimental_data.a_sat_atom)] = experimental_data.a_sat_atom * (self.P / 1E5)

        # then do the bss
        experimental_data = BSS_Data()

        # set the second part to the bss responses
        responses[-len(experimental_data.experiment):] = experimental_data.experiment * (self.P / 1E3)

        # then decide what portion to return
        if self.data_source == 'ft_au':
            responses = responses[:9]
        elif self.data_source == 'bs':
            responses = responses[9:]
        else:
            pass

        return responses

    def unfold(self):
        """This unfolds the spectrum"""

        # unfold the spectrum
        print(self.N.shape)
        print(self.R.shape)
        print(self.ds.shape)
        sol = unfold(self.N, self.N * 0.05, self.R, self.ds, method=self.method, params=self.params)

        return sol


def unfold_myriad():
    """A function that names many different unfoldings for this experiments."""

    # first, let's do all of this at the same power level
    P = 1E5

    # initialize a structure to hold these solutions and the energy bins
    solutions = {}

    # unfold with all data
    unfolder = Unfold_NEBP('all', P, 'Gravel', {'tol': 0, 'max_iter': 100})
    solutions['eb'] = unfolder.eb
    solutions['ds'] = unfolder.ds
    solutions['all'] = unfolder.solution

    # finally, return all of the solutions
    return solutions


if __name__ == '__main__':
    unfold_myriad()
