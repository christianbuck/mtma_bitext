import numpy as np
import matplotlib.pyplot as plt

if __name__ == '__main__':
	dict_scores = open('dict_scores', 'r').readlines()
	dict_line_equalities = []
	dict_jaccard_sims = []

	goslate_scores = open('goslate_scores', 'r').readlines()
	goslate_line_equalities = []
	goslate_jaccard_sims = []

	for line in dict_scores:
		line = line.strip()
		print(line)
		line_equality, jaccard = line.split('\t')
		dict_line_equalities.append(line_equality)
		dict_jaccard_sims.append(jaccard)

	for line in goslate_scores:
		line = line.strip()
		line_equality, jaccard = line.split('\t')
		goslate_line_equalities.append(line_equality)
		goslate_jaccard_sims.append(jaccard)

	x1 = range(len(dict_scores))
	x2 = range(len(goslate_scores))
	fig = plt.figure(figsize=(20, 8))
	ax1 = fig.add_subplot(111)
	ax1.set_xlabel('lexical translations')
	ax1.set_ylabel('google translations')

	ax1.scatter(dict_line_equalities, goslate_line_equalities, marker='.', color = (0,0,0.5,1), label='line equality ratio')
	ax1.scatter(dict_jaccard_sims, goslate_jaccard_sims, marker='x', color = (0,0,1,1), label='jaccard similarity')
	# ax1.scatter(x2, goslate_line_equalities, marker='.', color = (0.5,0,0,1), label='google translation: line equality ratio')
	# ax1.scatter(x2,  marker='x', color = (1,0,0,1), label='google translation: jaccard similarity')

	plt.legend(loc='upper left')
	plt.show()