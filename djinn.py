import argparse
from random import randint


def get_reads(seq, read_len, num_reads):
	reads = []

	for _ in range(num_reads):
		reads.append(fragment_read(seq, read_len))

	return reads


def fragment_read(seq, frag_len):
	ind = randint(0, len(seq) - 1)

	if ind + frag_len >= len(seq):
		return seq[ind:]
	else:
		return seq[ind : ind + frag_len]


def get_coverage(seq_len, reads, num_reads):
	avg_read_len = 0
	for read in reads:
		avg_read_len += len(read)
	avg_read_len /= len(reads)

	return num_reads * (avg_read_len / seq_len)


def get_kmers(k, reads, read_len):
	kmer_set = set()

	for read in reads:
		if k > read_len:
			print("k for kmer is greater than read length")
			exit(1)
		elif k <= len(read):
			for i in range(len(read) - k + 1):
				kmer_set.add(read[i : i + k])

	return kmer_set


def prepare_arguments():
	parser = argparse.ArgumentParser(description="Djinn: Naive de novo genome assembler")
	parser.add_argument("read_len", metavar="L", type=int, help="length of reads")
	parser.add_argument("num_reads", metavar="N", type=int, help="number of reads")
	parser.add_argument("k", metavar="k", type=int, default=4, help="kmer length")

	args = parser.parse_args()
	return args.read_len, args.num_reads, args.k


def main():
	read_len, num_reads, k = prepare_arguments()

	sample = "ATGGAAGTCGCGGAATC"

	reads = get_reads(sample, read_len, num_reads)

	coverage = get_coverage(len(sample), reads, num_reads)

	kmers = sorted(get_kmers(k, reads, read_len))

	print(sample)
	print("Coverage:", coverage)
	for el in kmers:
		print(el)


if __name__ == "__main__":
	main()
