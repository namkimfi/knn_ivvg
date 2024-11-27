# -*- coding: utf-8 -*-
"""
Created on Wed Oct 23 11:03:04 2024

@author: Admin
"""

import numpy as np

import matplotlib.pyplot as plt

from mpl_toolkits.mplot3d import Axes3D



def plot_3d_data(filename, elev=30, azim=35):

    """

    Generate a 3D plot from data file with adjustable viewing angles.

    

    Parameters:

    filename (str): Path to the data file. Expected format: x y z (space-separated)

    elev (float): Elevation viewing angle in degrees (default: 30)

    azim (float): Azimuth viewing angle in degrees (default: 45)

    """

    try:

        # Load data from file

        #data = np.loadtxt('C:\Users\Admin\testAI\accum_kim')
        #data = np.loadtxt(r'C:\Users\Admin\testAI\accum_kim')
        #data = np.loadtxt('C:/Users/Admin/testAI/accum_kim.txt') #knn
        data = np.loadtxt('C:/Users/Admin/testAI/data_knn_ivnvx_m0x4-0Vn_m0x4-0Vx_0TR_0x1Vs_200x200_202411070847.txt') #iv

        x = data[:, 0]

        y = data[:, 1]

        z = data[:, 2]

        

        # Create the 3D plot

        fig = plt.figure(figsize=(10, 8))

        ax = fig.add_subplot(111, projection='3d')

        

        # Create scatter plot

        #scatter = ax.scatter(y, x, z, c=z, cmap='viridis')  #knn;x, y exchanged
        scatter = ax.scatter(x, y, z, c=z, cmap='viridis')  # iv meas

        

        # Add a color bar

        plt.colorbar(scatter)

        

        # Set labels

        ax.set_xlabel('X')

        ax.set_ylabel('Y')

        ax.set_zlabel('Z')

        

        # Set viewing angle

        ax.view_init(elev=elev, azim=azim)

        

        # Add title

        plt.title(f'3D Plot (elevation: {elev}°, azimuth: {azim}°)')

        

        # Show the plot

        plt.show()

        

    except Exception as e:

        print(f"Error: {str(e)}")

        

# Example usage:

if __name__ == "__main__":

    # Example with different viewing angles

    data_file = "data.txt"

    

    # Default view

    plot_3d_data(data_file)

    plot_3d_data(data_file, elev=20, azim=60)

    # Top view

    plot_3d_data(data_file, elev=90, azim=0)

    

    # Side view

    plot_3d_data(data_file, elev=0, azim=0)