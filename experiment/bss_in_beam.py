import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
import sys
sys.path.insert(0, '../')
import paths
from nebp_flux import extract_mcnp
from response import response_data
from theoretical_activities import Au_Foil_Theoretical
from process_activities import Au_Foil_Data


class BSS_Data(object):

    """Houses the Bonner Sphere experimental data."""

    def __init__(self):
        """Docstring."""

        # nominal power level kW(th)
        self.P = 1000

        # sizes
        self.sizes = np.array([0, 2, 3, 5, 8, 10, 12])

        # store the experiment that we're comparing with
        self.experiment = self.process_experiment()

        # calculate the theoretical saturation activities
        self.calc_responses()

        return

    def process_experiment(self):
        """Implement after experiment."""
        # LLD channel
        lld = 400

        # initialize array
        counts = np.zeros(len(self.sizes))

        # model
        def model(x, A, B, C, D, E):
            """Docstring."""
            return A * np.exp(-B * x) + C * (1 / np.sqrt(2 * np.pi * D**2)) * np.exp(-(x - E)**2 / (2 * D**2))

        # loop through each size
        for i, size in enumerate(self.sizes):

            # name of the file
            filename = paths.main_path + '/experiment/4_18_19/bss' + str(size) + '.Spe'

            # grab the data
            with open(filename, 'r') as F:
                lines = F.readlines()

            # extract time
            t = int(lines[2065])

            # extract channel data
            ydata = np.array([int(l) for l in lines[12:2059]])

            # trim up to lld
            ydata = ydata[lld:1900]

            #
            xdata = range(len(ydata))

            # fit the curve
            popt, pcov = sp.optimize.curve_fit(model, xdata, ydata, p0=[1, 1, 1, 1, 1000])

            # sum counts beyond lld, convert to rate, and store
            counts[i] = popt[2] / t

            # plot fit
            fig = plt.figure(i + 200)
            ax = fig.add_subplot(111)
            ax.set_xlabel('Channel')
            ax.set_ylabel('Counts')
            ax.plot(xdata, ydata, color='navy', ls='None', marker='.', markersize=0.3, label='Data')
            ax.plot(xdata, model(xdata, *popt), color='seagreen', label='Model')
            ax.legend()
            fig.savefig('plot/bs{}_spectrum.png'.format(i), dpi=300)
            fig.clear()

        return counts

    def calc_responses(self):
        """Docstring."""

        # get the flux data at 100kW
        flux_data = extract_mcnp('n', self.P)

        # sum to only energy dependent (exclude the first cos group)
        flux = np.sum(flux_data[:, 1:, 1:, 0], axis=(0, 1))

        # get response functions
        responses = response_data()

        # this pulls only the rfs for the bonner spheres
        response_functions = []
        for name, response in responses.items():
            if 'bs' in name and 'p' not in name:
                response_functions.append(response.int)
        response_functions = np.array(response_functions)

        # fold the rfs and the flux together, convert to uCi / atom
        self.responses = np.sum(response_functions * flux, axis=1)

        return


if __name__ == '__main__':
    experimental_data = BSS_Data()
