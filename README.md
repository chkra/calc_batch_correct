# FASTGenomics App: Batch correction based on ComBat

## Introduction

ComBat is an R package for removing batch effects from sequencing data. The most prominent implementation can be found in the [R package SVA](https://www.rdocumentation.org/packages/sva/versions/3.20.0/topics/ComBat). This FASTGenomics app uses the faster python implementation of the SVA code provided by Brent Pedersen on [his GitHub page](https://github.com/brentp/combat.py).

## Parameters and assumptions

In the current state, the app takes no parameters. No additional covariate data is used.

The combat function is called on the input data set specified in 
`config/input_file_mapping.json`, assumes a single batch column as specified in `enum Columns.BATCHES` in `main.py`.

## Output

The app stores the transformed matrix in an output file as specified in `manifest.json`. It also provides a very simple statistic for the effect of batch correction, the average distance between all batch cluster centers, included in the summary output. For an array `all_batch_reps` holding the mean vectors of each batch, this statistic is computed as `np.sum(pdist(all_batch_reps))`.

Finally, for code debugging and visual inspection of the correction results, a simple PCA embedding before and after correction is plotted.

## Remark

In the currect state, this app requires pandas version 0.19.2, as stated in `requirements.txt`. Batch correction will crash for higher versions of pandas.



## References

> Pedersen, Brent: GitHub page for python / numpy / pandas / patsy version of ComBat for removing batch effects. [https://github.com/brentp/combat.py](https://github.com/brentp/combat.py) Accessed Oct. 2017.

> Bioconductor site for the original SVA package. [http://bioconductor.org/packages/release/bioc/html/sva.html](http://bioconductor.org/packages/release/bioc/html/sva.html). Accessed Oct. 2017.

> Johnson WE, Rabinovic A, Li C (2007). Adjusting batch effects in microarray
expression data using Empirical Bayes methods. Biostatistics 8:118-127.  

> Jeffrey T. Leek, W. Evan Johnson, Hilary S. Parker, Andrew E. Jaffe
and John D. Storey (). sva: Surrogate Variable Analysis. R package
version 3.4.0.
