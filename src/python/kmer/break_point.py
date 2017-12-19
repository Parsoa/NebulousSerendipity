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

from kmer.sv import StructuralVariation, Inversion, Deletion

import khmer
import colorama
import pybedtools

import plotly.offline as plotly
import plotly.graph_objs as graph_objs

# ============================================================================================================================ #
# ============================================================================================================================ #
# ============================================================================================================================ #

class BreakPoint(object):

    @staticmethod
    def to_json(break_point):
        return {
            'boundary': break_point.boundary,
            'kmers': break_point.kmers,
            'reference_kmers': break_point.reference_kmers
        }

    def __init__(self, boundary, begin, end, kmers, reference_kmers):
        self.name = '(' + str(begin) + ',' + str(end) + ')'
        self.boundary = boundary
        self.begin = begin
        self.end = end
        self.kmers = kmers
        self.reference_kmers = reference_kmers
        self.score = 0
        self.zygosity = None

# ============================================================================================================================ #
# ============================================================================================================================ #
# MapReduce job for finding StructuralVariation breakpoints
# Algorithm: starts with a set of structural variation events and their approximate breakpoints and tries to refine them
# considers a radius of [-50, 50] around each end of the breakpoint, and for each pair of endpoints within that radius considers
# the area as the structural variations and applies it to the reference genome to generate a set of kmers. Discards those endpoints
# whose kmers do not all appear in the base genome the event was detected in. 
# Output: Reports the remaining boundary candidates with their list of associated kmers and the count of those kmers in the
# base genome.
# ============================================================================================================================ #
# ============================================================================================================================ #

class BreakPointJob(map_reduce.Job):

    # ============================================================================================================================ #
    # Launcher
    # ============================================================================================================================ #

    @staticmethod
    def launch():
        job = BreakPointJob(job_name = 'break_point_', previous_job_name = '')
        job.execute()

    # ============================================================================================================================ #
    # MapReduce overrides
    # ============================================================================================================================ #

    def find_thread_count(self):
        pass

    def load_inputs(self):
        c = config.Configuration()
        bedtools = pybedtools.BedTool(c.bed_file)
        self.radius = 50
        # split variations into batches
        n = 0
        for track in bedtools:
            name = re.sub(r'\s+', '_', str(track).strip()).strip()
            # too large, skip
            if track.end - track.start > 1000000:
                print(colorama.Fore.RED + 'skipping ', name, ', too large')
                continue
            index = n % c.max_threads 
            if not index in self.batch:
                self.batch[index] = []
            self.batch[index].append(track)
            print(colorama.Fore.BLUE + 'assigned ', name, ' to ', index)
            n = n + 1
        self.num_threads = len(self.batch)
        print('running on ', self.num_threads, ' threads')

    def run_batch(self, batch):
        c = config.Configuration()
        sv_type = self.get_sv_type()
        output = {}
        for track in batch:
            name = re.sub(r'\s+', '_', str(track).strip()).strip()
            sv = sv_type(track = track, radius = self.radius)
            output[name] = self.transform(sv)
        self.output_batch(output)
        print(colorama.Fore.GREEN, 'process ', self.index, ' done')

    def transform(self, sv):
        c = config.Configuration()
        frontier = self.extract_boundary_kmers(sv)
        # whatever that is left in the frontier is a possible break point
        frontier = self.prune_boundary_candidates(frontier, sv)
        # now check the reference counts to find the best match
        results = {}
        results['candidates'] = len(frontier)
        for break_point in frontier :
            for kmer in break_point.reference_kmers:
                # counts for reference not available at this
                break_point.reference_kmers[kmer] = -1
            for kmer in break_point.kmers:
                break_point.kmers[kmer] = count_server.get_kmer_count(kmer, self.index, False)
            results[break_point.name] = BreakPoint.to_json(break_point)
            # save the number of boundary candidates
        return results

    # ============================================================================================================================ #
    # job-specific helpers
    # ============================================================================================================================ #

    def get_sv_type(self):
        c = config.Configuration()
        bed_file_name = c.bed_file.split('/')[-1]
        sv_type = bed_file_name.split('.')[-2]
        if sv_type == 'DEL':
            return Deletion
        if sv_type == 'INV':
            return Inversion
        return StructuralVariation

    def extract_boundary_kmers(self, sv):
        c = config.Configuration()
        frontier = {}
        for begin in range(-self.radius, self.radius + 1) :
            for end in range(-self.radius, self.radius + 1) :
                kmers, boundary = sv.get_signature_kmers(begin, end)
                if not kmers:
                    # skip this candidate
                    continue
                reference_kmers = sv.get_reference_signature_kmers(begin, end)
                #
                break_point = BreakPoint(boundary = boundary, begin = begin, end = end,\
                    kmers = kmers, reference_kmers = reference_kmers)
                frontier[break_point] = True
        return frontier

    # prunes a break points if not all its kmers appear in the counttable
    def prune_boundary_candidates(self, frontier, sv):
        c = config.Configuration()
        remove = {}
        for break_point in frontier:
            for kmer in break_point.kmers:
                count = count_server.get_kmer_count(kmer, self.index, False)
                if count == 0:
                    remove[break_point] = True
                    break
        for break_point in remove:
            frontier.pop(break_point, None)
        return frontier

