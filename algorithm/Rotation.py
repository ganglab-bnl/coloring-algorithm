import numpy as np
from scipy.spatial.transform import Rotation as R
import copy

from algorithm.Bond import Bond
from algorithm.Voxel import Voxel

class NpRotationDict:
    """
    Class to initialize and manage all (numpy) rotation transformations
    for use in Surroundings.
    """

    def __init__(self):

        # Initialize dictionaries for transformation functions
        self.translation = {
            'translation': lambda x: x # Identity function
        }
        self.single_rotations = {
            '90° X-axis': lambda x: np.rot90(x, 1, (0, 2)),
            '180° X-axis': lambda x: np.rot90(x, 2, (0, 2)),
            '270° X-axis': lambda x: np.rot90(x, 3, (0, 2)),
            '90° Y-axis': lambda x: np.rot90(x, 1, (0, 1)),  
            '180° Y-axis': lambda x: np.rot90(x, 2, (0, 1)),  
            '270° Y-axis': lambda x: np.rot90(x, 3, (0, 1)),  
            '90° Z-axis': lambda x: np.rot90(x, 1, (1, 2)),
            '180° Z-axis': lambda x: np.rot90(x, 2, (1, 2)),
            '270° Z-axis': lambda x: np.rot90(x, 3, (1, 2))
        }
        self.double_rotations = self._init_double_rotations()
        self.all_rotations = {
            **self.translation, 
            **self.single_rotations, 
            **self.double_rotations
        }

    def get_rotation(self, rot_label: str):
        """
        Get the rotation function based on the label (ex: '90° X-axis', '180° Y-axis', etc.)
        """
        return self.all_rotations[rot_label]

    def _init_double_rotations(cls):
        """
        Initialize double_rotations to contain all possible combinations of single_rotations,
        but excluding double rotations on the same axis.
        @return:
            - double_rotations: Dictionary of lambda functions for double rotations
                                {"label1 + label2": lambda x: rotation2(rotation1(x))}
        """
        frozen_double_rotations = [] # List to store frozensets of double rotations (avoids duplicates)

        for label1 in cls.single_rotations.keys():
            for label2 in cls.single_rotations.keys():
                # Create a frozen set of the pair of rotation labels
                rotation_pair = frozenset([label1, label2])

                # Get the last word in string (the axis) from each rotation label
                rotation1_axis = label1.split(' ')[-1] 
                rotation2_axis = label2.split(' ')[-1]

                # Only consider double rotation if they are on different axes and not already considered
                if rotation1_axis != rotation2_axis and rotation_pair not in frozen_double_rotations:
                    frozen_double_rotations.append(rotation_pair)
        
        # Iterate through list of non-repeating double rotations and create a dictionary of lambda functions
        double_rotations = {}
        for rotation_pair in frozen_double_rotations:
            label1, label2 = rotation_pair
            rotation1, rotation2 = cls.single_rotations[label1], cls.single_rotations[label2]

            double_rotations[f'{label1} + {label2}'] = \
                        lambda x, rotation1=rotation1, rotation2=rotation2: rotation2(rotation1(x))
            
        # Sort the dictionary by key
        sorted_double_rotations = {key: double_rotations[key] for key in sorted(double_rotations)}
        return sorted_double_rotations
    
    

class ScipyRotationDict:
    """
    Class for (scipy) rotations for transforming the vertices based on euclidean 
    coordinate space. For use in BondPainter.
    """

    def __init__(self):
        self.translation = {
            'translation': lambda x: x # Identity function
        }
        self.single_rotations = {
            '90° X-axis': lambda x: R.from_euler('x', 90, degrees=True).apply(x),
            '180° X-axis': lambda x: R.from_euler('x', 180, degrees=True).apply(x),
            '270° X-axis': lambda x: R.from_euler('x', 270, degrees=True).apply(x),
            '90° Y-axis': lambda x: R.from_euler('y', 90, degrees=True).apply(x),
            '180° Y-axis': lambda x: R.from_euler('y', 180, degrees=True).apply(x),
            '270° Y-axis': lambda x: R.from_euler('y', 270, degrees=True).apply(x),
            '90° Z-axis': lambda x: R.from_euler('z', 90, degrees=True).apply(x),
            '180° Z-axis': lambda x: R.from_euler('z', 180, degrees=True).apply(x),
            '270° Z-axis': lambda x: R.from_euler('z', 270, degrees=True).apply(x)
        }
        self.double_rotations = self._init_double_rotations()
        self.all_rotations = {
            **self.translation,
            **self.single_rotations,
            **self.double_rotations
        }

    def get_rotation(self, rot_label: str):
        """
        Get the rotation function based on the label (ex: '90° X-axis', '180° Y-axis', etc.)
        """
        return self.all_rotations[rot_label]
    
    def _init_double_rotations(self):
        """
        Initialize double_rotations to contain all possible combinations of single_rotations,
        but excluding double rotations on the same axis.
        @return:
            - double_rotations: Dictionary of lambda functions for double rotations
                                {"label1 + label2": lambda x: rotation2(rotation1(x))}
        """
        frozen_double_rotations = [] # List to store frozensets of double rotations (avoids duplicates)

        for label1 in self.single_rotations.keys():
            for label2 in self.single_rotations.keys():
                # Create a frozen set of the pair of rotation labels
                rotation_pair = frozenset([label1, label2])

                # Get the last word in string (the axis) from each rotation label
                rotation1_axis = label1.split(' ')[-1] 
                rotation2_axis = label2.split(' ')[-1]

                # Only consider double rotation if they are on different axes and not already considered
                if rotation1_axis != rotation2_axis and rotation_pair not in frozen_double_rotations:
                    frozen_double_rotations.append(rotation_pair)
        
        # Iterate through list of non-repeating double rotations and create a dictionary of lambda functions
        double_rotations = {}
        for rotation_pair in frozen_double_rotations:
            label1, label2 = rotation_pair
            rotation1, rotation2 = self.single_rotations[label1], self.single_rotations[label2]

            double_rotations[f'{label1} + {label2}'] = \
                        lambda x, rot1=rotation1, rot2=rotation2: rot1(rot2(x))
            
        # Sort the dictionary by key
        sorted_double_rotations = {key: double_rotations[key] for key in sorted(double_rotations)}
        return sorted_double_rotations
    

