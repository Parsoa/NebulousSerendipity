from __future__ import print_function

import copy
import time

from kmer import (
    config
)

from kmer.kmers import *
from kmer.commons import *
from kmer.chromosomes import *
print = pretty_print

# ============================================================================================================================ #
# ============================================================================================================================ #
# ============================================================================================================================ #

class StructuralVariation(object):

    def __init__(self, track):
        self.chrom = track.chrom
        self.begin = track.begin
        self.end = track.end
        self.inner_kmers = None
        self.extract_base_sequence()

    # the begin position itself is not included in the sequence
    # the end position is included in the sequence
    def extract_base_sequence(self):
        c = config.Configuration()
        # this is the largest sequence that we will ever need for this track
        # <- Slack -><-actual sequence-><- Slack ->
        self.slack = c.read_length - c.ksize
        begin = self.begin - self.slack
        end = self.end + self.slack
        chromosome = extract_chromosome(self.chrom.lower())
        self.sequence = chromosome[begin: end]
        if begin > len(chromosome) or end > len(chromosome) or len(self.sequence) == 0:
            print(self.chrom)
            print(len(chromosome))
            print(self.slack)
            print(self.begin)
            print(self.end)
            debug_breakpoint()

    def extract_inner_kmers(self, counter, count, n, overlap = True, canonical = True):
        c = config.Configuration()
        begin = self.slack
        end = len(self.sequence) - self.slack
        inner_seq = self.sequence[begin : end + 1 - c.ksize]
        #print(inner_seq)
        #print(len(inner_seq))
        inner_kmers = c_extract_kmers(c.ksize, counter, count, overlap, canonical, inner_seq)
        if len(inner_kmers) <= n:
            return inner_kmers
        else:
            items = sorted(inner_kmers.items(), key = lambda item: item[1])[0:n]
            return {item[0]: item[1] for item in items}

    def extract_boundary_gapped_kmers(self, counter = lambda x: 1, count = 1):
        c = config.Configuration()
        begin = self.slack
        end = len(self.sequence) - self.slack
        outer_gapped_kmers = {}
        inner_gapped_kmers = {}
        h = c.hsize
        # each half is 16 bases plus 10 bases in between, say nearly 45: 25 bases remain for each end
        b = self.sequence[begin - h - 2 - 25: begin + 3 + h + 25]
        kmer = self.sequence[begin - h - 2: begin + 3 + h]
        prefix = self.sequence[begin - h - 2 - 25: begin - h - 2]
        suffix = self.sequence[begin + 3 + h: begin + 3 + h + 25]
        inner_gapped_kmers[kmer] = {'indicators': self.generate_kmer_mask(prefix, suffix), 'prefix': prefix, 'suffix': suffix}
        #
        e = self.sequence[end - h - 2 - 25: end + 3 + h + 25]
        kmer = self.sequence[end - h - 2: end + 3 + h]
        prefix = self.sequence[end - h - 2 - 25: end - h - 2]
        suffix = self.sequence[end + 3 + h: end + 3 + h + 25]
        inner_gapped_kmers[kmer] = {'indicators': self.generate_kmer_mask(prefix, suffix), 'prefix': prefix, 'suffix': suffix}
        #
        kmer = self.sequence[begin - 2 - h: begin + 3] + self.sequence[end - 2: end + 3 + h]
        prefix = self.sequence[begin - h - 2 - 25: begin - h - 2]
        suffix = self.sequence[end + 3 + h: end + 3 + h + 25]
        outer_gapped_kmers[kmer] = {'indicators': self.generate_kmer_mask(prefix, suffix), 'prefix': prefix, 'suffix': suffix}
        return {'inner': inner_gapped_kmers, 'outer': outer_gapped_kmers, 'begin': b, 'end': e, 'sequence': self.sequence}

    def generate_kmer_mask(self, left, right):
        c = config.Configuration()
        masks = {}
        for seq in [left, right]:
            for j in range(0, 5):
                indices = []
                while len(indices) != 21:
                    i = random.randint(0, len(seq) - 1)
                    if not i in indices:
                        indices.append(i)
                indices = sorted(indices)
                indices.insert(0, '')
                mask = reduce(lambda x, y: x + seq[y], indices)
                masks[mask] = True
        return masks

# ============================================================================================================================ #
# ============================================================================================================================ #
# ============================================================================================================================ #

class Inversion(StructuralVariation):

    pass

# ============================================================================================================================ #
# ============================================================================================================================ #
# ============================================================================================================================ #

class Deletion(StructuralVariation):

    pass
