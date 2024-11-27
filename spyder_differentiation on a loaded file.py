# -*- coding: utf-8 -*-
"""
Created on Fri Oct 25 10:43:25 2024

@author: Admin
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import pandas as pd
from datetime import datetime
import os

class DataDifferentiator:
    def __init__(self):
        """Initialize the DataDifferentiator class"""
        self.original_data = None
        self.diff_data = None
        self.X = None
        self.Y = None
        self.metadata = {}
        
    def load_experimental_data(self, filepath):
        """
        Load experimental data from the specified text file
        
        Parameters:
        filepath (str): Full path to the data file
        """
        try:
            # Extract metadata from filename
            filename = os.path.basename(filepath)
            self.metadata['filename'] = filename
            
            # Read the data file
            # Assuming the file is space or tab-separated
            # Modify the delimiter and header handling based on your file format
            data = pd.read_csv(filepath, delimiter='\s+', header=None)
            print(f"Data shape: {data.shape}")
            
            # Store original data
            self.original_data = data.values
            
            # Create coordinate grids
            rows, cols = self.original_data.shape
            x = np.linspace(0, cols-1, cols)
            y = np.linspace(0, rows-1, rows)
            self.X, self.Y = np.meshgrid(x, y)
            
            print(f"Successfully loaded data from {filename}")
            print(f"Data dimensions: {rows} x {cols}")
            return True
            
        except Exception as e:
            print(f"Error loading file: {e}")
            return False
    
    def differentiate_data(self):
        """
        Calculate the gradient (differentiation) of the data
        Returns:
        tuple: (dx, dy) containing derivatives in x and y directions
        """
        if self.original_data is None:
            raise ValueError("No data loaded. Please load data first.")
            
        # Calculate derivatives using numpy gradient
        dy, dx = np.gradient(self.original_data)
        # Calculate magnitude of gradient
        self.diff_data = np.sqrt(dx**2 + dy**2)
        return dx, dy
    
    def plot_3d(self, title_suffix=''):
        """
        Create 3D surface plots for both original and differentiated data
        
        Parameters:
        title_suffix (str): Additional text to add to plot titles
        """
        if self.original_data is None or self.diff_data is None:
            raise ValueError("No data available. Please load and differentiate data first.")
            
        # Create figure with two subplots
        fig = plt.figure(figsize=(15, 6))
        
        # Original data plot
        ax1 = fig.add_subplot(121, projection='3d')
        surf1 = ax1.plot_surface(self.X, self.Y, self.original_data, 
                               cmap='viridis', edgecolor='none')
        ax1.set_title(f'Original Data {title_suffix}')
        ax1.set_xlabel('X Index')
        ax1.set_ylabel('Y Index')
        ax1.set_zlabel('Value')
        fig.colorbar(surf1, ax=ax1, shrink=0.5, aspect=5)
        
        # Differentiated data plot
        ax2 = fig.add_subplot(122, projection='3d')
        surf2 = ax2.plot_surface(self.X, self.Y, self.diff_data, 
                               cmap='viridis', edgecolor='none')
        ax2.set_title(f'Differentiated Data {title_suffix}')
        ax2.set_xlabel('X Index')
        ax2.set_ylabel('Y Index')
        ax2.set_zlabel('Gradient Magnitude')
        fig.colorbar(surf2, ax=ax2, shrink=0.5, aspect=5)
        
        plt.tight_layout()
        return fig
    
    def plot_density(self, title_suffix=''):
        """
        Create surface density plots for both original and differentiated data
        
        Parameters:
        title_suffix (str): Additional text to add to plot titles
        """
        if self.original_data is None or self.diff_data is None:
            raise ValueError("No data available. Please load and differentiate data first.")
            
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Original data density plot
        im1 = ax1.imshow(self.original_data, cmap='viridis', aspect='auto',
                        extent=[self.X.min(), self.X.max(), self.Y.min(), self.Y.max()])
        ax1.set_title(f'Original Data Density {title_suffix}')
        ax1.set_xlabel('X Index')
        ax1.set_ylabel('Y Index')
        fig.colorbar(im1, ax=ax1)
        
        # Differentiated data density plot
        im2 = ax2.imshow(self.diff_data, cmap='viridis', aspect='auto',
                        extent=[self.X.min(), self.X.max(), self.Y.min(), self.Y.max()])
        ax2.set_title(f'Differentiated Data Density {title_suffix}')
        ax2.set_xlabel('X Index')
        ax2.set_ylabel('Y Index')
        fig.colorbar(im2, ax=ax2)
        
        plt.tight_layout()
        return fig
    
    def save_data(self, output_folder='.'):
        """
        Save both original and differentiated data to CSV files
        
        Parameters:
        output_folder (str): Folder path to save the files
        """
        if self.original_data is None or self.diff_data is None:
            raise ValueError("No data available. Please load and differentiate data first.")
            
        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Base filename from original data if available
        base_filename = self.metadata.get('filename', 'data').split('.')[0]
        
        # Save original data
        original_filepath = os.path.join(output_folder, f"{base_filename}_original_{timestamp}.csv")
        np.savetxt(original_filepath, self.original_data, delimiter=',')
        
        # Save differentiated data
        diff_filepath = os.path.join(output_folder, f"{base_filename}_differentiated_{timestamp}.csv")
        np.savetxt(diff_filepath, self.diff_data, delimiter=',')
        
        print(f"Data saved in {output_folder}:")
        print(f"Original data: {os.path.basename(original_filepath)}")
        print(f"Differentiated data: {os.path.basename(diff_filepath)}")

# Example usage
if __name__ == "__main__":
    # Create instance
    differentiator = DataDifferentiator()
    
    # File path
    file_path = r"C:/Users/Admin/testAI/data_knn_Im0x4-0Vnm0x4-0Vx_0TR_0x1Vs_202411051545.txt"
    
    # Load the experimental data
    if differentiator.load_experimental_data(file_path):
        # Perform differentiation
        dx, dy = differentiator.differentiate_data()
        
        # Create and save plots
        title_suffix = '(77K)'  # You can modify this based on your data
        
        fig_3d = differentiator.plot_3d(title_suffix)
        fig_3d.savefig('3d_plots.png', dpi=300, bbox_inches='tight')
        
        fig_density = differentiator.plot_density(title_suffix)
        fig_density.savefig('density_plots.png', dpi=300, bbox_inches='tight')
        
        # Save data to CSV files
        output_folder = 'processed_data'  # You can modify this path
        differentiator.save_data(output_folder)
        
        # Show plots
        plt.show()
    else:
        print("Failed to load data file.")