# ============================================================================================================================ #
# ============================================================================================================================ #
# ============================================================================================================================ #

class MostLikelyBreakPointsJob(map_reduce.Job):

    # ============================================================================================================================ #
    # Launcher
    # ============================================================================================================================ #

    @staticmethod
    def launch():
        job = MostLikelyBreakPointsJob(job_name = 'MostLikelyBreakPoints_', previous_job_name = 'exact_')
        job.execute()

    # ============================================================================================================================ #
    # MapReduce overrides
    # ============================================================================================================================ #

    def check_cli_arguments(self, args):
        # requires only --coverage option to specify the read depth
        pass

    # this is upperbounded by --threads cli argument
    def find_thread_count(self):
        with open(os.path.join(self.get_previous_job_directory(), 'merge.json'), 'r') as json_file:
            tracks = json.load(json_file)
            self.tracks = tracks
            self.num_threads = len(tracks)
            print('num thread: ', self.num_threads)

    # As the CountKmersExactJob job doesn't work quite exactly as MapReduce expects, we need to fiddle with the input data
    # here to make it adhere to that format
    def load_inputs(self):
        index = 0
        for track in self.tracks:
            self.batch[index] = {
                track: self.tracks[track]
            }
            index += 1

    def transform(self, track, track_name):
        c = config.Configuration()
        likelihood = {}
        # TODO: proper value for std?
        distribution = {
            '(1, 1)': statistics.NormalDistribution(mean = c.coverage, std = 5),
            '(1, 0)': statistics.NormalDistribution(mean = c.coverage / 2, std = 5),
        }
        zygosity = ['(1, 1)', '(1, 0)']
        break_points = []
        for kmer in track['novel_kmers']:
            for break_point in track['novel_kmers'][kmer]['break_points']:
                if not break_point in likelihood:
                    likelihood[break_point] = {
                        '(1, 1)': 0,
                        '(1, 0)': 0,
                    }
                    break_points.append(break_point)
                for zyg in zygosity:
                    overflow = False
                    try:
                        r = distribution[zyg].log_pmf(track['novel_kmers'][kmer]['actual_count'])
                    except Exception as e:
                        overflow = True
                    if not overflow:
                        likelihood[break_point][zyg] += r
        # TODO: each term should be multiplied by P(zyg | bp) , how to calculate
        # output = map(lambda x: likelihood[x][(1, 1)] + likelihood[x](1, 0), break_points)
        return likelihood

    def plot(self, tracks):
        self.radius = 50
        for track in tracks:
            x = []
            for begin in range(-self.radius, self.radius + 1) :
                x.append([])
                for end in range(-self.radius, self.radius + 1) :
                    break_point = '(' + str(begin) + ',' + str(end) + ')'
                    if break_point in tracks[track]:
                        x[begin + self.radius].append(tracks[track][break_point]['(1, 1)'] + tracks[track][break_point]['(1, 0)'])
                    else:
                        # TODO: fix this
                        x[begin + self.radius].append(-1000)
            path = os.path.join(self.get_current_job_directory(), track + '.html')
            trace = graph_objs.Heatmap(z = x)
            data = [trace]
            plotly.plot(data, filename = path, auto_open = False)

# ============================================================================================================================ #
# Main
# ============================================================================================================================ #

if __name__ == '__main__':
    config.init()
    #
    MostLikelyBreakPointsJob.launch()
