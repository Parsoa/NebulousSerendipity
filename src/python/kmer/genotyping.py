import io
import os
import re
import pwd
import sys
import copy
import json
import time
import argparse
import traceback

from multiprocessing import Process

from kmer import (
    bed,
    sets,
    config,
    commons,
    counttable,
    map_reduce,
    statistics,
    count_server,
)

# /share/hormozdiarilab/Data/Genomes/Illumina/1KG_Trio/HG00732.fq
# /share/hormozdiarilab/Data/Genomes/Illumina/1KG_Trio/HG00731.fq
# /share/hormozdiarilab/Data/Genomes/Illumina/1KG_Trio/HG00513.fq
# /share/hormozdiarilab/Data/Genomes/Illumina/1KG_Trio/HG00512.fq

# ============================================================================================================================ #
# ============================================================================================================================ #
# MapReduce job to produce a kmer signature for each break point of a deletion
# Step 1: get the break points all of which's kmers are found in CHM1, these are the possible candidates for the structural
# variation's boundaries -> BreakPointJob
# Step 2: Find a set of novel kmers for each break point that can be used to indentify it. khmer never underestimates counts so
# if a kmer comes with a count of zero in reference genome, we can be sure that it is really novel -> NovelKmerJob
# Step 3: khmer may report oversetimated counts for these break points so we need to count them exactly again. This is necessary
# for a reliable likelihood model -> CountKmersExactJob
# Step 4: With exact kmer counts available, we can find the most likely break points for each event in our library -> MostLikelyBreakPointsJob
# Step 5: Given a sample genome, try to genotype the structural variations using the likelihood model and signatures gathered
# above.
# ============================================================================================================================ #
# ============================================================================================================================ #

class GenotypingJob(map_reduce.Job):

    # ============================================================================================================================ #
    # Launcher
    # ============================================================================================================================ #

    @staticmethod
    def launch():
        job = GenotypingJob(job_name = 'Genotyping_', previous_job_name = 'novel_')
        job.execute()

    # ============================================================================================================================ #
    # MapReduce overrides
    # ============================================================================================================================ #

    def transform(self, track, track_name):
        c = config.Configuration()
        likelihood = {}qy
        # TODO: proper value for std?
        distribution = {
            (1, 1): statistics.NormalDistribution(mean = c.coverage, std = 5),
            (1, 0): statistics.NormalDistribution(mean = c.coverage / 2, std = 5),
            (0, 0): statistics.ErrorDistribution(p = 1.0 / 1000),
        }
        likelihood = {
            (1, 1): 0,
            (1, 0): 0,
            (0, 0): 0,
        }
        # all kmers remaining in the track are to be considered part of the signature, no matter the number of breakpoints
        for kmer in track:
            for zyg in likelihood:
                likelihood[zyg] += math.log(distribution[zyg](count_server.get_kmer_count(kmer, self.index, False)))
        return likelihood

# ============================================================================================================================ #
# Main
# ============================================================================================================================ #

if __name__ == '__main__':
    config.init()
    #
    GenotypingJob.launch()