class VoxelRotater:
    def __init__(self):
        self.scirot_dict = ScipyRotationDict()
        
    def rotate_voxel(self, voxel: Voxel, rot_label: str) -> Voxel:
        """
        Rotates a single voxel and returns a new Voxel object containing the new 
        rotated bonds. Used to compare bond colors in map_paint operations.
        """
        rot = self.scirot_dict.get_rotation(rot_label)
        new_voxel = copy.deepcopy(voxel)

        new_bonds = {}
        for direction, bond in new_voxel.bonds.items():
            # Rotate the direction vector of the bond
            direction = np.array(direction)
            rotated_direction = tuple(np.round(rot(direction)).astype(int))

            old_bond = new_voxel.get_bond(direction)
            old_bond.direction = rotated_direction
            new_bonds[rotated_direction] = old_bond
        
        new_voxel.bonds = new_bonds
        return new_voxel
        
    def rotate_voxel_bonds(self, voxel: Voxel, rot_label: str) -> dict[tuple[int, int, int], tuple[int, str]]:
        """
        Rotates a single voxel and returns a dictionary containing the rotated 
        directions as keys and the corresponding bond colors as values.
        
        Args:
            voxel (Voxel): The voxel to be rotated.
            rot_label (str): The rotation label to be applied.
            
        Returns:
            bond_dict (dict): A dictionary where keys are the rotated directions 
                              and values are tuples of (bond colors, bond types).
        """
        rot = self.scirot_dict.get_rotation(rot_label)
        
        bond_dict = {}
        for direction, bond in voxel.bonds.items():
            # Rotate the direction vector of the bond
            direction = np.array(direction)
            rotated_direction = tuple(np.round(rot(direction)).astype(int))

            # Store the color in the bond_dict with the rotated direction as the key
            bond_dict[rotated_direction] = (bond.color, bond.type)
        
        return bond_dict

    def find_best_rotation(self, parent_voxel: Voxel, child_voxel: Voxel, rotations_to_check=None):
        """
        Find the best rotation which when applied to the parent_voxel, will
        minimize the difference between its bonds and the bonds of the child_voxel.
        """
        if rotations_to_check is None:
            rotations_to_check = list(self.scirot_dict.all_rotations.keys())
        
        best_rotation = None
        for rot_label in rotations_to_check:
            rot = self.scirot_dict.get_rotation(rot_label)
            # parent_bond_dict = {}
            
            found_valid_rotation = True
            for direction, parent_bond in parent_voxel.bonds.items():
                direction = np.array(direction)
                rotated_direction = tuple(np.round(rot(direction)).astype(int))
                # parent_bond_dict[rotated_direction] = parent_bond.color
                if parent_bond.color == 0 or parent_bond.color is None:
                    continue
            
                # See if child_bond's color in that direction is (1) colored and if so, 
                # (2) matches parent_bond's color
                child_bond = child_voxel.get_bond(rotated_direction)
                if child_bond.color != 0 and child_bond.color is not None:
                    if child_bond.color != parent_bond.color:
                        found_valid_rotation = False
                        break

                # if child_bond.color != 0 and child_bond.color != parent_bond.color:
                #     # print(f"Child voxel{child_voxel.id} has a different color in direction {rotated_direction} after rotation {rot_label}")
                #     found_valid_rotation = False
                #     break

                # Ensure that result of coloring will not result in a palindromic voxel
                elif child_voxel.is_palindromic(parent_bond.color):
                    # print(f"Child voxel{child_voxel.id} is palindromic after rotation {rot_label}")
                    found_valid_rotation = False # child becomes palindromic
                    break
                elif child_bond.bond_partner.voxel.is_palindromic(-parent_bond.color):
                    # print(f"Child voxel{child_voxel.id}'s partner is palindromic after rotation {rot_label}")
                    found_valid_rotation = False # child's partner voxel becomes palindromic
                    break
            
            if found_valid_rotation:
                best_rotation = rot_label
                print(f"Found best rotation between voxel{parent_voxel.id} and voxel{child_voxel.id}: {best_rotation}")
                return best_rotation
            
        return best_rotation
    

    def compare_bond_dicts(parent_bond_dict: dict[tuple[int, int, int], int], 
                           child_bond_dict: dict[tuple[int, int, int], int]) -> bool:
        """
        Compares two bond dictionaries to see if a given rotation is a candidate for a swap_paint. 
        
        Args:
            bond_dict1 (dict): First bond dictionary {3D coordinates tuple: bond color (int)}
            bond_dict2 (dict): Second bond dictionary {3D coordinates tuple: bond color (int)}
        
        Returns:
            bool: True if the non-zero key-value pairs in common keys are equal, False otherwise.
        """
        # Get the common keys between the two dictionaries
        for direction, child_bond_color in child_bond_dict.items():
            
            if child_bond_color == 0: # Only need to check colored child bond equality
                continue

            parent_bond_color = parent_bond_dict[direction]
            if parent_bond_color != child_bond_color:
                return False
        
        # If all colored child_bonds are matched, return True
        return True

            