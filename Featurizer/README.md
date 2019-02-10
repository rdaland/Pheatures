# Featurizer

This repository containst the code used in Mayer & Daland (in progress). This code is made publicly available for use and extension in future research.

The basic functionality of this code is to take a set of input phonological classes and produce a feature system for that set. See the paper for a full description.

---

## code

This folder contains the code used in the paper.

Python requirements (earlier versions may work but have not been tested):

* Python 3 (3.6.5)
* `numpy` package (1.13.3) (optional)

**Featurizer.py**: Takes a file containing a set of phonological classes as input, and produces a featurization of that set. Can be called from the command line, or imported and used in a Python script.

* Input: A file which contains a set of phonological classes. Classes should be separated by a new line, and each member of the class must be separated by a space. The first line in the file must be the full alphabet. See the files in `sample_inputs` for examples.
* Ouput: In addition to printing output to the command line, running this script produces three output files:
    * A `.csv` file containing the segments and their generated features. This is stored by default in `csv_output`.
    * A `.gv` file containing a graph of the final intersectional closure of the input class system once the featurization has been done. By default this is stored in `poset_output`. See below for how to convert these to image files.
    * A `.gv` file containing a feature graph of the final intersectional closure of the input class system after featurization. This is similar to the class diagram above, but also includes the feature/value pairs associated with each class. By default this is saved in the `feats_output` folder. See below for how to convert these to image files.

Command line arguments:

* Required positional argument: The path to the input class file.
* `--output_file`: The path where the output `.csv` file will be saved. Optional, default `../csv_output/features.csv`.
* `--featurization`: The type of featurization to use. Must be one of `privative`, `complementary`, `inferential_complementary`, or `full`. Optional, default `complementary`.
* `--use_numpy`: If this flag is provided, the `numpy` package will be used for matrix operations. This requires `numpy` to be installed. Otherwise, a bespoke, less efficient matrix implementation will be used.
* `--poset_file`: The path where the output class system graph will be saved. Optional, default `../poset_output/poset_graph.gv`.
* `--feats_file`: The path where the output feature graph will be saved. Optional, default `../feats_output/feats_graph.gv`.
* `--verbose`: If this flag is provided, additional information will be printed to the console as the algorithm is run.

**Poset.py**: Implements a partially ordered set. Maintains the basic partial ordering of the class system (parent/child), and calculates the intersectional closure, among other things. No command line interface.

**Array.py**: A bespoke implementation that duplicates the subset of the functionality of `numpy` arrays that is necessary for this program. Included to improve code portability, but things will run *much* faster if you install `numpy` and use the `--use_numpy` flag described above.

## sample_inputs

A folder containing some example class input files, including all examples discussed in the paper.

## csv_output

A folder for saving output `.csv`s containing segment feature mappings.

## poset_output

A folder for saving output poset graphs.

## feats_output 

A folder for saving feature output graphs.

---

## Generating images from Graphviz (`.gv`) files

The class structure and feature diagrams are saved from this program as Graphviz `.gv` files. These files are useful because they can be easily modified to customize the graphs (all diagrams in the paper were made by this process). To convert the files to an image format like a `.png`, you can use the `dot` program, which you may have to install. See the [dot manual](https://www.graphviz.org/doc/info/command.html) for details.

For example, you can convert a `.gv` file to a `.png` by running:

```dot -Tpng -O my_graphviz_file.gv```

---


