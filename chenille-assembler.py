"""
	Sachandhan Ganesh
	Created On 10.18.2017

	Simple de novo genome assembler to test naive de Bruijn graph manipulation and the implications of
	read lengths, coverage, and kmer sizes.
"""

import argparse
import copy
from random import randint
from Bio import Seq, SeqIO, SeqRecord
from difflib import SequenceMatcher
from graphviz import Digraph


class ArachneAssembler(object):
	def __init__(self, reads, read_len, k):
		self._k = k
		self._kmers = sorted(self.get_kmers(k, reads, read_len))
		self._graph = {}
		self._graph_raw = {}
		self._graph_rev = {}
		self._graph_rev_raw = {}


	@staticmethod
	def get_reads(seq, read_len, num_reads, k):
		reads = []

		for _ in range(num_reads):
			read = ArachneAssembler.fragment_read(seq, read_len)
			if len(read) > k:
				reads.append(read)

		return reads

	@staticmethod
	def fragment_read(seq, frag_len):
		ind = randint(-frag_len / 2, len(seq) - 1)
		if (ind < 0):
			frag_len = frag_len + ind
			ind = 0

		if ind + frag_len >= len(seq):
			return seq[ind:]
		else:
			return seq[ind : ind + frag_len]


	@staticmethod
	def get_coverage(seq_len, reads, num_reads):
		avg_read_len = 0
		for read in reads:
			avg_read_len += len(read)
		avg_read_len /= len(reads)

		return num_reads * (avg_read_len / seq_len)


	def get_kmers(self, k, reads, read_len):
		kmer_set = set()

		for read in reads:
			if k > read_len:
				print("k for kmer is greater than read length")
				exit(1)
			elif k <= len(read):
				for i in range(len(read) - k + 1):
					kmer_set.add(read[i : i + k])

		return kmer_set


	def find_next_kmers(self, kmer):
		followers = []

		for other in self._kmers:
			if kmer != other and kmer[1:] == other[:-1]:
				followers.append(other)

		return followers


	def build_debruijn(self):
		graph = {}
		reverse_graph = {}

		for kmer in self._kmers:
			followers = self.find_next_kmers(kmer)
			graph[kmer] = set(followers)

			for follower in followers:
				if follower in reverse_graph:
					reverse_graph[follower].add(kmer)
				else:
					reverse_graph[follower] = set([kmer])

		for key in graph:
			if key not in reverse_graph:
				reverse_graph[key] = set()

		self._graph = graph
		self._graph_rev = reverse_graph


	def get_graph(self):
		return self._graph


	def get_raw_graph(self):
		return self._graph_raw


	def get_predecessor_graph(self):
		return self._graph_rev


	def get_predecessor_raw_graph(self):
		return self._graph_rev_raw


	def get_graph_ends(self):
		heads = []
		tails = []

		for key in self._graph:
			if len(self._graph_rev[key]) == 0:
				heads.append(key)

		for key in self._graph_rev:
			if len(self._graph[key]) == 0:
				tails.append(key)

		return heads, tails


	def sieve_graph(self, graph):
		sieved_graph = {}

		for key in graph:
			if key in set.union(*graph.values()) or len(graph[key]) != 0:
				sieved_graph[key] = graph[key]

		return sieved_graph, graph


	def simplify_debruijn(self):
		graph, _ = self.sieve_graph(self._graph)
		reverse_graph, _ = self.sieve_graph(self._graph_rev)

		kmers = list(graph.keys())
		k = len(kmers[0])
		change = 1

		while change:
			graph_size = len(graph.keys())

			for kmer in kmers:
				word = kmer

				while word is not None and word in graph:
					if len(graph[word]) == 1 and len(reverse_graph[list(graph[word])[0]]) == 1:
						follower = list(graph[word])[0]

						s = SequenceMatcher(None, follower, word)
						alpha, beta, overlap_len = s.find_longest_match(0, len(follower), 0, len(word))
						new_word = word[: beta + overlap_len] + follower[alpha + overlap_len:]

						# set new word in graph with appropriate chain
						graph[new_word] = graph[follower]

						# set new word in reverse_graph with appropriate chain
						reverse_graph[new_word] = reverse_graph[word]

						# get predecessors of word from reverse_graph
						word_predecessors = list(reverse_graph[word])
						follower_antecessors = list(graph[follower])

						# for each predecessor in graph, link new word in with existing chain
						for predecessor in word_predecessors:
							graph[predecessor].remove(word)
							graph[predecessor].add(new_word)

						# for each antecessor in reverse_graph, link new word in with existing chain
						for antecessor in follower_antecessors:
							reverse_graph[antecessor].remove(follower)
							reverse_graph[antecessor].add(new_word)

						# empty original graph nodes
						graph.pop(word, 0)
						graph.pop(follower, 0)

						# empty original reverse_graph nodes
						reverse_graph.pop(word, 0)
						reverse_graph.pop(follower, 0)

						word = new_word
					else:
						word = None

			change = graph_size - len(graph.keys())

		self._graph_raw = self._graph
		self._graph_rev_raw = self._graph_rev

		self._graph = graph
		self._graph_rev = reverse_graph


	def visualize_graph(self):
		dot = Digraph(comment="de Bruijn graph for assembly")

		graphs = [self._graph_raw, self._graph]
		labels = ["plain_de-debruijn", "assembled_contigs"]

		for enum, pair in enumerate(zip(labels, graphs)):
			label = pair[0]
			graph = pair[1]
			name = "cluster_" + label

			with dot.subgraph(name=name) as c:
				c.attr(label=label)
				c.attr("node", shape="box")

				for kmer in graph:
					node_label = kmer
					for i in range(enum):
						node_label += "_"
					c.node(node_label, node_label)

					for follower in graph[kmer]:
						follower_label = follower
						for i in range(enum):
							follower_label += "_"
						c.edge(node_label, follower_label)

		dot.attr(rankdir="LR")
		dot.render("assembly.gv", view=True)


