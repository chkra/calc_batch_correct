#!/usr/bin/env python
# coding: utf-8
'''
 Combat batch correction app for FASTGenomics
'''
import json
import pathlib
import random
import csv
import jinja2
import logging
import enum

import pandas as pd
import numpy as np

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.cm as cm


from sklearn import decomposition
from scipy.spatial.distance import pdist

from collections import defaultdict
from fastgenomics import io as fg_io
from hello_genomics import logging_config

import combat as cb

# initialize logging
logging_config.configure_logging(level=logging.INFO)
logger = logging.getLogger('hello_genomics_calc')

# set paths to jinja2-templates for summary.md etc.
TEMPLATE_PATH = pathlib.Path(__file__).parent.parent / 'templates'




class Columns(str, enum.Enum):
    # @todo: this is horrible on so many levels ...
    CELLS = 'cellId*Ganzzahl'
    GENES = 'entrezId*Ganzzahl'
    EXPR = 'expressionValue*Zahl'
    # BATCH = '_generated_batch*Text'
    BATCH = 'batch'


def get_data():
    logger.info('Loading genes and cell annotation matrice')
    # @todo: tidy up
    # genes_path = fg_io.get_input_path('genes_data_input')
    expre_path = fg_io.get_input_path('expression_input')
    cells_meta = fg_io.get_input_path('cells_meta_input')

    # combat requires full matrix input - unstack input file
    # combat expects matrix of shape [genes x cells], so index columns accordingly
    # @todo: check if this truly makes sense
    # @todo: the Columns.enum-Trick sucks, this should be some global definition
    # @todo: will blow up for large data files - 
    X = pd.read_csv(expre_path , sep='\t')
    print(X.head(10))
    data = X.set_index([Columns.GENES, Columns.CELLS])\
           .unstack() \
           .fillna(0)
           # @todo this sucks as well - won't hurt to select this column, but
           # @todo I'd rather have a global data scheme
           # .loc[:, Columns.EXPR]

    pheno = pd.read_csv(cells_meta, sep='\t')
    return data, pheno


def get_test_data():
    # @todo: how to test?
    
    logger.info('Loading genes and cell annotation matrice')
    genes_path = fg_io.get_input_path('test_genes_data_input')
    cells_meta = fg_io.get_input_path('test_cells_meta_input')

    #genes_path = './bladder-expr.txt'
    #cells_meta = './bladder-pheno.txt'
    
    data = pd.read_csv(genes_path, sep='\t')
    pheno = pd.read_csv(cells_meta, sep='\t')

    return data, pheno


def check_batch_distribution(X, batch_anno, axis, title=''):
    
    pca = decomposition.PCA(n_components=2)
    pca.fit(X)
    X_trans = pca.transform(X)

    all_batch_reps = []

    labels = set(batch_anno)
    colors = cm.spectral(np.linspace(0, 1, len(labels)))

    for val, col in zip(labels, colors):
        Z = X_trans[np.ix_((batch_anno == val))]
        rep = np.mean(Z, axis=0)
        all_batch_reps.append(rep)

        axis.scatter(Z[:, 0], Z[:, 1], label=val, marker='o', c=col, edgecolor='none')
        axis.add_artist(plt.Circle(rep, 5, color=col))

    axis.set_title(title)
    axis.legend(numpoints=1)

    all_batch_reps = np.array(all_batch_reps)
    return np.sum(pdist(all_batch_reps))


def make_output(data, corr, pheno, parameters):
    
    f, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 4))

    total_batch_dist = check_batch_distribution(data.values.T,
                                                pheno[Columns.BATCH],
                                                ax1,
                                                'Before Batch Correction')

    total_batch_dist_corr = check_batch_distribution(corr.values.T,
                                                     pheno[Columns.BATCH],
                                                     ax2,
                                                     'After Batch Correction')

    logger.info('Batch center distance before correction: ' + str(total_batch_dist))
    logger.info('Batch center distance after correction: ' + str(total_batch_dist_corr))
    corr_ratio = total_batch_dist / total_batch_dist_corr

    if corr_ratio >= 1:
        logger.info('Batch completed without errors. Reduced batch center distance by ratio of '
                    + str(np.round(corr_ratio, 2)))
    else:
        logger.error('Batch correction modified data in invald way!')
        logger.error('Batch center ratio is less than 1:' + str(np.round(corr_ratio, 2)))

    doc_img_path = fg_io.get_output_path('batch_corr_img')
    logger.info('Plotting PCA embedding of data for documentation.')
    # plt.savefig(doc_img_path, bbox_inches='tight')
    
    logger.info("Storing matrix of batch-corrected gene expressions.")
    output_path = fg_io.get_output_path('batch_corr_matrix')
    corr.to_csv(output_path)

    results = {'num_batches': len(set(pheno[Columns.BATCH])),
               'ctr_dist_before': total_batch_dist, 
               'ctr_dist_before': total_batch_dist_corr,
               'ctr_ratio': corr_ratio}
    
    logger.debug("Loading Jinja2 summary template")
    with open(TEMPLATE_PATH / 'summary.md.j2') as temp:
        template_str = temp.read()

    logger.debug("Rendering template")
    template = jinja2.Template(template_str)
    summary = template.render(results=results, parameters=parameters)

    logger.info("Writing summary")
    summary_path = fg_io.get_summary_path()
    with summary_path.open('w') as f_sum:
        f_sum.write(summary)

    


def main():
    '''
    main routine of batch correction with combat
    '''

    try:

        logger.info('Loading parameters')
        parameters = fg_io.get_parameters()

        random.seed(4711)
        parameters['random_seed'] = 4711

        # data, pheno = get_data()
        #data, pheno = get_test_data()

        logger.info('Received data matrix of shape (genes x cells) = ' + str(data.shape))
        logger.info('Found the following batches: ' + str(set(pheno[Columns.BATCH])))
        logger.info('Calling combat for batch correction.')

        corr = cb.combat(data, pheno[Columns.BATCH])

        make_output(data, corr, pheno, parameters)

        logger.info('Done.')

    except Exception as inst:
        logger.error(type(inst))
        logger.error(inst)
        raise inst

if __name__ == '__main__':
    main()