def parse_arguments():
	parser = argparse.ArgumentParser(description="Arachne: Naive de novo genome assembler")
	parser.add_argument("-f", "--file", metavar=("filepath", "format"), nargs=2, type=str, help="DNA sequence source file as 'txt', 'fastq', or 'fasta'")
	parser.add_argument("read_len", metavar="L", type=int, help="length of reads")
	parser.add_argument("num_reads", metavar="N", type=int, help="number of reads")
	parser.add_argument("k", metavar="k", type=int, default=4, help="kmer length")
	parser.add_argument("-d", "--display", action="store_true", help="display pictoral results")

	args = parser.parse_args()
	return args


def main():
	args = parse_arguments()

	if args.file and args.file[1] == "txt":
		with open(args.file[0]) as seq_file:
			sample = seq_file.read().replace('\n', '').replace(' ', '')
	else:
		sample = "ATGGAAGTCGCGGAATC"

	reads = ArachneAssembler.get_reads(sample, args.read_len, args.num_reads, args.k)

	coverage = ArachneAssembler.get_coverage(len(sample), reads, args.num_reads)

	assembly = ArachneAssembler(reads, args.read_len, args.k)
	assembly.build_debruijn()
	assembly.simplify_debruijn()

	# debruijn, rev_debruijn = build_debruijn(kmers)
	# simp_debruijn, simp_rev_debruijn = simplify_debruijn(copy.deepcopy(debruijn), copy.deepcopy(rev_debruijn))

	print("Sequence:", sample)
	print("\nCoverage:", coverage)
	print("\nOriginal Kmers:")
	for key in assembly.get_raw_graph().keys():
		print("\t%s" % key)
	print("\nAssembled Contigs:")
	for key in assembly.get_graph().keys():
		print("\t%s" % key)

	if args.display:
		assembly.visualize_graph()

if __name__ == "__main__":
	main()